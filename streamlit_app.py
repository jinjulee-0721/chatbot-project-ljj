import os
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="리더십 코칭 AI", layout="centered")

st.title("🏆 리더십 코칭 AI")

# Get API key from Streamlit secrets or environment
OPENAI_API_KEY = None
if "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 설정되어 있지 않습니다. `.streamlit/secrets.toml` 에 `OPENAI_API_KEY` 를 추가해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 한국어로 답변하는 친절한 리더십 코칭 AI입니다. 현실적이고 실행 가능한 조언, 우선순위, 예시 행동을 제공하세요."}
    ]

def extract_response(resp):
    # Try several access patterns for different client versions
    try:
        return resp.choices[0].message["content"]
    except Exception:
        pass
    try:
        return resp.choices[0].message.content
    except Exception:
        pass
    try:
        return resp.choices[0].text
    except Exception:
        return str(resp)

def call_openai_chat(messages):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=800,
            temperature=0.6,
        )
        return extract_response(resp)
    except Exception as e:
        st.error(f"OpenAI 호출 중 오류가 발생했습니다: {e}")
        return "죄송합니다. 응답을 가져오지 못했습니다."

st.sidebar.header("리더의 고민")
choice = st.sidebar.radio("당면한 고민을 선택하세요:", ("사람관리", "조직관리"))

# Track whether context was submitted for flow control (특히 사람관리)
if 'context_submitted' not in st.session_state:
    st.session_state['context_submitted'] = None
if 'last_choice' not in st.session_state:
    st.session_state['last_choice'] = None

# Reset context when user switches between 사람관리/조직관리
if st.session_state.get('last_choice') != choice:
    st.session_state['context_submitted'] = None
    st.session_state['last_choice'] = choice
    # keep only system message when switching context
    st.session_state['messages'] = [m for m in st.session_state['messages'] if m['role'] == 'system']
    # Clear form widget state for both 사람관리 and 조직관리 to avoid leftover inputs
    for _k in [
        'p_role', 'p_age', 'p_work', 'p_concerns', 'p_motivation', 'p_team_relation', 'p_priority_goals',
        'o_size', 'o_tenure', 'o_goal', 'o_concerns'
    ]:
        if _k in st.session_state:
            st.session_state.pop(_k)

with st.form(key="context_form"):
    if choice == "사람관리":
        st.subheader("당신의 구성원은 어떤 사람인가요?")
        role = st.selectbox("구성원의 직급", ["사원", "대리", "과장", "차장", "부장"], key='p_role')
        age = st.number_input("구성원의 연령", min_value=15, max_value=100, step=1, key='p_age')
        work = st.text_input("구성원의 주요 업무", key='p_work')
        concerns = st.text_area("고민사항 (구체적으로 적어주세요)", key='p_concerns')
        # 추가 개인화 필드
        motivation = st.selectbox(
            "구성원의 동기/성향",
            [
                "목표지향(성과 중심)",
                "관계중시(협력 중심)",
                "안정지향(현상 유지)",
                "학습지향(성장 중심)",
                "기타/모름",
            ],
            key='p_motivation'
        )
        team_relation = st.selectbox(
            "팀 내 관계 상태",
            ["협업 양호", "일부 갈등 있음", "심한 갈등 있음", "관계 파악 필요"],
            key='p_team_relation'
        )
        priority_goals = st.multiselect(
            "우선 해결 목표 (중복 선택 가능)",
            ["성과 개선", "관계 개선", "역량 개발", "프로세스 개선", "기타"],
            key='p_priority_goals'
        )
    else:
        st.subheader("당신의 조직은 어떤가요?")
        size = st.selectbox(
            "조직 구성원 수",
            ["1명", "2~3명", "4~5명", "5~10명", "10명 이상"],
            key='o_size'
        )
        tenure = st.selectbox(
            "현재 팀장직책을 맡은 기간",
            [
                "6개월 미만",
                "6개월 이상~1년 미만",
                "1년 이상~3년 미만",
                "3년 이상~5년 미만",
                "5년 이상~10년 미만",
                "10년 이상",
            ],
            key='o_tenure'
        )
        goal = st.selectbox(
            "조직의 목표 (범주로 선택하세요)",
            ["성장/확장", "생산성/효율", "문화/협업", "프로세스 개선", "고객만족", "기타"],
            key='o_goal'
        )
        concerns = st.text_area("고민사항 (구체적으로 적어주세요)", key='o_concerns')

    submit = st.form_submit_button("상황 제출하고 코칭 받기")

if submit:
    if choice == "사람관리":
        user_content = (
            f"[사람관리]\n구성원의 직급: {role}\n"
            f"구성원의 연령: {age}\n"
            f"구성원의 업무: {work}\n"
            f"고민사항: {concerns}\n"
            f"구성원의 동기/성향: {motivation}\n"
            f"팀 내 관계 상태: {team_relation}\n"
            f"우선 해결 목표: {', '.join(priority_goals) if priority_goals else '없음'}\n"
        )
    else:
        user_content = (
            f"[조직관리]\n조직 구성원 수: {size}\n"
            f"팀장직책 기간: {tenure}\n"
            f"조직의 목표: {goal}\n"
            f"고민사항: {concerns}\n"
        )
    # mark that context was submitted (사람관리의 경우 이후에 채팅창을 활성화함)
    st.session_state['context_submitted'] = choice
    st.session_state.messages.append({"role": "user", "content": user_content})
    with st.chat_message("user"):
        st.markdown(user_content)

    with st.chat_message("assistant"):
        assistant_reply = call_openai_chat(st.session_state.messages)
        st.markdown(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# Chat input for follow-up questions
# Show chat history and follow-up input only after 해당 유형의 정보가 제출된 경우
show_chat = True
# If the submitted context does not match the current choice, hide chat
if st.session_state.get('context_submitted') != choice:
    show_chat = False

if show_chat:
    st.markdown("---")
    st.header("대화하기")
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"]) 
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"]) 

    if user_input := st.chat_input("추가로 궁금한 점을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            reply = call_openai_chat(st.session_state.messages)
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
