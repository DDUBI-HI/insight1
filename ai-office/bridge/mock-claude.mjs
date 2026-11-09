#!/usr/bin/env node
// 데모·시험용 가짜 Claude. 진짜 claude -p 처럼 stream-json 을 한 줄씩 내보내지만
// 아무 파일도 고치지 않고, Claude 사용량도 쓰지 않는다. 작업 종류는 AI_OFFICE_MOCK_TAG 로 받는다.
import crypto from 'node:crypto';

const tag = process.env.AI_OFFICE_MOCK_TAG || 'generic';
const speed = Number(process.env.AI_OFFICE_MOCK_MS || 900);
const args = process.argv.slice(2);
const resumeIdx = args.indexOf('--resume');
const sessionId = resumeIdx >= 0 ? args[resumeIdx + 1] : crypto.randomUUID();

let prompt = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => { prompt += c; });
process.stdin.on('end', run);

const say = (o) => process.stdout.write(JSON.stringify(o) + '\n');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tool = (name, input) => say({ type: 'assistant', session_id: sessionId, message: { content: [{ type: 'tool_use', id: crypto.randomUUID(), name, input }] } });
const text = (t) => say({ type: 'assistant', session_id: sessionId, message: { content: [{ type: 'text', text: t }] } });

const RESULTS = {
  'chief.request': () => '```json\n' + JSON.stringify({
    reply: '요청을 확인했습니다. 콘텐츠마케팅팀에 이번 주 트렌드 조사를 맡기겠습니다.',
    actions: [{ type: 'trend.research', params: { focus: 'AI 리더십' }, reason: '카드뉴스 주제를 먼저 정해야 합니다' }],
  }, null, 2) + '\n```',
  'inquiry.analyze': () => '```json\n' + JSON.stringify({
    summary: '중견 제조사 HR 담당자가 팀장 대상 성과 피드백 교육을 찾고 있습니다.',
    company: null, target: '팀장 20명', headcount: '20', schedule: '12월 중 1일(8H)', location: null,
    format: '집체', budget: null, needs: ['성과 피드백', '1on1 코칭'], company_hint: '제조업 중견기업',
    match: { project: 'mbo_ai_coaching_generic', reason: '성과 피드백·코칭 니즈가 MBO 범용본과 맞습니다', confidence: 0.82 },
  }, null, 2) + '\n```',
  'inquiry.queue': () => '할 일 없음',
  'proposal.draft': () => '맞춤본 수정을 마쳤습니다. 표지·기획 배경·커리큘럼 3개 페이지를 고쳤습니다.\nCHANGES: 표지 대상 \'팀장 20명\' 반영 / 기획 배경에 성과 피드백 니즈 반영 / 커리큘럼 1on1 모듈 강조',
  'proposal.generic': () => '범용본을 만들었습니다. verify_deck PASS.',
  'instructor.intake': () => '```json\n' + JSON.stringify({
    name: '홍길동', email: 'hong.sample@example.com', phone: '010-0000-0000', title: '리더십 전문 강사',
    fields: ['리더십', '코칭'], career: ['(예시) OO그룹 인재개발원 10년', '(예시) 코칭 전문 기업 대표'],
    programs: ['팀장 코칭 리더십', '성과 피드백 워크숍'], education: '(예시) OO대학교 교육학 석사',
    certifications: ['(예시) KPC 코치'], summary: '테스트용 가상 강사 프로필입니다.',
  }, null, 2) + '\n```',
  'trend.research': () => '```json\n' + JSON.stringify({
    trends: [
      { title: '(데모) 팀장 대상 AI 활용 리더십 교육 수요 증가', summary: '데모 데이터입니다. 실제 조사 결과가 아닙니다.', source_url: '' },
      { title: '(데모) 마이크로러닝과 현업 적용 측정', summary: '데모 데이터입니다.', source_url: '' },
    ],
    topics: [{ topic: '팀장의 AI 피드백 대화법', angle: '데모 주제', audience: '기업 HR·교육 담당자' }],
  }, null, 2) + '\n```',
  'cardnews.draft': () => '| 카드 | 템플릿 | 문구 요약 |\n|---|---|---|\n| 1 | cn-cover | (데모) 팀장의 AI 피드백 대화법 |\n| 2 | cn-intro | (데모) 도입 |\n\n```\n(데모) 인스타그램 문구 초안\n```\nSLUG: 2026-11-demo-ai-feedback',
  'cardnews.revise': () => '수정 의견을 반영했습니다.\nSLUG: 2026-11-demo-ai-feedback',
  'cardnews.render': () => '렌더와 압축을 마쳤습니다.\nZIP: cardnews/dist/2026-11-demo-ai-feedback.zip',
};

async function run() {
  say({ type: 'system', subtype: 'init', session_id: sessionId, tools: [] });
  await sleep(speed);
  text('요청을 확인하고 자료를 읽겠습니다.');
  await sleep(speed);
  tool('Read', { file_path: tag.startsWith('cardnews') ? 'cardnews/COPY_GUIDE.md' : 'README.md' });
  await sleep(speed);
  if (tag === 'trend.research' || tag.startsWith('cardnews')) { tool('WebSearch', { query: 'HRD 트렌드 2026' }); await sleep(speed); }
  if (tag.startsWith('proposal') || tag === 'cardnews.render') {
    tool('Bash', { command: '.claude/skills/slide/scripts/_py.sh ...', description: 'PPTX 만들기(데모)' });
    await sleep(speed * 2);
  }
  const result = (RESULTS[tag] || (() => '데모 작업을 마쳤습니다.'))();
  text('정리했습니다.');
  await sleep(speed / 2);
  say({ type: 'result', subtype: 'success', is_error: false, session_id: sessionId, result, permission_denials: [], num_turns: 4 });
}
