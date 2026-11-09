"use strict";
// AI 사무실 업무 패널 — 승인함·업무 요청·작업 현황·연결 상태.
// 서버에서 받은 글은 전부 textContent 로만 넣는다(HTML 로 해석하지 않는다).

(() => {
  const $ = (id) => document.getElementById(id);
  const S = { token: null, types: [], apSig: "", jobSig: "", open: new Set(), status: null };
  const TAB_KEY = "aiOffice.tab";

  function el(tag, attrs = {}, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === null || v === false) continue;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat()) if (c != null) e.append(c instanceof Node ? c : document.createTextNode(String(c)));
    return e;
  }
  const when = (iso) => (iso ? new Date(iso).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "");
  let flashTimer;
  function flash(msg, bad = false) {
    const f = $("flash");
    f.textContent = msg; f.className = "flash" + (bad ? " bad" : ""); f.hidden = false;
    clearTimeout(flashTimer); flashTimer = setTimeout(() => { f.hidden = true; }, bad ? 9000 : 4500);
  }

  async function api(method, path, body) {
    const res = await fetch(path, {
      method, cache: "no-store",
      headers: { "x-office-token": S.token || "", ...(body ? { "content-type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `오류 ${res.status}`);
    return data;
  }

  // ---------- 탭 ----------
  function showTab(name) {
    for (const b of document.querySelectorAll(".tabs button")) b.setAttribute("aria-selected", String(b.dataset.tab === name));
    for (const s of document.querySelectorAll(".tab")) s.hidden = s.id !== "tab-" + name;
    try { localStorage.setItem(TAB_KEY, name); } catch { /* 저장 못 해도 됨 */ }
    if (name === "status") loadStatus();
  }
  for (const b of document.querySelectorAll(".tabs button")) b.addEventListener("click", () => showTab(b.dataset.tab));

  // ---------- 승인함 ----------
  const KIND = {
    "proposal.draft.confirm": { ok: "초안 만들기 시작", no: "만들지 않음" },
    "chief.dispatch": { ok: "실행 승인", no: "실행 안 함" },
    "proposal.review": { ok: "검토 완료", no: "반려(다시 검토)" },
    "design.review": { ok: "확인 완료", no: "반려" },
    "instructor.update": { ok: "강사풀에 반영", no: "반영 안 함" },
    "cardnews.approve": { ok: "승인하고 완성하기", no: "이 초안 쓰지 않음", revise: "수정 요청 보내기" },
    "instagram.publish": { ok: "게시 승인", no: "게시 안 함" },
  };
  async function openFile(body) {
    try {
      const r = await api("POST", "/api/open", body);
      flash(r.opened ? "탐색기에서 열었습니다" : `위치: ${r.path}`);
    } catch (e) { flash(e.message, true); }
  }
  function fileList(files, mk) {
    if (!files?.length) return null;
    return el("div", { class: "row" }, ...files.map((f, i) => el("button", { class: "btn link", type: "button", title: f, text: `📂 ${f.split(/[\\/]/).pop()}`, onclick: () => openFile(mk(i)) })));
  }
  function approvalCard(a) {
    const k = KIND[a.kind] || { ok: "승인", no: "반려" };
    const note = el("textarea", { class: "note", placeholder: k.revise ? "수정할 점을 적고 '수정 요청 보내기'를 누르세요" : "의견(선택)" });
    const buttons = el("div", { class: "row" });
    const go = async (decision) => {
      if (decision === "revise" && !note.value.trim()) { flash("수정할 점을 적어 주세요", true); return; }
      for (const b of buttons.querySelectorAll("button")) b.disabled = true;
      try {
        const r = await api("POST", `/api/approvals/${a.id}`, { decision, note: note.value });
        flash(r.outcome || "처리했습니다");
        S.apSig = ""; await loadApprovals(); loadJobs();
      } catch (e) { flash(e.message, true); for (const b of buttons.querySelectorAll("button")) b.disabled = false; }
    };
    buttons.append(el("button", { class: "btn ok", type: "button", text: k.ok, onclick: () => go("approve") }));
    if (k.revise) buttons.append(el("button", { class: "btn soft", type: "button", text: k.revise, onclick: () => go("revise") }));
    buttons.append(el("button", { class: "btn bad", type: "button", text: k.no, onclick: () => go("reject") }));
    return el("li", { class: "card" },
      el("h3", { text: a.title }),
      el("p", { class: "meta", text: `${workerName(a.worker)} · ${when(a.createdAt)} · 작업 ${a.jobId || "-"}` }),
      a.detail ? el("pre", { class: "detail", text: a.detail }) : null,
      fileList(a.files, (i) => ({ approvalId: a.id, index: i })),
      note, buttons);
  }
  async function loadApprovals() {
    const list = await api("GET", "/api/approvals");
    const c = $("ap-count"); c.textContent = String(list.length); c.hidden = !list.length;
    document.title = (list.length ? `(${list.length}) ` : "") + "AI 사무실 업무 패널";
    const sig = list.map((a) => a.id).join(",");
    if (sig === S.apSig) return;
    S.apSig = sig;
    const ul = $("approvals");
    ul.replaceChildren(...(list.length ? list.map(approvalCard) : [el("li", { class: "empty", text: "승인할 일이 없습니다" })]));
    const past = (await api("GET", "/api/approvals?all=1")).filter((a) => a.status !== "pending").slice(0, 30);
    $("approvals-past").replaceChildren(...past.map((a) => el("li", { class: "card" },
      el("h3", { text: `${{ approved: "✔ 승인", rejected: "✖ 반려", revised: "✎ 수정 요청" }[a.status] || a.status} · ${a.title}` }),
      el("p", { class: "meta", text: `${when(a.decidedAt)} — ${a.outcome || ""}${a.note ? ` / 의견: ${a.note}` : ""}` }))));
  }

  // ---------- 업무 요청 ----------
  const workerName = (key) => S.status?.workers?.[key]?.name || S.types.find((t) => t.worker === key)?.workerName || key || "";
  function field(f) {
    const id = `f-${Math.random().toString(36).slice(2)}`;
    if (f.kind === "checkbox") return el("label", { class: "check", for: id }, el("input", { type: "checkbox", id, name: f.name }), f.label);
    const input = f.kind === "textarea"
      ? el("textarea", { id, name: f.name, rows: 5, maxlength: f.max || 8000, required: f.required, placeholder: f.placeholder })
      : el("input", { id, name: f.name, type: f.kind === "number" ? "number" : "text", maxlength: f.max || 400, required: f.required, placeholder: f.placeholder });
    return el("div", { class: "form" }, el("label", { for: id, text: f.label + (f.required ? " *" : "") }), input,
      f.kind === "file" ? el("small", { text: "파일을 Shift + 오른쪽 클릭 → '경로로 복사' 후 붙여 넣으세요. C:\\AI-OFFICE 안의 파일만 됩니다." }) : null);
  }
  function jobForm(t) {
    const form = el("form", { class: "form" }, ...t.fields.map(field), el("button", { class: "btn", type: "submit", text: t.fields.length ? "요청하기" : "지금 실행" }));
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const params = {};
      for (const f of t.fields) {
        const i = form.elements[f.name];
        params[f.name] = f.kind === "checkbox" ? i.checked : i.value;
      }
      const btn = form.querySelector("button[type=submit]"); btn.disabled = true;
      try {
        const j = await api("POST", "/api/jobs", { type: t.type, params });
        flash(`접수했습니다 — ${j.title} (작업 현황에서 진행을 봅니다)`);
        form.reset(); S.jobSig = ""; loadJobs();
      } catch (e) { flash(e.message, true); } finally { btn.disabled = false; }
    });
    return el("div", { class: "card" },
      el("h3", {}, t.label, " ", t.heavy ? el("span", { class: "pill heavy", text: "오래 걸림 · 사용량 큼" }) : null),
      el("p", { class: "meta", text: `${t.workerName} · ${t.desc}` }), form);
  }
  function renderForms() {
    const teams = {};
    for (const t of S.types) {
      if (t.team === "chief" && t.type === "chief.request") continue;
      if (t.internal) continue;
      (teams[t.teamLabel] ||= []).push(t);
    }
    $("team-forms").replaceChildren(...Object.entries(teams).map(([label, ts]) =>
      el("section", { class: "team" }, el("h2", { text: label }), el("div", { class: "grid2" }, ...ts.map(jobForm)))));
  }
  $("chief-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = ev.currentTarget; const btn = f.querySelector("button"); btn.disabled = true;
    try {
      await api("POST", "/api/jobs", { type: "chief.request", params: { text: f.elements.text.value } });
      flash("비서실장에게 보냈습니다. 작업 현황과 승인함을 확인하세요."); f.reset(); S.jobSig = ""; loadJobs();
    } catch (e) { flash(e.message, true); } finally { btn.disabled = false; }
  });

  // ---------- 작업 현황 ----------
  const ST = { queued: "대기", running: "진행 중", done: "완료", failed: "실패", canceled: "취소됨" };
  function jobItem(j) {
    const body = el("div", { class: "jobbody" }, el("p", { class: "meta", text: "불러오는 중…" }));
    const det = el("details", { ontoggle: () => { if (det.open) { S.open.add(j.id); fillJob(j.id, body); } else S.open.delete(j.id); } },
      el("summary", {}, el("span", { class: `st ${j.status}`, text: ST[j.status] || j.status }), el("span", { class: "title", text: j.title }),
        el("span", { class: "meta", text: `${j.teamLabel} · ${j.workerName} · ${when(j.createdAt)} · ${j.source === "n8n" ? "n8n 요청" : j.source === "approval" ? "승인 후" : j.source === "chain" ? "이어서" : j.source === "schedule" ? "예약" : "패널"}` })),
      el("p", { text: j.error ? `⚠ ${j.error}` : j.summary || "" }), body);
    if (S.open.has(j.id)) { det.open = true; fillJob(j.id, body); }
    return el("li", {}, det);
  }
  async function fillJob(id, box) {
    try {
      const j = await api("GET", `/api/jobs/${id}`);
      const kids = [];
      if (j.outputs?.length) kids.push(el("p", { class: "meta", text: "결과 파일" }), fileList(j.outputs, (i) => ({ jobId: j.id, index: i })));
      if (j.status === "queued" || j.status === "running") kids.push(el("button", { class: "btn bad", type: "button", text: "작업 취소", onclick: async () => { try { await api("POST", `/api/jobs/${id}/cancel`); flash("취소를 요청했습니다"); S.jobSig = ""; loadJobs(); } catch (e) { flash(e.message, true); } } }));
      kids.push(el("pre", { class: "detail", text: (j.log || []).map((l) => `${when(l.at)}  ${l.line}`).join("\n") || "기록 없음" }));
      box.replaceChildren(...kids);
    } catch (e) { box.replaceChildren(el("p", { class: "meta", text: e.message })); }
  }
  async function loadJobs() {
    const list = await api("GET", "/api/jobs?limit=60");
    const run = list.find((j) => j.status === "running");
    const q = list.filter((j) => j.status === "queued").length;
    $("run-chip").textContent = run ? `진행 중: ${run.title}${q ? ` · 대기 ${q}건` : ""}` : q ? `대기 ${q}건` : "쉬는 중";
    const sig = list.map((j) => j.id + j.status).join(",");
    if (sig === S.jobSig) { for (const id of S.open) { const box = document.querySelector(`[data-job="${id}"] .jobbody`); if (box) fillJob(id, box); } return; }
    S.jobSig = sig;
    $("jobs").replaceChildren(...(list.length ? list.map((j) => { const li = jobItem(j); li.dataset.job = j.id; return li; }) : [el("li", { class: "empty", text: "아직 작업이 없습니다" })]));
  }

  // ---------- 연결 상태 ----------
  function stateCell(kind, text) { return el("td", {}, el("span", { class: `state ${kind}`, text })); }
  async function loadStatus() {
    try {
      const s = await api("GET", "/api/status");
      S.status = s;
      $("demo-chip").hidden = !s.demo;
      const rows = [
        ["실행 모드", s.demo ? ["warn", "데모 — 가짜 Claude 로 화면과 흐름만 시험합니다"] : ["ok", "실제 업무 모드"]],
        ["Claude Code (claude -p)", s.claude?.ok ? ["ok", `연결됨 · ${s.claude.version}`] : ["bad", "찾지 못함 — 설치·로그인 확인, 설정 claudePath"]],
        ["PPT 디자인 에이전트 (slide-svg 복사본)", s.agents.slideSvg.ok ? ["ok", `사용 가능 · ${s.agents.slideSvg.msg}`] : [s.demo ? "warn" : "bad", s.agents.slideSvg.msg]],
        ["카드뉴스 에이전트 (insight1 복사본)", s.agents.cardnews.ok ? ["ok", `사용 가능 · ${s.agents.cardnews.msg}`] : [s.demo ? "warn" : "bad", s.agents.cardnews.msg]],
        ["n8n (이 PC → n8n)", s.n8n.reachable ? ["ok", `연결됨 · ${s.n8n.baseUrl}`] : ["bad", `응답 없음 · ${s.n8n.baseUrl}`]],
        ["n8n → AI 사무실 접속", s.n8n.lastRequestFromDocker ? ["ok", `확인됨 · 마지막 ${when(s.n8n.lastRequestFromDocker)}`] : ["warn", "미확인 — n8n 에서 아직 요청이 온 적 없습니다(연결테스트 스크립트로 확인)"]],
        ["작업 완료 알림 (n8n 웹훅)", s.webhooks.events ? ["ok", "설정됨(발송 결과는 n8n 실행 기록에서 확인)"] : ["warn", "미설정 — 패널에서만 확인"]],
        ["인스타그램 게시", s.instagram.enabled ? ["warn", "n8n 흐름으로 넘김(실제 게시는 n8n 에서 확인)"] : ["warn", "미연동 — 승인 후 압축 파일로 직접 게시"]],
        ["고객사 메일 발송", ["ok", "자동 발송 없음(항상 사람이 직접 보냄)"]],
        ["작업 대기", [s.queue.running ? "ok" : "ok", s.queue.running ? `진행 중: ${s.queue.running.title} · 대기 ${s.queue.queued}건` : `쉬는 중 · 대기 ${s.queue.queued}건`]],
        ["내장 예약", s.schedule.length ? ["ok", s.schedule.map((x) => `${x.type} ${x.days?.join(",") || "매일"} ${x.time}`).join(" / ")] : ["warn", "없음(n8n 예약 흐름 사용 또는 설정 schedule)"]],
        ["데이터 폴더", ["ok", s.dataDir]],
        ["파일을 받을 수 있는 폴더", ["ok", s.inputRoots.join(", ")]],
      ];
      $("status-rows").replaceChildren(...rows.map(([k, [kind, v]]) => el("tr", {}, el("th", { text: k }), stateCell(kind, v))));
      const folders = [["inquiry", "교육문의"], ["review", "제안서 검토대기"], ["approved", "제안서 검토완료"], ["instructors", "강사관리"], ["instructorInbox", "신규 강사 프로필 넣는 곳"], ["trends", "트렌드"], ["cardnews", "카드뉴스"], ["reports", "보고서"], ["backups", "백업"]];
      $("folders").replaceChildren(...folders.map(([key, label]) => el("button", { class: "btn ghost", type: "button", text: `📂 ${label}`, onclick: () => openFile({ folder: key }) })));
    } catch (e) { flash(e.message, true); }
  }

  // ---------- 시작 ----------
  async function start() {
    try {
      const r = await fetch("/api/session", { cache: "no-store" });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "토큰을 받지 못했습니다");
      S.token = (await r.json()).token;
    } catch (e) {
      flash(`${e.message} — 이 PC 에서 http://127.0.0.1:8765/control.html 로 열어 주세요`, true);
      return;
    }
    try { S.types = await api("GET", "/api/job-types"); } catch (e) { flash(e.message, true); }
    await loadStatus();
    renderForms();
    let tab = "approvals";
    try { tab = localStorage.getItem(TAB_KEY) || tab; } catch { /* 기본값 */ }
    showTab(["approvals", "request", "jobs", "status"].includes(tab) ? tab : "approvals");
    const tick = async () => { if (document.hidden) return; try { await Promise.all([loadApprovals(), loadJobs()]); } catch (e) { flash(e.message, true); } };
    await tick();
    setInterval(tick, 4000);
    setInterval(() => { if (!document.hidden && !$("tab-status").hidden) loadStatus(); }, 30000);
  }
  start();
})();
