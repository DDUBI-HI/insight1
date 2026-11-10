// Claude Code 명령형 실행(claude -p)과 Python 헬퍼 실행.
// - 프롬프트는 표준입력으로 넘긴다(명령줄에 사용자 글을 넣지 않는다 → 셸 해석·따옴표 문제 없음).
// - 허용 도구는 작업마다 만든 설정 파일(--settings)로만 준다. 목록에 없는 도구는 -p 모드에서 자동 거부된다.
// - stream-json 출력을 한 줄씩 읽어 3D 화면에 "지금 하는 일"을 보낸다.
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { IS_WIN } from './config.mjs';
import { UUID_RE, writeJsonAtomic } from './util.mjs';

const MOCK = path.join(path.dirname(fileURLToPath(import.meta.url)), 'mock-claude.mjs');
const SAFE_ARG = /^[\p{L}\p{N} _:\\/.\-()]+$/u;

const base = (p) => String(p || '').split(/[\\/]/).pop();
const short = (s, n) => { const t = String(s ?? '').replace(/\s+/g, ' ').trim(); return t.length > n ? t.slice(0, n - 1) + '…' : t; };

/** 도구 사용 한 건 → 3D 화면 활동(Act, claude-3d-frog-office CONTRACT 4절과 같은 모양) */
export function toolAct(name, input = {}) {
  switch (name) {
    case 'Read': return { k: 'read', a: base(input.file_path) };
    case 'Edit': case 'MultiEdit': case 'NotebookEdit': return { k: 'edit', a: base(input.file_path || input.notebook_path) };
    case 'Write': return { k: 'write', a: base(input.file_path) };
    case 'Bash': return { k: 'bash', a: short(input.description || input.command, 44) };
    case 'Grep': return { k: 'grep', a: short(input.pattern, 24) };
    case 'Glob': return { k: 'glob', a: short(input.pattern, 28) };
    case 'WebFetch': { let h = ''; try { h = new URL(input.url).hostname; } catch { /* 주소 아님 */ } return { k: 'fetch', a: h }; }
    case 'WebSearch': return { k: 'search', a: short(input.query, 24) };
    case 'Skill': return { k: 'skill', a: short(input.skill || input.command, 24) };
    case 'TodoWrite': return { k: 'todo', a: '' };
    case 'Agent': case 'Task': return { k: 'agent', a: short(input.description, 30) };
    default:
      if (String(name).startsWith('mcp__')) return { k: 'mcp', a: String(name).split('__').pop() };
      return { k: 'tool', a: short(name, 24) };
  }
}

/** claude 실행 파일 찾기: 설정값 그대로 → Windows 면 where.exe 로 실제 경로 */
export function resolveClaude(cfg) {
  const p = cfg.claudePath || 'claude';
  if (path.isAbsolute(p)) return fs.existsSync(p) ? p : null;
  if (IS_WIN) {
    const r = spawnSync('where.exe', [p], { encoding: 'utf8', windowsHide: true });
    const lines = (r.stdout || '').split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    const found = lines.find((l) => /\.exe$/i.test(l)) || lines.find((l) => /\.(cmd|bat)$/i.test(l));
    if (found) return found;
    // 바탕 화면에서 켜면 PATH 가 예전 값일 수 있다 → Claude Code 가 보통 깔리는 자리를 직접 찾는다
    const home = process.env.USERPROFILE || '';
    const known = [
      path.join(home, '.local', 'bin', 'claude.exe'),
      path.join(process.env.APPDATA || path.join(home, 'AppData', 'Roaming'), 'npm', 'claude.cmd'),
      path.join(process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local'), 'Programs', 'claude', 'claude.exe'),
    ];
    return known.find((k) => fs.existsSync(k)) || null;
  }
  const r = spawnSync('which', [p], { encoding: 'utf8' });
  return r.status === 0 ? r.stdout.trim() : null;
}

export function claudeVersion(cfg) {
  if (cfg.demo) return { ok: true, version: '데모(가짜 Claude)' };
  const exe = resolveClaude(cfg);
  if (!exe) return { ok: false, version: '' };
  const r = /\.(cmd|bat)$/i.test(exe)
    ? spawnSync('cmd.exe', ['/d', '/c', exe, '--version'], { encoding: 'utf8', windowsHide: true, timeout: 15000 })
    : spawnSync(exe, ['--version'], { encoding: 'utf8', windowsHide: true, timeout: 15000 });
  return { ok: r.status === 0, version: (r.stdout || '').trim().split('\n')[0] || '' };
}

function killTree(child) {
  if (!child || child.exitCode !== null) return;
  if (IS_WIN) spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true });
  else { try { child.kill('SIGTERM'); } catch { /* 이미 끝남 */ } }
}

/**
 * claude -p 한 번 실행.
 * opts: { cwd, prompt, allow:[], deny:[], addDirs:[], env:{}, resume, timeoutMin, settingsFile, onAct(act), onLog(line), mockTag }
 * 결과: { ok, result, sessionId, isError, denials:[], exitCode, timedOut }
 */
export function runClaude(cfg, opts) {
  return new Promise((resolve) => {
    const settings = {
      permissions: {
        allow: opts.allow || [],
        deny: opts.deny || [],
        additionalDirectories: opts.addDirs || [],
        defaultMode: 'default',
      },
    };
    writeJsonAtomic(opts.settingsFile, settings);
    const args = ['-p', '--output-format', 'stream-json', '--verbose', '--settings', opts.settingsFile];
    if (opts.resume) {
      if (!UUID_RE.test(opts.resume)) return resolve({ ok: false, result: '', isError: true, denials: [], error: '세션 ID 형식 오류' });
      args.push('--resume', opts.resume);
    }

    let cmd; let cmdArgs;
    if (cfg.demo) {
      cmd = process.execPath; cmdArgs = [MOCK, ...args];
    } else {
      const exe = resolveClaude(cfg);
      if (!exe) return resolve({ ok: false, result: '', isError: true, denials: [], error: 'claude 실행 파일을 찾지 못했습니다(설정 claudePath 확인)' });
      if (/\.(cmd|bat)$/i.test(exe)) {
        // npm 으로 깐 claude.cmd — cmd.exe 를 거쳐야 한다. 인자는 우리가 만든 고정값뿐이지만 한 번 더 검사한다.
        if (![exe, ...args].every((a) => SAFE_ARG.test(a))) return resolve({ ok: false, result: '', isError: true, denials: [], error: '실행 인자에 허용되지 않는 글자가 있습니다' });
        cmd = 'cmd.exe'; cmdArgs = ['/d', '/s', '/c', exe, ...args];
      } else { cmd = exe; cmdArgs = args; }
    }

    const env = { ...process.env, ...(opts.env || {}), PYTHONIOENCODING: 'utf-8', AI_OFFICE_JOB: '1' };
    if (cfg.demo && opts.mockTag) env.AI_OFFICE_MOCK_TAG = opts.mockTag;
    let child;
    try {
      child = spawn(cmd, cmdArgs, { cwd: opts.cwd, env, windowsHide: true, shell: false });
    } catch (e) {
      return resolve({ ok: false, result: '', isError: true, denials: [], error: `실행 실패: ${e.message}` });
    }
    const out = { ok: false, result: '', sessionId: null, isError: true, denials: [], exitCode: null, timedOut: false, error: '' };
    let buf = '';
    let errTail = '';
    const handle = (line) => {
      if (!line.trim()) return;
      let m;
      try { m = JSON.parse(line); } catch { opts.onLog?.(short(line, 300)); return; }
      if (m.session_id && !out.sessionId) out.sessionId = m.session_id;
      if (m.type === 'assistant' && Array.isArray(m.message?.content)) {
        for (const b of m.message.content) {
          if (b.type === 'tool_use') { const act = toolAct(b.name, b.input || {}); opts.onAct?.(act); opts.onLog?.(`도구 ${b.name} ${act.a}`); }
          else if (b.type === 'text' && b.text?.trim()) { opts.onAct?.({ k: 'text', a: short(b.text.replace(/[#*`>|]/g, ''), 60) }); }
        }
      } else if (m.type === 'result') {
        out.result = String(m.result ?? '');
        out.isError = !!m.is_error || m.subtype !== 'success';
        out.denials = Array.isArray(m.permission_denials) ? m.permission_denials.map((d) => d.tool_name || String(d)) : [];
        if (m.session_id) out.sessionId = m.session_id;
      }
    };
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (c) => {
      buf += c;
      let i;
      while ((i = buf.indexOf('\n')) >= 0) { handle(buf.slice(0, i)); buf = buf.slice(i + 1); }
    });
    child.stderr.setEncoding('utf8');
    child.stderr.on('data', (c) => { errTail = (errTail + c).slice(-2000); });
    child.stdin.on('error', () => { /* 일찍 끝나면 무시 */ });
    child.stdin.end(opts.prompt, 'utf8');

    const limit = Math.max(0.02, opts.timeoutMin || 60) * 60 * 1000;
    const timer = setTimeout(() => { out.timedOut = true; killTree(child); }, limit);
    child.on('error', (e) => { out.error = `실행 실패: ${e.message}`; });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (buf) handle(buf);
      out.exitCode = code;
      out.ok = code === 0 && !out.isError && !out.timedOut;
      if (!out.ok && !out.error) {
        out.error = out.timedOut ? `제한 시간(${opts.timeoutMin}분)을 넘겨 중단했습니다`
          : short(errTail || out.result || `종료 코드 ${code}`, 400);
      }
      resolve(out);
    });
    opts.onStart?.(() => killTree(child));
  });
}

/** slide-svg 복사본의 가상환경 Python 경로 */
export function venvPython(slideSvg) {
  const win = path.join(slideSvg, '.venv', 'Scripts', 'python.exe');
  const nix = path.join(slideSvg, '.venv', 'bin', 'python3');
  if (fs.existsSync(win)) return win;
  if (fs.existsSync(nix)) return nix;
  return null;
}

/** 정해진 Python 스크립트를 정해진 인자로 실행(셸 없음). 결과 { code, stdout, stderr } */
export function runPython(py, args, { cwd, timeoutMin = 10 } = {}) {
  return new Promise((resolve) => {
    const child = spawn(py, args, { cwd, windowsHide: true, shell: false, env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' } });
    let stdout = ''; let stderr = '';
    child.stdout.setEncoding('utf8'); child.stderr.setEncoding('utf8');
    child.stdout.on('data', (c) => { stdout = (stdout + c).slice(-200000); });
    child.stderr.on('data', (c) => { stderr = (stderr + c).slice(-20000); });
    const timer = setTimeout(() => killTree(child), timeoutMin * 60 * 1000);
    child.on('error', (e) => { stderr += e.message; });
    child.on('close', (code) => { clearTimeout(timer); resolve({ code, stdout, stderr }); });
  });
}
