import streamlit as st
from ai_tutor import ask_ai, build_messages, get_ai_config
from tutor import explain_topic
from question_bank import QUESTIONS

st.set_page_config(page_title="AI 个性化辅导", page_icon="🤖", layout="wide")
st.title("🤖 AI 个性化辅导")
st.caption("围绕 SQL 知识点、练习题、学生代码和错误反馈进行多轮辅导。")

topics = sorted({q["topic"] for q in QUESTIONS})
with st.sidebar:
    st.subheader("辅导设置")
    topic = st.selectbox("当前知识点", topics)
    st.caption("先选择知识点，再补充题目、SQL 或报错信息。")

cfg = get_ai_config()
if cfg["api_key"]:
    st.success(f"已读取 API 配置｜模型：{cfg['model']}")
else:
    st.warning("当前尚未配置大模型 API。页面仍可查看知识点讲解；配置 API 后即可开启多轮 AI 对话。")

left, right = st.columns(2)
with left:
    task = st.text_area("题目或你想弄懂的问题", height=110, placeholder="例如：统计每个班级的人数，应该怎样写 SQL？")
    student_sql = st.text_area("你的 SQL 代码（可选）", height=130, placeholder="SELECT ...")
with right:
    feedback = st.text_area("执行报错或判题反馈（可选）", height=110, placeholder="例如：结果与要求不一致，或粘贴 SQL 报错。")
    st.markdown("**本知识点基础讲解**")
    st.markdown(explain_topic(topic))

if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []

st.divider()
st.subheader("与知学 AI 对话")
for msg in st.session_state.ai_chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("继续提问，例如：为什么这里要使用 HAVING？")
if prompt:
    st.session_state.ai_chat_history.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        if not cfg["api_key"]:
            answer = "目前还没有配置大模型 API Key，所以暂时无法调用在线模型。你可以先阅读上方知识点讲解。配置完成后，我就能结合你的题目、SQL 和错误反馈进行多轮辅导。"
            st.markdown(answer)
        else:
            context = build_messages(topic, task, student_sql, feedback, st.session_state.ai_chat_history[:-1])
            context.append({"role":"user","content":prompt})
            with st.spinner("知学 AI 正在分析你的问题……"):
                answer, err = ask_ai(context)
            if err:
                answer = "暂时没有成功获得模型回答。\n\n" + err
            st.markdown(answer)
    st.session_state.ai_chat_history.append({"role":"assistant","content":answer})

c1,c2 = st.columns(2)
with c1:
    if st.button("清空本轮对话"):
        st.session_state.ai_chat_history = []
        st.rerun()
with c2:
    st.caption("注意：不要在对话中输入密码、个人隐私或真实业务数据库中的敏感数据。")
