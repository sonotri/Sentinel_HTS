"use strict";

const scenarios = [
  { id: "TX-2026-0917", time: "02:14", amount: "2,840,000원", location: "서울 → 베를린", ip: "0.87 / HIGH", device: "처음 보는 Android", velocity: "10분 이내 7회", merchant: "CRYPTO EXCHANGE", action: "차단", score: 92, reasons: ["심야 해외 거래", "고위험 IP", "신규 기기", "짧은 시간 내 반복 결제"], models: {"Local-only": 61, Federated: 92, Centralized: 94} },
  { id: "TX-2026-2048", time: "19:42", amount: "186,000원", location: "서울 → 파리", ip: "0.48 / MEDIUM", device: "처음 보는 iPhone", velocity: "30분 이내 2회", merchant: "TRAVEL BOOKING", action: "추가 인증", score: 58, reasons: ["새로운 해외 위치", "신규 기기", "평소보다 큰 결제 금액"], models: {"Local-only": 37, Federated: 58, Centralized: 62} },
  { id: "TX-2026-3310", time: "13:05", amount: "42,500원", location: "서울 → 서울", ip: "0.08 / LOW", device: "등록된 iPhone", velocity: "2시간 이내 1회", merchant: "GROCERY", action: "승인", score: 7, reasons: ["평소 이용 지역", "등록 기기", "일상적인 금액과 업종"], models: {"Local-only": 11, Federated: 7, Centralized: 6} }
];

const privacyLevels = {
  Low: { noise: "0.00", f1: "0.91", exposure: "높음", stars: 2 },
  Balanced: { noise: "0.05", f1: "0.87", exposure: "낮음", stars: 5 },
  High: { noise: "0.12", f1: "0.76", exposure: "매우 낮음", stars: 4 }
};

const state = { step: 0, scenario: Math.floor(Math.random() * scenarios.length), revealed: false, transaction: null, model: null, attack: null, privacy: null, deal: false };
const app = document.querySelector("#app");

const nav = () => `<div class="sentinel-nav"><div class="brand"><i class="brand-mark">S</i><span><b>SENTINEL BANK</b><small>MAGICAL SECURITY OFFICE</small></span></div></div>`;
const footer = () => `<div class="operator-note">SENTINEL BANK · PRIVACY-PRESERVING FEDERATED FRAUD DETECTION</div>`;
const head = (number, title, description) => `<div class="section-head"><div class="eyebrow"><span>✦</span> MISSION ${number} <span>✦</span></div><h2>${title}</h2><p>${description}</p><div class="ornament"><i></i><b>◆</b><i></i></div></div>`;
const concept = (title, body, extra = "") => `<div class="concept-card ${extra}"><div class="concept-sigil">✦</div><div><small>LEDGER NOTE</small><strong>${title}</strong><p>${body}</p></div></div>`;
const expand = (title, body) => `<details class="static-expander"><summary>${title}</summary><p>${body}</p></details>`;
const stars = count => "✦".repeat(count) + "✧".repeat(5 - count);

function stepper() {
  const labels = ["거래", "모델", "공격", "보호", "결과"];
  return `<div class="stepper">${labels.map((label, i) => {
    const number = i + 1;
    const status = state.step === number ? "active" : state.step > number ? "done" : "";
    return `<div class="step-pill ${status}"><i>${status === "done" ? "✓" : `0${number}`}</i><span>${label}</span></div>`;
  }).join("")}</div>`;
}

function choiceList(key, options, label = "") {
  return `${label ? `<div class="choice-group-label">${label}</div>` : ""}<div class="choice-list">${options.map((option, i) => {
    const selected = state[key] === option;
    return `<div class="st-key-choice_${key}_${i}"><div class="stButton"><button type="button" kind="${selected ? "primary" : "secondary"}" data-choice="${key}" data-value="${option}">${selected ? "SELECTED  ·  " : ""}${option}</button></div></div>`;
  }).join("")}</div>`;
}

function submit(key) {
  return `<div class="st-key-submit_${key}"><div class="stButton"><button type="button" data-submit="${key}" ${state[key] ? "" : "disabled"}>제출하기&nbsp; ✦</button></div></div>`;
}

const next = () => `<div class="st-key-next_mission"><div class="stButton"><button type="button" data-next>다음 임무로 이동&nbsp; →</button></div></div>`;

function landing() {
  return `<section class="landing-shell">
    <div class="dust dust-a"></div><div class="dust dust-b"></div>
    <i class="corner corner-nw"></i><i class="corner corner-ne"></i><i class="corner corner-sw"></i><i class="corner corner-se"></i>
    <div class="landing-copy"><div class="hero-kicker"><span>✦</span> AI SECURITY INITIATION <span>✦</span></div><div class="hero-overline">SENTINEL BANK · SECURITY OFFICE</div><h1>나의 거래는<br><em>안전한가?</em></h1><p>데이터를 공유하지 않고도 금융 위험을 함께 탐지할 수 있을까요?<br>실제 거래 시나리오를 통해 연합 FDS의 판단과 대응 과정을 확인해보세요.</p></div>
    <div class="card-stage" aria-label="SENTINEL 001 카드 앞면과 뒷면 미리보기"><div class="vault-door"><i></i><i></i><i></i><i></i><b>S</b></div><div class="vault-halo"></div><i class="spark spark-one">✦</i><i class="spark spark-two">✧</i><i class="spark spark-three">✦</i><div class="card-shadow"></div><div class="card-face-preview card-back"><img src="Card_Design/2.png" alt="SENTINEL 001 카드 뒷면"><span>BACK · MISSION RECORD</span></div><div class="card-face-preview card-front"><img src="Card_Design/1.png" alt="SENTINEL 001 카드 앞면"><span>FRONT · IDENTITY</span></div></div>
  </section><div class="st-key-enter_security_office landing-action"><div class="stButton"><button type="button" data-enter>Sentinel 카드 발급 · Cyber 보안국 입장&nbsp; ✦</button></div></div>`;
}

function dealOverlay() {
  if (!state.deal) return "";
  state.deal = false;
  return `<div class="deal-overlay" aria-hidden="true"><div class="deal-rays"></div><div class="deal-copy"><small>SENTINEL 001 · ISSUED</small><b>조사관 카드가 지급되었습니다</b></div><div class="issued-card"><div class="issued-card-inner"><img class="issued-face issued-front" src="Card_Design/1.png" alt=""><img class="issued-face issued-back" src="Card_Design/2.png" alt=""></div></div><div class="deal-particles">✦　·　✧　·　✦　·　✧　·　✦</div></div>`;
}

function transactionScreen() {
  const s = scenarios[state.scenario];
  let body = `${head("01", "이 거래를 승인하시겠습니까?", "거래 원장의 단서를 읽고 은행이 취해야 할 조치를 결정하세요.")}${concept("이상거래탐지시스템(Fraud Detection System, FDS)", "FDS는 거래 내역, 고객 정보, 평소 거래 패턴 등을 분석해서 의심되는 이상 거래를 탐지하고 차단하는 기술입니다.")}
  <div class="transaction-card"><div class="ledger-ribbon"><span>TRANSACTION LEDGER</span><b>${s.id}</b></div><div class="amount-hero"><small>${s.merchant}</small><b>${s.amount}</b><span>결제 승인 요청</span></div><div class="transaction-grid"><div class="datum"><span>거래 시간</span><b>${s.time}</b></div><div class="datum"><span>접속 위치</span><b>${s.location}</b></div><div class="datum"><span>접속 IP</span><b>${s.ip}</b></div><div class="datum"><span>사용 기기</span><b>${s.device}</b></div><div class="datum wide"><span>거래 속도</span><b>${s.velocity}</b></div></div><div class="ledger-stamp">REVIEW</div></div><div class="question"><small>YOUR DECISION</small><b>거래 징후를 검토한 후 조치를 선택하세요.</b></div>`;
  if (!state.revealed) return body + choiceList("transaction", ["승인", "추가 인증", "차단"]) + submit("transaction");
  const correct = state.transaction === s.action;
  body += `<div class="result-card ${correct ? "success" : "danger"}"><div class="result-seal">${correct ? "✓" : "!"}</div><div class="eyebrow">SENTINEL ANALYSIS · FRAUD SCORE ${s.score}%</div><h3>AI 권고 · ${s.action}</h3><p>당신의 판단은 <b>${state.transaction}</b>입니다. ${correct ? "AI의 권고와 일치합니다." : "AI의 권고와 다른 선택입니다."}</p><div class="reason-list">${s.reasons.map(reason => `<span>${reason}</span>`).join("")}</div></div>`;
  return body + expand("왜 이런 판단을 내렸나요?", "Fraud Score는 여러 위험 신호를 결합한 확률 점수입니다. 점수만으로 결론을 내리지 않고 거래 맥락과 고객 피해 가능성에 맞는 조치를 선택해야 합니다.") + next();
}

function modelScreen() {
  const s = scenarios[state.scenario];
  let body = `${head("02", "어떤 학습 방법이 적합할까요?", "세 은행의 협업 조건을 확인하고 가장 적합한 학습 방식을 선택하세요.")}${concept("세 가지 학습 방식", '<span class="model-method"><b>Local-only</b><em>한 은행 내부의 거래 데이터만으로 학습합니다.</em></span><span class="model-method"><b>Federated</b><em>원본 거래 데이터는 각 은행에 보관하고, 각 은행의 학습 결과만 안전하게 취합해 공동 모델을 개선합니다.</em></span><span class="model-method"><b>Centralized</b><em>모든 은행의 원본 데이터를 한곳에 모아 하나의 모델을 학습합니다.</em></span>')}
  <div class="model-scenario"><p>세 은행이 공동 FDS를 구축하려 합니다</p><p>은행마다 서로 다른 사기 패턴을 보유하고 있지만 고객의 원본 거래 데이터는 외부로 반출할 수 없습니다.</p><div><span>원본 데이터 반출 금지</span><span>세 은행의 패턴 공동 활용</span><span>개인정보 노출 최소화</span></div></div>
  <div class="bank-network"><div class="bank-row">${["A", "B", "C"].map(bank => `<div class="bank-node"><div class="bank-building"><i>${bank}</i><span></span></div><b>BANK ${bank}</b><small>원본 거래 보관</small></div>`).join("")}</div><div class="network-search"><span></span><b>SEARCHING FOR THE RIGHT CONNECTION</b><span></span></div></div>`;
  if (!state.revealed) return body + choiceList("model", ["Local-only", "Federated", "Centralized"], "탐지 모델") + submit("model");
  const correct = state.model === "Federated";
  const scores = Object.entries(s.models).map(([model, score]) => `<div class="score-chip ${model === "Federated" ? "best" : ""}"><span>${model}</span><b>${score}%</b><small>FRAUD SCORE</small></div>`).join("");
  body += `<div class="result-card ${correct ? "success" : "danger"}"><div class="result-seal">${correct ? "✓" : "!"}</div><div class="eyebrow">SCENARIO RECOMMENDATION</div><h3>권장 방식 · Federated</h3><p>당신의 선택은 <b>${state.model}</b>입니다. 원본 반출 없이 세 은행의 패턴을 함께 활용하려면 Federated가 가장 적합합니다.</p><div class="score-row">${scores}</div></div>`;
  return body + expand("Federated가 왜 유리한가요?", "한 은행에서는 드문 공격이 다른 은행에서는 관측될 수 있습니다. 연합학습은 원본 거래를 중앙에 모으지 않으면서 이런 패턴을 공동으로 학습합니다.") + next();
}

function attackScreen() {
  let body = `${head("03", "공동 모델에 무슨 일이 생겼을까요?", "비정상 업데이트의 흔적을 보고 공격 유형을 추리하세요.")}${concept("세 가지 공격 유형", '<span class="attack-method"><b>Label Flip</b><em>정상과 사기 라벨을 뒤집어 모델이 잘못된 패턴을 학습하게 합니다.</em></span><span class="attack-method"><b>Update Scale</b><em>한 참여자의 학습 결과를 비정상적으로 증폭해 공동 모델을 흔듭니다.</em></span><span class="attack-method"><b>Gradient Leakage</b><em>공유된 학습 정보에서 원본 데이터의 특성이나 민감 정보를 추정합니다.</em></span>', "attack-concept")}
  <div class="attack-ledger"><div class="alert-sigil">!</div><div><small>FEDERATED ROUND 04</small><b>비정상 업데이트 감지</b><span>Bank B · 보안 격리 검토 필요</span></div><div class="attack-metric"><span>업데이트 크기</span><b>× 12.4</b><small>평균 대비</small></div><div class="attack-metric"><span>사기 탐지 점수</span><b>92 → 34</b><small>급격한 하락</small></div><div class="attack-metric"><span>공동 모델 F1</span><b>0.88 → 0.49</b><small>성능 훼손</small></div></div>`;
  if (!state.revealed) return body + choiceList("attack", ["Label Flip", "Update Scale", "Gradient Leakage"], "공격 유형") + submit("attack");
  const correct = state.attack === "Update Scale";
  body += `<div class="result-card attack-result ${correct ? "success" : "danger"}"><div class="result-seal">${correct ? "✓" : "!"}</div><div class="eyebrow">ATTACK IDENTIFIED</div><h3>정답 · Update Scale</h3><p>Bank B가 정상 범위를 벗어난 크기로 모델 업데이트를 증폭했습니다. 하나의 악성 업데이트만으로도 글로벌 모델이 크게 흔들릴 수 있습니다.</p><div class="agent-action"><small>SECURITY AGENT RESPONSE</small><b>업데이트 격리 → Bank B 임시 제외 → 정상 참여자 재집계 → 재검증 요청</b></div></div>`;
  return body + expand("다른 공격은 어떻게 다른가요?", "Label Flip은 사기/정상 라벨을 뒤집어 학습을 오염시킵니다. Gradient Leakage는 공유된 기울기에서 입력 특성이나 라벨을 추정하는 개인정보 공격입니다.") + next();
}

function privacyScreen() {
  let body = `${head("04", "얼마나 강하게 보호하시겠습니까?", "탐지 성능과 개인정보 보호 사이에서 은행의 정책을 결정하세요.")}${concept("Differential Privacy", "학습 정보에 통계적 노이즈를 더해 특정 개인의 데이터가 결과에 드러날 가능성을 낮추는 기술입니다. 노이즈가 커질수록 보호는 강해지지만 탐지 성능은 낮아질 수 있습니다.", "privacy-concept")}
  <div class="privacy-scale"><div class="scale-copy"><small>MODEL UTILITY</small><b>탐지 성능</b></div><div class="balance-scale" aria-label="탐지 성능과 개인정보 보호의 균형"><div class="balance-stand"><i></i><span></span></div><div class="balance-beam"><div class="balance-pan pan-left"><i></i><span></span></div><b>◆</b><div class="balance-pan pan-right"><i></i><span></span></div></div></div><div class="scale-copy"><small>DATA SHIELD</small><b>개인정보 보호</b></div></div>`;
  if (!state.revealed) return body + choiceList("privacy", ["Low", "Balanced", "High"], "보호 수준") + submit("privacy");
  const p = privacyLevels[state.privacy];
  body += `<div class="result-card success"><div class="result-seal">ε</div><div class="eyebrow">PRIVACY POLICY · ${state.privacy.toUpperCase()}</div><h3>선택한 보호 수준을 적용합니다.</h3><div class="score-row"><div class="score-chip"><span>DP 노이즈</span><b>${p.noise}</b><small>NOISE</small></div><div class="score-chip"><span>탐지 성능</span><b>${p.f1}</b><small>F1 SCORE</small></div><div class="score-chip best"><span>정보 노출</span><b>${p.exposure}</b><small>EXPOSURE</small></div></div></div>`;
  return body + expand("보호 수준은 높을수록 좋은가요?", "항상 그렇지는 않습니다. High는 정보 노출을 강하게 줄이지만 실제 사기 패턴까지 흐릴 수 있습니다. 위험 수준과 규제 요구사항을 만족하면서 필요한 탐지력을 유지하는 균형이 중요합니다.") + next();
}

function resultScreen() {
  const s = scenarios[state.scenario];
  const judgment = state.transaction === s.action ? 5 : 3;
  const defense = state.attack === "Update Scale" ? 5 : 3;
  const privacy = privacyLevels[state.privacy].stars;
  const total = judgment + defense + privacy + (state.model === "Federated" ? 1 : 0);
  const rank = total >= 15 ? "SENTINEL ARCHITECT" : total >= 12 ? "SECURITY ANALYST" : "RISK INVESTIGATOR";
  return `${head("05", "보안 조사관 최종 기록", "판단력, 방어력, 프라이버시 균형을 종합한 당신의 인증 결과입니다.")}
  <div class="result-showcase"><div class="completed-card"><img src="Card_Design/2.png" alt="SENTINEL 001 카드 뒷면"><span>Sentinel 카드의 뒷면을 확인하세요</span></div><div class="rank-card"><div class="rank-overlay"><small>SENTINEL BANK · CARD 02 RECORD</small><span>FINAL RANK</span><h2>${rank}</h2><div class="rank-body"><div class="rank-line"><span>판단력</span><b>${stars(judgment)}</b></div><div class="rank-line"><span>보안 대응력</span><b>${stars(defense)}</b></div><div class="rank-line"><span>프라이버시 균형</span><b>${stars(privacy)}</b></div></div><div class="rank-score"><b>${total}</b><span>/ 16 TRUST</span></div></div></div></div>
  <div class="takeaway-card"><small>KEY TAKEAWAYS</small><h3>오늘의 핵심 개념 다시 보기</h3><ol><li><b>FDS</b><span>금액뿐 아니라 시간·위치·기기·행동 패턴을 함께 분석합니다.</span></li><li><b>연합학습</b><span>원본 거래를 이동하지 않고 여러 은행의 학습 결과를 모읍니다.</span></li><li><b>공격 대응</b><span>악성 참여자의 학습 결과는 검증하고 격리해야 합니다.</span></li><li><b>Differential Privacy</b><span>노이즈를 더해 개인의 흔적이 드러날 가능성을 낮춥니다.</span></li><li><b>보안의 균형</b><span>탐지 성능과 개인정보 보호, 대응력을 함께 고려해야 합니다.</span></li></ol></div>
  <div class="stButton"><button type="button" data-restart>새 조사관 맞이하기&nbsp; ↻</button></div>`;
}

function render({ scrollTop = false } = {}) {
  try {
    const screens = { 1: transactionScreen, 2: modelScreen, 3: attackScreen, 4: privacyScreen, 5: resultScreen };
    const overlayMarkup = state.deal ? dealOverlay() : "";
    app.innerHTML = `<div class="screen-enter">${nav()}${state.step === 0 ? landing() : stepper() + screens[state.step]() + footer()}</div>${overlayMarkup}`;
    bindEvents();
    if (scrollTop) window.scrollTo({ top: 0, behavior: "auto" });
    const overlay = document.querySelector(".deal-overlay");
    if (overlay && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.body.classList.add("deal-active");
      const finishDeal = () => {
        overlay.remove();
        document.body.classList.remove("deal-active");
      };
      overlay.addEventListener("animationend", event => {
        if (event.target === overlay) finishDeal();
      });
      window.setTimeout(finishDeal, 2800);
    } else {
      overlay?.remove();
      document.body.classList.remove("deal-active");
    }
  } catch (error) {
    console.error(error);
    app.innerHTML = `<div class="error-boundary">화면을 표시하지 못했습니다. 페이지를 새로고침해 주세요.</div>`;
  }
}

function bindEvents() {
  document.querySelector("[data-enter]")?.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "auto" });
    state.step = 1;
    state.deal = true;
    render();
  });
  document.querySelectorAll("[data-choice]").forEach(button => button.addEventListener("click", () => {
    const key = button.dataset.choice;
    state[key] = button.dataset.value;
    document.querySelectorAll(`[data-choice="${key}"]`).forEach(option => {
      const selected = option.dataset.value === state[key];
      option.setAttribute("kind", selected ? "primary" : "secondary");
      option.textContent = `${selected ? "SELECTED  ·  " : ""}${option.dataset.value}`;
    });
    document.querySelector(`[data-submit="${key}"]`).disabled = false;
  }));
  document.querySelector("[data-submit]")?.addEventListener("click", () => { state.revealed = true; render(); });
  document.querySelector("[data-next]")?.addEventListener("click", () => { state.step += 1; state.revealed = false; render({ scrollTop: true }); });
  document.querySelector("[data-restart]")?.addEventListener("click", () => { Object.assign(state, { step: 0, scenario: Math.floor(Math.random() * scenarios.length), revealed: false, transaction: null, model: null, attack: null, privacy: null, deal: false }); render({ scrollTop: true }); });
}

render();
