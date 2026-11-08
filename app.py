import streamlit as st
import pandas as pd
import plotly.express as px
from database import (
    init_db, save_attempt, get_history, get_student_summary,
    record_wrong_answers, get_wrong_answers, mark_wrong_resolved,
    save_practice_record, get_practice_history
)
from question_bank import QUESTIONS
from tutor import explain_topic, make_study_plan
from learning_analytics import get_mastery_stats, build_learning_path, build_ai_study_prompt

st.set_page_config(page_title="知学 AI", page_icon="🎓", layout="wide")
init_db()

TOPICS = sorted({q["topic"] for q in QUESTIONS})
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1180px;}
.hero {padding: 1.4rem 1.6rem; border-radius: 16px; background: linear-gradient(110deg,#eaf2ff,#f1edff);}
.hero h1 {margin:0;color:#183153;}
.small-muted {color:#64748b;font-size:0.92rem;}
</style>
""", unsafe_allow_html=True)

if "student" not in st.session_state:
    st.session_state.student = ""

with st.sidebar:
    st.title("🎓 知学 AI")
    st.caption("大学生知识诊断与个性化辅导智能体")
    name = st.text_input("学生姓名/演示昵称", value=st.session_state.student, placeholder="请输入演示昵称")
    if st.button("进入学习空间", use_container_width=True):
        if name.strip():
            st.session_state.student = name.strip()
            st.rerun()
        else:
            st.warning("请先输入昵称。")
    st.divider()
    page = st.radio("功能导航", [
        "学习首页", "知识诊断", "个性化辅导", "专项练习",
        "学习报告", "学习画像与错题本"
    ])

student = st.session_state.student
if not student:
    st.markdown('<div class="hero"><h1>知学 AI</h1><p>从一次测试开始，发现知识漏洞，获得针对性辅导，让学习更有方向。</p></div>', unsafe_allow_html=True)
    st.info("请在左侧输入演示昵称并点击“进入学习空间”。")
    st.subheader("项目核心流程")
    cols = st.columns(5)
    for c, (n, d) in zip(cols, [("01 测试","完成课程测评"),("02 诊断","定位薄弱知识点"),("03 辅导","获取针对性讲解"),("04 练习","巩固相关知识"),("05 反馈","查看学习变化")]):
        c.metric(n, d)
    st.stop()

st.title(f"你好，{student} 👋")
st.caption("课程：数据库原理与 SQL｜当前版本：第四阶段升级版")

if page == "学习首页":
    st.markdown('<div class="hero"><h1>让每一次练习，都更有针对性</h1><p>知学 AI 根据答题记录识别薄弱知识点，并推荐解释与练习。</p></div>', unsafe_allow_html=True)
    summary = get_student_summary(student)
    a,b,c = st.columns(3)
    a.metric("累计测评次数", summary["attempts"])
    b.metric("累计答题数", summary["answered"])
    c.metric("平均正确率", f'{summary["accuracy"]:.1f}%')
    st.subheader("学习路径")
    st.write("**知识测试 → 能力诊断 → 个性化讲解 → 专项练习 → 学习画像 → 再测**")
    st.info("建议第一次使用先进入“知识诊断”，完成一套测评，系统才能生成个人薄弱点分析。")
    st.subheader("本项目覆盖的知识点")
    st.write("、".join(TOPICS))
    stats = get_mastery_stats(student)
    if stats:
        st.subheader("最近累计掌握情况")
        st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

elif page == "知识诊断":
    st.header("知识诊断测评")
    st.write("请独立完成以下题目。提交后，系统将按知识点统计正确率，并自动收录答错题目。")
    with st.form("diagnostic_form"):
        answers = {}
        for i, q in enumerate(QUESTIONS):
            st.markdown(f"**{i+1}. {q['question']}**")
            answers[q["id"]] = st.radio("选择答案", q["options"], key=f"diag_{q['id']}", index=None, label_visibility="collapsed")
            st.caption(f"知识点：{q['topic']}｜题型：{q['type']}")
        submitted = st.form_submit_button("提交测评并生成诊断", type="primary", use_container_width=True)
    if submitted:
        unanswered = [q for q in QUESTIONS if not answers[q["id"]]]
        if unanswered:
            st.error(f"还有 {len(unanswered)} 道题未作答，请完成后提交。")
        else:
            correct = sum(answers[q["id"]] == q["answer"] for q in QUESTIONS)
            topic_stats = {}
            for q in QUESTIONS:
                t = q["topic"]
                topic_stats.setdefault(t, {"correct":0,"total":0})
                topic_stats[t]["total"] += 1
                topic_stats[t]["correct"] += int(answers[q["id"]] == q["answer"])
            save_attempt(student, correct, len(QUESTIONS), topic_stats)
            wrong_count = record_wrong_answers(student, QUESTIONS, answers)
            st.session_state.last_answers = answers
            st.session_state.last_stats = topic_stats
            st.session_state.last_correct = correct
            st.success(f"测评完成！答对 {correct}/{len(QUESTIONS)} 题，正确率 {correct/len(QUESTIONS)*100:.1f}%。")
            st.info(f"本次已将 {wrong_count} 道错题加入个人错题本。")
            st.subheader("知识点诊断结果")
            rows = [{"知识点":t,"正确题数":v["correct"],"题目数":v["total"],"正确率":v["correct"]/v["total"]*100} for t,v in topic_stats.items()]
            df = pd.DataFrame(rows).sort_values("正确率")
            st.dataframe(df.style.format({"正确率":"{:.1f}%"}), use_container_width=True, hide_index=True)
            weak = df[df["正确率"] < 70]["知识点"].tolist()
            if weak:
                st.warning("建议优先巩固：" + "、".join(weak))
            else:
                st.success("本次测评各知识点均达到 70%，可以尝试进阶练习。")
            with st.expander("查看逐题解析"):
                for q in QUESTIONS:
                    ok = answers[q["id"]] == q["answer"]
                    st.markdown(f"**{q['id']}. {'✅' if ok else '❌'} {q['question']}**")
                    st.write(f"你的答案：{answers[q['id']]}｜正确答案：{q['answer']}")
                    st.write(q["explanation"])

elif page in ["个性化辅导", "专项练习"]:
    st.header(page)
    selected_topic = st.selectbox("选择需要学习的知识点", TOPICS)
    if page == "个性化辅导":
        st.subheader("知识点讲解")
        st.markdown(explain_topic(selected_topic))
        st.info("可进入左侧“2_AI个性化辅导”页面使用已配置的大模型进行多轮讲解。")
    else:
        qs = [q for q in QUESTIONS if q["topic"] == selected_topic]
        with st.form("practice_form"):
            answers = {}
            for q in qs:
                st.markdown(f"**{q['question']}**")
                answers[q["id"]] = st.radio("选择答案", q["options"], key=f"prac_{q['id']}", index=None, label_visibility="collapsed")
            go = st.form_submit_button("提交专项练习", type="primary")
        if go:
            if any(not v for v in answers.values()):
                st.error("请完成全部题目。")
            else:
                score = sum(answers[q["id"]] == q["answer"] for q in qs)
                save_practice_record(student, selected_topic, score, len(qs))
                wrong_count = record_wrong_answers(student, qs, answers)
                st.success(f"专项练习：{score}/{len(qs)}，正确率 {score/len(qs)*100:.1f}%")
                st.info(f"本次新增 {wrong_count} 道错题；练习成绩已保存到学习记录。")
                for q in qs:
                    st.write(("✅ " if answers[q["id"]]==q["answer"] else "❌ ") + q["question"])
                    if answers[q["id"]] != q["answer"]:
                        st.caption("解析：" + q["explanation"])

elif page == "学习报告":
    st.header("个人学习报告")
    history = get_history(student)
    practice_history = get_practice_history(student)
    if not history and not practice_history:
        st.info("暂无学习记录。请先完成一次知识诊断或专项练习。")
    else:
        if history:
            df = pd.DataFrame(history)
            df["测评时间"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            latest = df.iloc[0]
            a,b,c = st.columns(3)
            a.metric("最近一次正确率", f'{latest["accuracy"]:.1f}%')
            b.metric("首次测评正确率", f'{float(df.iloc[-1]["accuracy"]):.1f}%')
            c.metric("累计测评次数", len(df))
            chart = px.line(df.sort_values("created_at"), x="created_at", y="accuracy", markers=True,
                            title="测评正确率变化", labels={"created_at":"测评时间","accuracy":"正确率（%）"})
            st.plotly_chart(chart, use_container_width=True)
            st.subheader("测评记录")
            st.dataframe(df[["测评时间","score","total","accuracy"]].rename(columns={"score":"答对题数","total":"总题数","accuracy":"正确率（%）"}), use_container_width=True, hide_index=True)
        if practice_history:
            st.subheader("专项练习记录")
            pdf = pd.DataFrame(practice_history)
            pdf["练习时间"] = pd.to_datetime(pdf["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(pdf[["练习时间","topic","score","total","accuracy"]].rename(
                columns={"topic":"知识点","score":"答对题数","total":"总题数","accuracy":"正确率（%）"}
            ), use_container_width=True, hide_index=True)
        st.subheader("下一步学习建议")
        latest_accuracy = float(history[0]["accuracy"]) if history else 0
        st.markdown(make_study_plan(latest_accuracy))

elif page == "学习画像与错题本":
    st.header("📊 学习画像与智能错题本")
    st.caption("基于本地学习记录统计；样本较少时，掌握度仅供参考。")
    stats = get_mastery_stats(student)
    wrongs = get_wrong_answers(student)
    unresolved = [w for w in wrongs if not w["resolved"]]
    a,b,c = st.columns(3)
    a.metric("知识点数量", len(stats))
    b.metric("待复习错题", len(unresolved))
    c.metric("累计错题记录", len(wrongs))
    if stats:
        sdf = pd.DataFrame(stats)
        st.subheader("知识点掌握度")
        st.dataframe(sdf, use_container_width=True, hide_index=True)
        chart = px.bar(sdf.sort_values("掌握度"), x="知识点", y="掌握度",
                       range_y=[0,100], title="各知识点累计掌握度",
                       labels={"掌握度":"正确率（%）","知识点":"SQL 知识点"})
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("还没有足够的诊断记录。请先完成“知识诊断”测评。")
    st.subheader("动态学习路径")
    for i, item in enumerate(build_learning_path(student), 1):
        st.write(f"{i}. {item}")
    st.divider()
    st.subheader("智能错题本")
    if not wrongs:
        st.info("当前没有错题记录。完成诊断或专项练习后，系统会自动收录答错题目。")
    else:
        filter_mode = st.radio("错题筛选", ["待复习", "全部错题", "已掌握"], horizontal=True)
        selected = [w for w in wrongs if (
            filter_mode == "全部错题" or
            (filter_mode == "待复习" and not w["resolved"]) or
            (filter_mode == "已掌握" and w["resolved"])
        )]
        for w in selected:
            with st.expander(f"{'✅' if w['resolved'] else '📌'} {w['topic']}｜{w['question']}"):
                st.write(f"你的答案：{w['user_answer'] or '未作答'}")
                st.write(f"正确答案：{w['correct_answer']}")
                st.write("解析：" + (w["explanation"] or "暂无解析"))
                st.caption("记录时间：" + w["created_at"])
                if not w["resolved"]:
                    if st.button("标记为已掌握", key=f"resolve_{w['id']}"):
                        mark_wrong_resolved(student, w["id"])
                        st.success("已更新错题状态。")
                        st.rerun()
    st.divider()
    st.subheader("AI 个性化学习建议")
    prompt = build_ai_study_prompt(student)
    try:
        from ai_tutor import ask_ai, get_ai_config
        cfg = get_ai_config()
        if cfg.get("api_key"):
            if st.button("根据我的学习数据生成 AI 建议", type="primary"):
                with st.spinner("AI 正在结合你的学习记录生成建议……"):
                    answer, error = ask_ai([{"role":"user","content":prompt}])
                if error:
                    st.warning("AI 暂时不可用：" + str(error))
                elif answer:
                    st.markdown(answer)
        else:
            st.info("尚未读取到大模型 API 配置。下方提供基于规则的学习建议；配置完成后可生成 AI 建议。")
    except Exception:
        st.info("当前未检测到 AI 辅导模块，暂时使用规则化学习建议。")
    for item in build_learning_path(student):
        st.markdown("- " + item)
