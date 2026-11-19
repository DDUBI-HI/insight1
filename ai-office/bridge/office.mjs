// 3D 사무실 화면용 스냅샷 — claude-3d-frog-office 의 GET /api/office 형식(CONTRACT 4절)에 맞춘다.
// 직원 = WORKERS. 승인 대기 > 일하는 중 > 쉬는 중.
import { TEAMS, WORKERS } from './jobs/common.mjs';

export function officeSnapshot({ store, runner, cfg }) {
  const now = new Date();
  const dayStart = new Date(now); dayStart.setHours(0, 0, 0, 0);
  const pending = store.pendingApprovals();
  const queued = runner.queued();
  const cur = runner.current ? store.jobs.get(runner.current.jobId) : null;
  const people = Object.entries(WORKERS).map(([key, w]) => {
    const mine = pending.filter((a) => a.worker === key);
    const running = cur && cur.worker === key ? cur : null;
    const waiting = queued.filter((j) => j.worker === key);
    const status = mine.length ? 'decision' : running ? 'working' : 'rest';
    const doing = running ? (runner.current.act || { k: 'text', a: running.title }) : null;
    const todays = [...store.jobs.values()].filter((j) => j.worker === key && Date.parse(j.createdAt) >= dayStart.getTime()).length;
    return {
      id: `ai-office/${key}`,
      name: w.name,
      path: `${TEAMS[w.team]} — ${w.role}`,
      status,
      pending: mine.length,
      ask: mine.length ? String(mine[0].title).slice(0, 80) : '',
      sessions: Math.max(1, todays),
      source: 'hook',
      commits: null,
      kid: false,
      home: null,
      subs: waiting.slice(0, 12).map((j) => ({ id: j.id.slice(-6), type: '대기', desc: j.title, doing: null })),
      subCount: 0,
      doing,
      log: store.events.filter((e) => e.worker === key).slice(-8).map((e) => ({ at: e.at, k: e.k, a: e.a })),
    };
  });
  return { version: 1, now: now.toISOString(), hooks: true, demo: !!cfg.demo, people };
}
