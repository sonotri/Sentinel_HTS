from __future__ import annotations

import base64
import random
from dataclasses import dataclass
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
CARD_DIR = ROOT / "Card_Design"


@dataclass(frozen=True)
class TransactionScenario:
    transaction_id: str
    time: str
    amount: str
    location: str
    ip_risk: str
    device: str
    velocity: str
    merchant: str
    agent_action: str
    fraud_score: int
    reasons: tuple[str, ...]


SCENARIOS = (
    TransactionScenario("TX-2026-0917", "02:14", "2,840,000원", "서울 → 베를린", "0.87 / HIGH", "처음 보는 Android", "10분 이내 7회", "CRYPTO EXCHANGE", "차단", 92, ("심야 해외 거래", "고위험 IP", "신규 기기", "짧은 시간 내 반복 결제")),
    TransactionScenario("TX-2026-2048", "19:42", "186,000원", "서울 → 파리", "0.48 / MEDIUM", "처음 보는 iPhone", "30분 이내 2회", "TRAVEL BOOKING", "추가 인증", 58, ("새로운 해외 위치", "신규 기기", "평소보다 큰 결제 금액")),
    TransactionScenario("TX-2026-3310", "13:05", "42,500원", "서울 → 서울", "0.08 / LOW", "등록된 iPhone", "2시간 이내 1회", "GROCERY", "승인", 7, ("평소 이용 지역", "등록 기기", "일상적인 금액과 업종")),
)

ATTACK_EVENT = {"answer": "Update Scale", "bank": "Bank B"}
PRIVACY = {
    "Low": {"noise": "0.00", "epsilon": "∞", "f1": 0.91, "exposure": "높음", "stars": 2},
    "Balanced": {"noise": "0.05", "epsilon": "8.7", "f1": 0.87, "exposure": "낮음", "stars": 5},
    "High": {"noise": "0.12", "epsilon": "3.1", "f1": 0.76, "exposure": "매우 낮음", "stars": 4},
}


def initialize() -> None:
    defaults = {"step": 0, "scenario_index": random.randrange(len(SCENARIOS)), "transaction_choice": None, "model_choice": None, "attack_choice": None, "privacy_choice": None, "revealed": False, "deal_animation": False}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_styles() -> None:
    # Keep booth styling external so visual adjustments remain independent.
    css = (ROOT / "dashboard" / "booth.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def card_data_uri(filename: str) -> str:
    """Load one of the two physical card faces used by the booth."""
    if filename not in {"1.png", "2.png"}:
        raise ValueError(f"Unknown card face: {filename}")
    encoded = base64.b64encode((CARD_DIR / filename).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def nav() -> None:
    st.markdown("""
    <div class="sentinel-nav">
      <div class="brand"><i class="brand-mark">S</i><span><b>SENTINEL BANK</b><small>MAGICAL SECURITY OFFICE</small></span></div>
    </div>""", unsafe_allow_html=True)


def stepper() -> None:
    labels = ("거래", "모델", "공격", "보호", "결과")
    pills = []
    for index, label in enumerate(labels, start=1):
        state = "active" if st.session_state.step == index else "done" if st.session_state.step > index else ""
        symbol = "✓" if state == "done" else f"0{index}"
        pills.append(f'<div class="step-pill {state}"><i>{symbol}</i><span>{label}</span></div>')
    st.markdown(f'<div class="stepper">{"".join(pills)}</div>', unsafe_allow_html=True)


def section_head(number: str, title: str, description: str) -> None:
    st.markdown(f"""
    <div class="section-head">
      <div class="eyebrow"><span>✦</span> MISSION {number} <span>✦</span></div><h2>{title}</h2><p>{description}</p>
      <div class="ornament"><i></i><b>◆</b><i></i></div>
    </div>""", unsafe_allow_html=True)


def concept(title: str, body: str, extra_class: str = "") -> None:
    st.markdown(f'<div class="concept-card {extra_class}"><div class="concept-sigil">✦</div><div><small>LEDGER NOTE</small><strong>{title}</strong><p>{body}</p></div></div>', unsafe_allow_html=True)


def reveal_button(choice_key: str) -> None:
    if st.button("제출하기  ✦", key=f"submit_{choice_key}", type="primary", disabled=not st.session_state.get(choice_key), use_container_width=True):
        st.session_state.revealed = True
        st.rerun()


def choice_cards(choice_key: str, options: tuple[str, ...], label: str | None = None) -> None:
    """Render choices as a vertical stack of seal-stamped parchment ribbons."""
    if label:
        st.markdown(f'<div class="choice-group-label">{label}</div>', unsafe_allow_html=True)
    for index, option in enumerate(options):
        selected = st.session_state.get(choice_key) == option
        if st.button(
            f"{'SELECTED  ·  ' if selected else ''}{option}",
            key=f"choice_{choice_key}_{index}",
            type="primary" if selected else "secondary",
            use_container_width=True,
        ):
            st.session_state[choice_key] = option
            st.rerun()


def next_button() -> None:
    if st.button("다음 임무로 이동  →", key="next_mission", use_container_width=True):
        st.session_state.step += 1
        st.session_state.revealed = False
        st.rerun()


def landing() -> None:
    card_front = card_data_uri("1.png")
    card_back = card_data_uri("2.png")
    st.markdown(f"""
    <section class="landing-shell">
      <div class="dust dust-a"></div><div class="dust dust-b"></div>
      <i class="corner corner-nw"></i><i class="corner corner-ne"></i><i class="corner corner-sw"></i><i class="corner corner-se"></i>
      <div class="landing-copy">
        <div class="hero-kicker"><span>✦</span> AI SECURITY INITIATION <span>✦</span></div>
        <div class="hero-overline">SENTINEL BANK · SECURITY OFFICE</div>
        <h1>나의 거래는<br><em>안전한가?</em></h1>
        <p>데이터를 공유하지 않고도 금융 위험을 함께 탐지할 수 있을까요?<br>실제 거래 시나리오를 통해 연합 FDS의 판단과 대응 과정을 확인해보세요.</p>
      </div>
      <div class="card-stage" aria-label="SENTINEL 001 카드 앞면과 뒷면 미리보기">
        <div class="vault-door"><i></i><i></i><i></i><i></i><b>S</b></div><div class="vault-halo"></div>
        <i class="spark spark-one">✦</i><i class="spark spark-two">✧</i><i class="spark spark-three">✦</i><div class="card-shadow"></div>
        <div class="card-face-preview card-back"><img src="{card_back}" alt="SENTINEL 001 카드 뒷면"><span>BACK · MISSION RECORD</span></div>
        <div class="card-face-preview card-front"><img src="{card_front}" alt="SENTINEL 001 카드 앞면"><span>FRONT · IDENTITY</span></div>
      </div>
    </section>""", unsafe_allow_html=True)
    if st.button("Sentinel 카드 발급 · Cyber 보안국 입장  ✦", key="enter_security_office", type="primary", use_container_width=True):
        st.session_state.step = 1
        st.session_state.deal_animation = True
        st.rerun()


def card_deal_animation() -> None:
    if not st.session_state.get("deal_animation"):
        return
    card_front = card_data_uri("1.png")
    card_back = card_data_uri("2.png")
    st.markdown(f"""
    <div class="deal-overlay" aria-hidden="true">
      <div class="deal-rays"></div>
      <div class="deal-copy"><small>SENTINEL 001 · ISSUED</small><b>조사관 카드가 지급되었습니다</b></div>
      <div class="issued-card"><div class="issued-card-inner">
        <img class="issued-face issued-front" src="{card_front}" alt="SENTINEL 카드 앞면">
        <img class="issued-face issued-back" src="{card_back}" alt="SENTINEL 카드 뒷면">
      </div></div>
      <div class="deal-particles">✦　·　✧　·　✦　·　✧　·　✦</div>
    </div>""", unsafe_allow_html=True)
    st.session_state.deal_animation = False


def transaction_step() -> None:
    scenario = SCENARIOS[st.session_state.scenario_index]
    card_deal_animation()
    section_head("01", "이 거래를 승인하시겠습니까?", "거래 원장의 단서를 읽고 은행이 취해야 할 조치를 결정하세요.")
    concept("이상거래탐지시스템(Fraud Detection System, FDS)", "FDS는 거래 내역, 고객 정보, 평소 거래 패턴 등을 분석해서 의심되는 이상 거래를 탐지하고 차단하는 기술입니다.")
    st.markdown(f"""
    <div class="transaction-card">
      <div class="ledger-ribbon"><span>TRANSACTION LEDGER</span><b>{scenario.transaction_id}</b></div>
      <div class="amount-hero"><small>{scenario.merchant}</small><b>{scenario.amount}</b><span>결제 승인 요청</span></div>
      <div class="transaction-grid">
        <div class="datum"><span>거래 시간</span><b>{scenario.time}</b></div><div class="datum"><span>접속 위치</span><b>{scenario.location}</b></div>
        <div class="datum"><span>접속 IP</span><b>{scenario.ip_risk}</b></div><div class="datum"><span>사용 기기</span><b>{scenario.device}</b></div>
        <div class="datum wide"><span>거래 속도</span><b>{scenario.velocity}</b></div>
      </div><div class="ledger-stamp">REVIEW</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="question"><small>YOUR DECISION</small><b>거래 징후를 검토한 후 조치를 선택하세요.</b></div>', unsafe_allow_html=True)
    if not st.session_state.revealed:
        choice_cards("transaction_choice", ("1. 승인", "2. 추가 인증", "3. 차단"))
        reveal_button("transaction_choice")
        return
    matched = st.session_state.transaction_choice == scenario.agent_action
    reasons = "".join(f'<span>{reason}</span>' for reason in scenario.reasons)
    st.markdown(f"""
    <div class="result-card {'success' if matched else 'danger'}">
      <div class="result-seal">{'✓' if matched else '!'}</div><div class="eyebrow">SENTINEL ANALYSIS · FRAUD SCORE {scenario.fraud_score}%</div>
      <h3>AI 권고 · {scenario.agent_action}</h3><p>당신의 판단은 <b>{st.session_state.transaction_choice}</b>입니다. {'AI의 권고와 일치합니다.' if matched else 'AI의 권고와 다른 선택입니다.'}</p>
      <div class="reason-list">{reasons}</div>
    </div>""", unsafe_allow_html=True)
    with st.expander("왜 이런 판단을 내렸나요?"):
        st.write("Fraud Score는 여러 위험 신호를 결합한 확률 점수입니다. 점수만으로 결론을 내리지 않고 거래 맥락과 고객 피해 가능성에 맞는 조치를 선택해야 합니다.")
    next_button()


def model_step() -> None:
    section_head("02", "어떤 학습 방법이 적합할까요?", "세 은행의 협업 조건을 확인하고 가장 적합한 학습 방식을 선택하세요.")
    concept("세 가지 학습 방식", """
      <span class="model-method"><b>Local-only</b><em>한 은행 내부의 거래 데이터만으로 학습합니다.</em></span>
      <span class="model-method"><b>Federated</b><em>원본 거래 데이터는 각 은행에 보관하고, 각 은행의 학습 결과만 안전하게 취합해 공동 모델을 개선합니다.</em></span>
      <span class="model-method"><b>Centralized</b><em>모든 은행의 원본 데이터를 한곳에 모아 하나의 모델을 학습합니다.</em></span>
    """)
    st.markdown("""
    <div class="model-scenario">
    <p>세 은행이 공동 FDS를 구축하려 합니다</p>
      <p>은행마다 서로 다른 사기 패턴을 보유하고 있지만 고객의 원본 거래 데이터는 외부로 반출할 수 없습니다.</p>
      <div><span>원본 데이터 반출 금지</span><span>세 은행의 패턴 공동 활용</span><span>개인정보 노출 최소화</span></div>
    </div>
    <div class="bank-network">
      <div class="bank-row">
        <div class="bank-node"><div class="bank-building"><i>A</i><span></span></div><b>BANK A</b><small>원본 거래 보관</small></div>
        <div class="bank-node"><div class="bank-building"><i>B</i><span></span></div><b>BANK B</b><small>원본 거래 보관</small></div>
        <div class="bank-node"><div class="bank-building"><i>C</i><span></span></div><b>BANK C</b><small>원본 거래 보관</small></div>
      </div>
      <div class="network-search"><span></span><b>SEARCHING FOR THE RIGHT CONNECTION</b><span></span></div>
    </div>""", unsafe_allow_html=True)
    if not st.session_state.revealed:
        choice_cards("model_choice", ("1. Local-only", "2. Federated", "3. Centralized"), "탐지 모델")
        reveal_button("model_choice")
        return
    correct = st.session_state.model_choice == "Federated"
    comparison = "".join(
        f'<div class="model-fit-row {"best" if model == "Federated" else ""}"><span><b>{model}</b><em>— {reason}</em></span><small>{verdict}</small></div>'
        for model, reason, verdict in (
            ("Local-only", "공동 패턴 활용 불가", "조건 불충족"),
            ("Federated", "원본 반출 없이 공동 학습", "권장"),
            ("Centralized", "원본 데이터 집중 위험", "조건 불충족"),
        )
    )
    st.markdown(f'<div class="result-card {"success" if correct else "danger"}"><div class="result-seal">{"✓" if correct else "!"}</div><div class="eyebrow">SCENARIO RECOMMENDATION</div><h3>권장 방식 · Federated</h3><p>당신의 선택은 <b>{st.session_state.model_choice}</b>입니다. 원본 반출 없이 세 은행의 패턴을 함께 활용하려면 Federated가 가장 적합합니다.</p><div class="model-fit-list">{comparison}</div></div>', unsafe_allow_html=True)
    with st.expander("Federated가 왜 유리한가요?"):
        st.write("한 은행에서는 드문 공격이 다른 은행에서는 관측될 수 있습니다. 연합학습은 원본 거래를 중앙에 모으지 않으면서 이런 패턴을 공동으로 학습합니다. Centralized는 성능 상한을 보여주지만 원본 집중에 따른 개인정보 위험이 큽니다.")
    next_button()


def attack_step() -> None:
    section_head("03", "공동 모델에 무슨 일이 생겼을까요?", "비정상 업데이트의 흔적을 보고 공격 유형을 추리하세요.")
    concept("세 가지 공격 유형", """
      <span class="attack-method"><b>Label Flip</b><em>정상과 사기 라벨을 뒤집어 모델이 잘못된 패턴을 학습하게 합니다.</em></span>
      <span class="attack-method"><b>Update Scale</b><em>한 참여자의 학습 결과를 비정상적으로 증폭해 공동 모델을 흔듭니다.</em></span>
      <span class="attack-method"><b>Gradient Leakage</b><em>공유된 학습 정보에서 원본 데이터의 특성이나 민감 정보를 추정합니다.</em></span>
    """, "attack-concept")
    st.markdown("""
    <div class="attack-ledger">
      <div class="alert-sigil">!</div><div><small>FEDERATED ROUND 04</small><b>비정상 업데이트 감지</b><span>Bank B · 보안 격리 검토 필요</span></div>
      <div class="attack-metric"><span>업데이트 크기</span><b>× 12.4</b><small>평균 대비</small></div><div class="attack-metric"><span>사기 탐지 점수</span><b>92 → 34</b><small>급격한 하락</small></div><div class="attack-metric"><span>공동 모델 F1</span><b>0.88 → 0.49</b><small>성능 훼손</small></div>
    </div>""", unsafe_allow_html=True)
    if not st.session_state.revealed:
        choice_cards("attack_choice", ("1. Label Flip", "2. Update Scale", "3. Gradient Leakage"), "공격 유형")
        reveal_button("attack_choice")
        return
    correct = st.session_state.attack_choice == ATTACK_EVENT["answer"]
    st.markdown(f"""
    <div class="result-card attack-result {'success' if correct else 'danger'}">
      <div class="result-seal">{'✓' if correct else '!'}</div><div class="eyebrow">ATTACK IDENTIFIED</div><h3>정답 · Update Scale</h3>
      <p>Bank B가 정상 범위를 벗어난 크기로 모델 업데이트를 증폭했습니다. 하나의 악성 업데이트만으로도 글로벌 모델이 크게 흔들릴 수 있습니다.</p>
      <div class="agent-action"><small>SECURITY AGENT RESPONSE</small><b>업데이트 격리 → Bank B 임시 제외 → 정상 참여자 재집계 → 재검증 요청</b></div>
    </div>""", unsafe_allow_html=True)
    with st.expander("다른 공격은 어떻게 다른가요?"):
        st.markdown("**Label Flip**은 사기/정상 라벨을 뒤집어 학습을 오염시킵니다. **Gradient Leakage**는 공유된 기울기에서 입력 특성이나 라벨을 추정하는 개인정보 공격입니다.")
    next_button()


def privacy_step() -> None:
    section_head("04", "얼마나 강하게 보호하시겠습니까?", "탐지 성능과 개인정보 보호 사이에서 은행의 정책을 결정하세요.")
    concept("Differential Privacy", "학습 정보에 통계적 노이즈를 더해 특정 개인의 데이터가 결과에 드러날 가능성을 낮추는 기술입니다. 노이즈가 커질수록 보호는 강해지지만 탐지 성능은 낮아질 수 있습니다.", "privacy-concept")
    st.markdown('''
    <div class="privacy-scale">
      <div class="scale-copy"><small>MODEL UTILITY</small><b>탐지 성능</b></div>
      <div class="balance-scale" aria-label="탐지 성능과 개인정보 보호의 균형">
        <div class="balance-stand"><i></i><span></span></div>
        <div class="balance-beam">
          <div class="balance-pan pan-left"><i></i><span></span></div><b>◆</b><div class="balance-pan pan-right"><i></i><span></span></div>
        </div>
      </div>
      <div class="scale-copy"><small>DATA SHIELD</small><b>개인정보 보호</b></div>
    </div>''', unsafe_allow_html=True)
    if not st.session_state.revealed:
        choice_cards("privacy_choice", ("1. Low", "2. Balanced", "3. High"), "보호 수준")
        reveal_button("privacy_choice")
        return
    choice = st.session_state.privacy_choice
    result = PRIVACY[choice]
    st.markdown(f"""
    <div class="result-card success"><div class="result-seal">ε</div><div class="eyebrow">PRIVACY POLICY · {choice.upper()}</div><h3>선택한 보호 수준을 적용합니다.</h3>
      <div class="score-row"><div class="score-chip"><span>DP 노이즈</span><b>{result['noise']}</b><small>NOISE</small></div><div class="score-chip"><span>탐지 성능</span><b>{result['f1']:.2f}</b><small>F1 SCORE</small></div><div class="score-chip best"><span>정보 노출</span><b>{result['exposure']}</b><small>EXPOSURE</small></div></div>
    </div>""", unsafe_allow_html=True)
    with st.expander("보호 수준은 높을수록 좋은가요?"):
        st.write("항상 그렇지는 않습니다. High는 정보 노출을 강하게 줄이지만 실제 사기 패턴까지 흐릴 수 있습니다. 위험 수준과 규제 요구사항을 만족하면서 필요한 탐지력을 유지하는 균형이 중요합니다.")
    next_button()


def stars(count: int) -> str:
    return "✦" * count + "✧" * (5 - count)


def result_step() -> None:
    scenario = SCENARIOS[st.session_state.scenario_index]
    judgment = 5 if st.session_state.transaction_choice == scenario.agent_action else 3
    defense = 5 if st.session_state.attack_choice == ATTACK_EVENT["answer"] else 3
    privacy = PRIVACY[st.session_state.privacy_choice]["stars"]
    model_bonus = 1 if st.session_state.model_choice == "Federated" else 0
    total = judgment + defense + privacy + model_bonus
    rank = "SENTINEL ARCHITECT" if total >= 15 else "SECURITY ANALYST" if total >= 12 else "RISK INVESTIGATOR"
    card_back = card_data_uri("2.png")
    section_head("05", "보안 조사관 최종 기록", "판단력, 방어력, 프라이버시 균형을 종합한 당신의 인증 결과입니다.")
    st.markdown(f"""
    <div class="result-showcase">
      <div class="completed-card"><img src="{card_back}" alt="SENTINEL 001 카드 뒷면"><span>Sentinel 카드의 뒷면을 확인하세요</span></div>
      <div class="rank-card"><div class="rank-overlay">
        <small>SENTINEL BANK · CARD 02 RECORD</small><span>FINAL RANK</span><h2>{rank}</h2>
        <div class="rank-body"><div class="rank-line"><span>판단력</span><b>{stars(judgment)}</b></div><div class="rank-line"><span>보안 대응력</span><b>{stars(defense)}</b></div><div class="rank-line"><span>프라이버시 균형</span><b>{stars(privacy)}</b></div></div>
        <div class="rank-score"><b>{total}</b><span>/ 16 TRUST</span></div>
      </div></div>
    </div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class="takeaway-card"><small>KEY TAKEAWAYS</small><h3>오늘의 핵심 개념 다시 보기</h3><ol>
      <li><b>FDS</b><span>금액뿐 아니라 시간·위치·기기·행동 패턴을 함께 분석합니다.</span></li>
      <li><b>연합학습</b><span>원본 거래를 이동하지 않고 여러 은행의 학습 결과를 모읍니다.</span></li>
      <li><b>공격 대응</b><span>악성 참여자의 학습 결과는 검증하고 격리해야 합니다.</span></li>
      <li><b>Differential Privacy</b><span>노이즈를 더해 개인의 흔적이 드러날 가능성을 낮춥니다.</span></li>
      <li><b>보안의 균형</b><span>탐지 성능과 개인정보 보호, 대응력을 함께 고려해야 합니다.</span></li>
    </ol></div>""", unsafe_allow_html=True)
    if st.button("새 조사관 맞이하기  ↻", type="primary", use_container_width=True):
        for key in tuple(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Sentinel Bank · 나의 거래는 안전한가?", page_icon="✦", layout="centered")
    initialize()
    load_styles()
    nav()
    if st.session_state.step == 0:
        landing()
        return
    stepper()
    {1: transaction_step, 2: model_step, 3: attack_step, 4: privacy_step, 5: result_step}[st.session_state.step]()
    st.markdown('<div class="operator-note">SENTINEL BANK · PRIVACY-PRESERVING FEDERATED FRAUD DETECTION</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
