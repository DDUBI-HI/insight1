// 작업 허용 목록(이 목록에 없는 일은 실행하지 않는다) + 승인 처리.
import fs from 'node:fs';
import path from 'node:path';
import { chiefJobs } from './chief.mjs';
import { team1Jobs } from './team1.mjs';
import { team2Jobs } from './team2.mjs';
import { team3Jobs } from './team3.mjs';
import { TEAMS, WORKERS } from './common.mjs';
import { applyUpdate } from '../instructors.mjs';
import { copyNoOverwrite, isInside } from '../util.mjs';

const ALL = [...chiefJobs, ...team1Jobs, ...team2Jobs, ...team3Jobs];
const BY_TYPE = new Map(ALL.map((d) => [d.type, d]));
for (const d of ALL) {
  if (!TEAMS[d.team] || !WORKERS[d.worker]) throw new Error(`작업 정의 오류: ${d.type}`);
}

export const registry = {
  get: (type) => BY_TYPE.get(String(type || '')),
  list: () => ALL,
  /** 화면에 보낼 모양(함수 없이) */
  publicList: () => ALL.filter((d) => d.panel !== false).map((d) => ({
    type: d.type, team: d.team, teamLabel: TEAMS[d.team], worker: d.worker, workerName: WORKERS[d.worker].name,
    label: d.label, desc: d.desc, heavy: !!d.heavy, fields: d.fields || [], internal: d.chiefCallable === false && (d.fields || []).some((f) => /JobId$/.test(f.name)),
  })),
};

/**
 * 승인함 결정 처리. 반환: { outcome, enqueue: [{type, params}] }
 * 외부로 나가는 일(고객사 메일·인스타그램 게시)은 여기서도 직접 하지 않는다.
 */
export async function decide(approval, decision, note, { cfg, paths, postN8n }) {
  const approve = decision === 'approve';
  const k = approval.kind;
  if (k === 'proposal.draft.confirm') {
    return approve ? { outcome: '맞춤 초안 작업을 시작합니다', enqueue: [{ type: 'proposal.draft', params: { inquiryJobId: approval.data.inquiryJobId } }] }
      : { outcome: '맞춤 초안을 만들지 않기로 했습니다' };
  }
  if (k === 'chief.dispatch') {
    return approve ? { outcome: '비서실장 제안 작업을 시작합니다', enqueue: [{ type: approval.data.type, params: approval.data.params }] }
      : { outcome: '실행하지 않기로 했습니다' };
  }
  if (k === 'proposal.review' || k === 'design.review') {
    if (!approve) return { outcome: `반려 — ${note || '의견 없음'}` };
    const copied = [];
    if (k === 'proposal.review') {
      for (const f of approval.files || []) {
        if (fs.existsSync(f) && fs.statSync(f).isFile()) copied.push(copyNoOverwrite(f, path.join(paths.approved, path.basename(f))));
      }
    }
    return { outcome: k === 'proposal.review' ? `검토 완료 — ${copied.length ? '검토완료 폴더로 복사했습니다. ' : ''}고객사 메일은 직접 보내 주세요(자동 발송 없음)` : '확인 완료', files: copied };
  }
  if (k === 'instructor.update') {
    if (!approve) return { outcome: `반영하지 않음 — ${note || '의견 없음'}` };
    const r = applyUpdate(paths.instructorPool, paths.backups, approval.data.plan);
    return { outcome: `강사풀에 반영했습니다(${r.id}, 전체 ${r.count}명). ${r.backup ? `반영 전 파일 백업: ${r.backup}` : '새 강사풀 파일을 만들었습니다'}` };
  }
  if (k === 'cardnews.approve') {
    if (approve) return { outcome: '카드뉴스 완성 작업을 시작합니다', enqueue: [{ type: 'cardnews.render', params: { draftJobId: approval.data.draftJobId } }] };
    if (decision === 'revise' && note) return { outcome: '수정 요청을 보냈습니다', enqueue: [{ type: 'cardnews.revise', params: { draftJobId: approval.data.draftJobId, note } }] };
    return { outcome: '이 초안은 쓰지 않기로 했습니다' };
  }
  if (k === 'instagram.publish') {
    if (!approve) return { outcome: `게시하지 않음 — ${note || '의견 없음'}` };
    const hook = cfg.n8n?.webhooks?.instagramPublish;
    if (cfg.instagram?.enabled && hook) {
      const files = (approval.files || []).filter((f) => isInside(paths.root, f));
      const r = await postN8n(hook, { action: 'instagram.publish', slug: approval.data.slug, caption: approval.detail, files });
      return { outcome: r.ok ? 'n8n 인스타그램 흐름에 넘겼습니다(게시 결과는 n8n 실행 기록에서 확인)' : `n8n 전달 실패: ${r.error}` };
    }
    return { outcome: '인스타그램 미연동 — 자동 게시하지 않았습니다. 콘텐츠 폴더의 압축 파일로 직접 올려 주세요.' };
  }
  return { outcome: approve ? '승인' : '반려' };
}
