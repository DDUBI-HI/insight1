#!/usr/bin/env node
// AI 사무실 로컬 브리지 — n8n(Docker)·업무 패널·3D 화면과 Windows 의 Claude Code 를 잇는다.
//
// 안전 규칙
//  1) 정해진 작업(jobs/index.mjs 허용 목록)만 실행한다. 명령을 그대로 실행하는 통로는 없다.
//  2) /api/health·/api/config·/api/office(보기 전용)를 뺀 모든 API 는 토큰(X-Office-Token)이 필요하다.
//  3) Host 헤더를 확인한다(127.0.0.1·localhost·host.docker.internal 만) — 다른 웹사이트가 읽어 가지 못하게(DNS 리바인딩 방어).
//  4) 토큰은 이 PC 의 브라우저(127.0.0.1)에서만 받아 갈 수 있다(/api/session).
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { APP, IS_WIN, ROOT, VERSION, ensureDirs, loadConfig, loadN8nSecret, loadToken } from './config.mjs';
import { Store } from './store.mjs';
import { Runner } from './runner.mjs';
import { registry } from './jobs/index.mjs';
import { cardnewsState, slideSvgState, TEAMS, WORKERS } from './jobs/common.mjs';
import { officeSnapshot } from './office.mjs';
import { claudeVersion } from './claude.mjs';
import { ID_RE, InputError, isInside } from './util.mjs';

const WEB = path.join(ROOT, 'web');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json; charset=utf-8', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8' };
const CSP = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

function listWeb() {
  const out = new Map();
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p);
      else if (MIME[path.extname(e.name).toLowerCase()]) out.set('/' + path.relative(WEB, p).split(path.sep).join('/'), p);
    }
  };
  walk(WEB);
  return out;
}

export function createApp(cfgIn) {
  const cfg = cfgIn || loadConfig();
  const paths = ensureDirs(cfg);
  const token = loadToken(cfg);
  loadN8nSecret(cfg); // 처음 실행 때 n8n 알림 비밀값 파일을 만들어 둔다
  const store = new Store(paths);
  const runner = new Runner({ cfg, paths, store, registry });
  const files = listWeb();
  const started = Date.now();
  const info = { lastDocker: null, claude: null, n8n: { at: 0, ok: null } };
  const allowedHosts = new Set([`127.0.0.1:${cfg.port}`, `localhost:${cfg.port}`, `host.docker.internal:${cfg.port}`, ...(cfg.extraHosts || []).map((h) => `${h}:${cfg.port}`)].map((h) => h.toLowerCase()));

  const send = (res, code, body, headers = {}) => {
    const isJson = typeof body !== 'string' && !Buffer.isBuffer(body);
    res.writeHead(code, {
      'content-type': isJson ? 'application/json; charset=utf-8' : headers['content-type'] || 'text/plain; charset=utf-8',
      'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer', ...headers,
    });
    res.end(isJson ? JSON.stringify(body) : body);
  };
  const tokenOk = (req) => {
    const got = String(req.headers['x-office-token'] || (req.headers.authorization || '').replace(/^Bearer\s+/i, ''));
    const a = Buffer.from(got); const b = Buffer.from(token);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  };
  const isLoopback = (req) => ['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(req.socket.remoteAddress);
  const readBody = (req) => new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => { size += c.length; if (size > 1024 * 1024) { reject(new InputError('요청이 너무 큽니다')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => {
      if (!chunks.length) return resolve({});
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { reject(new InputError('JSON 형식이 아닙니다')); }
    });
    req.on('error', reject);
  });

  async function n8nReachable() {
    if (Date.now() - info.n8n.at < 30000) return info.n8n.ok;
    info.n8n.at = Date.now();
    try {
      const r = await fetch(new URL('/healthz', cfg.n8n.baseUrl), { signal: AbortSignal.timeout(2500) });
      info.n8n.ok = r.ok;
    } catch { info.n8n.ok = false; }
    return info.n8n.ok;
  }

  function publicJob(j, full = false) {
    const o = { id: j.id, type: j.type, team: j.team, teamLabel: TEAMS[j.team], worker: j.worker, workerName: WORKERS[j.worker]?.name, title: j.title, status: j.status, source: j.source, heavy: j.heavy, createdAt: j.createdAt, startedAt: j.startedAt, finishedAt: j.finishedAt, summary: j.summary, error: j.error, outputs: j.outputs, parentId: j.parentId };
    if (full) { o.params = j.params; o.log = j.log.slice(-120); o.result = j.result; }
    return o;
  }

  function openPath(p) {
    const allowed = [paths.root, cfg.agents?.slideSvg, cfg.agents?.cardnews].filter(Boolean);
    if (!p || !allowed.some((r) => isInside(r, p)) || !fs.existsSync(p)) throw new InputError('열 수 없는 경로입니다');
    if (!IS_WIN) return { opened: false, path: p };
    const isFile = fs.statSync(p).isFile();
    spawn('explorer.exe', isFile ? [`/select,${p}`] : [p], { detached: true, stdio: 'ignore', windowsHide: false }).unref();
    return { opened: true, path: p };
  }

  async function api(req, res, url) {
    const m = (re) => url.pathname.match(re);
    const method = req.method;

    if (url.pathname === '/api/health') return send(res, 200, { ok: true, app: APP, version: VERSION, demo: !!cfg.demo });
    if (url.pathname === '/api/config') return send(res, 200, { lang: cfg.lang || 'ko' });
    if (url.pathname === '/api/office') return send(res, 200, officeSnapshot({ store, runner, cfg }));
    if (url.pathname === '/api/session') {
      const host = String(req.headers.host || '').toLowerCase();
      const origin = req.headers.origin;
      const localHost = host === `127.0.0.1:${cfg.port}` || host === `localhost:${cfg.port}`;
      const originOk = !origin || origin === `http://${host}`;
      if (!isLoopback(req) || !localHost || !originOk) return send(res, 403, { error: '이 PC 의 브라우저에서만 열 수 있습니다' });
      return send(res, 200, { token });
    }

    if (!tokenOk(req)) return send(res, 401, { error: '토큰이 없거나 틀렸습니다' });

    if (url.pathname === '/api/status' && method === 'GET') {
      if (!info.claude?.ok) info.claude = claudeVersion(cfg); // 못 찾았으면 매번 다시 찾는다
      const cur = runner.current ? store.jobs.get(runner.current.jobId) : null;
      return send(res, 200, {
        app: APP, version: VERSION, demo: !!cfg.demo, dataDir: paths.root, configFile: cfg.configFile, uptimeSec: Math.round((Date.now() - started) / 1000),
        claude: info.claude,
        agents: { slideSvg: slideSvgState(cfg), cardnews: cardnewsState(cfg) },
        n8n: { baseUrl: cfg.n8n.baseUrl, reachable: await n8nReachable(), lastRequestFromDocker: info.lastDocker },
        webhooks: { events: !!cfg.n8n.webhooks?.events, instagramPublish: !!cfg.n8n.webhooks?.instagramPublish },
        instagram: { enabled: !!cfg.instagram?.enabled && !!cfg.n8n.webhooks?.instagramPublish },
        queue: { running: cur ? publicJob(cur) : null, queued: runner.queued().length },
        inputRoots: cfg.inputRoots,
        schedule: (cfg.schedule || []).filter((s) => s && s.enabled !== false).map((s) => ({ type: s.type, days: s.days, time: s.time })),
        teams: TEAMS, workers: WORKERS,
      });
    }
    if (url.pathname === '/api/job-types' && method === 'GET') return send(res, 200, registry.publicList());
    if (url.pathname === '/api/jobs' && method === 'GET') return send(res, 200, store.listJobs(Number(url.searchParams.get('limit')) || 60).map((j) => publicJob(j)));
    if (url.pathname === '/api/jobs' && method === 'POST') {
      const b = await readBody(req);
      const viaDocker = String(req.headers.host || '').toLowerCase().startsWith('host.docker.internal');
      const job = runner.enqueue(String(b.type || ''), b.params || {}, { source: viaDocker ? 'n8n' : (b.source === 'n8n' ? 'n8n' : 'panel') });
      return send(res, 201, publicJob(job));
    }
    let mm = m(/^\/api\/jobs\/([^/]+)$/);
    if (mm && method === 'GET') {
      if (!ID_RE.test(mm[1]) || !store.jobs.has(mm[1])) return send(res, 404, { error: '작업이 없습니다' });
      return send(res, 200, publicJob(store.jobs.get(mm[1]), true));
    }
    mm = m(/^\/api\/jobs\/([^/]+)\/cancel$/);
    if (mm && method === 'POST') {
      if (!ID_RE.test(mm[1]) || !store.jobs.has(mm[1])) return send(res, 404, { error: '작업이 없습니다' });
      return send(res, 200, publicJob(runner.cancel(mm[1])));
    }
    if (url.pathname === '/api/approvals' && method === 'GET') {
      const all = url.searchParams.get('all') === '1';
      const list = all ? [...store.approvals.values()].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1)).slice(0, 100) : store.pendingApprovals();
      return send(res, 200, list);
    }
    mm = m(/^\/api\/approvals\/([^/]+)$/);
    if (mm && method === 'POST') {
      if (!ID_RE.test(mm[1])) return send(res, 404, { error: '승인 항목이 없습니다' });
      const b = await readBody(req);
      const note = String(b.note || '').slice(0, 2000);
      return send(res, 200, await runner.decideApproval(mm[1], String(b.decision || ''), note));
    }
    if (url.pathname === '/api/open' && method === 'POST') {
      const b = await readBody(req);
      let target = null;
      if (ID_RE.test(String(b.jobId || ''))) target = store.jobs.get(b.jobId)?.outputs?.[Number(b.index) || 0];
      else if (ID_RE.test(String(b.approvalId || ''))) target = store.approvals.get(b.approvalId)?.files?.[Number(b.index) || 0];
      else if (b.folder && Object.prototype.hasOwnProperty.call(paths, b.folder)) target = paths[b.folder];
      return send(res, 200, openPath(target));
    }
    return send(res, 404, { error: '없는 주소입니다' });
  }

  const server = http.createServer(async (req, res) => {
    const host = String(req.headers.host || '').toLowerCase();
    if (!allowedHosts.has(host)) return send(res, 421, { error: 'Host 헤더가 허용되지 않습니다' });
    if (host.startsWith('host.docker.internal')) info.lastDocker = new Date().toISOString();
    let url;
    try { url = new URL(req.url, `http://${host}`); } catch { return send(res, 400, { error: '주소 오류' }); }
    try {
      if (url.pathname.startsWith('/api/')) return await api(req, res, url);
      if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, { error: '허용되지 않는 방법' });
      const key = url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname);
      const file = files.get(key);
      if (!file) return send(res, 404, '없는 파일입니다');
      const headers = { 'content-type': MIME[path.extname(file).toLowerCase()], 'cache-control': 'no-cache', 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer' };
      if (file.endsWith('.html')) headers['content-security-policy'] = CSP;
      res.writeHead(200, headers);
      return res.end(req.method === 'HEAD' ? undefined : fs.readFileSync(file));
    } catch (e) {
      const code = e instanceof InputError ? 400 : 500;
      if (code === 500) console.error(`[ai-office] ${req.method} ${url?.pathname}:`, e);
      return send(res, code, { error: String(e.message || e) });
    }
  });

  return { cfg, paths, store, runner, server, token: () => token };
}

async function main() {
  const demo = process.argv.includes('--demo');
  const cfg = loadConfig(demo ? { override: { demo: true } } : {});
  if (process.argv.includes('--port')) cfg.port = Number(process.argv[process.argv.indexOf('--port') + 1]);
  const app = createApp(cfg);
  app.runner.startScheduler();
  const pidFile = path.join(app.paths.run, 'bridge.pid');
  app.server.on('error', (e) => {
    console.error(e.code === 'EADDRINUSE' ? `[ai-office] ${cfg.port} 포트를 이미 쓰고 있습니다. 이미 켜져 있는지 확인하세요.` : e);
    process.exit(1);
  });
  app.server.listen(cfg.port, cfg.bindHost, () => {
    fs.writeFileSync(pidFile, JSON.stringify({ pid: process.pid, port: cfg.port, startedAt: new Date().toISOString() }));
    console.log(`[ai-office] ${cfg.demo ? '데모 모드 ' : ''}http://127.0.0.1:${cfg.port}/ 에서 실행 중 (데이터: ${app.paths.root})`);
    setImmediate(() => app.runner.kick());
  });
  const stop = () => { try { fs.rmSync(pidFile, { force: true }); } catch { /* 무시 */ } process.exit(0); };
  process.on('SIGINT', stop); process.on('SIGTERM', stop);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
