import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SQL 实战训练", page_icon="🧪", layout="wide")
st.title("🧪 SQL 实战训练与自动判题")
st.caption("在隔离的临时 SQLite 数据库中练习 SELECT 查询；每次运行都会重新创建演示数据。")

def build_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("""CREATE TABLE student (
        id INTEGER PRIMARY KEY, name TEXT, gender TEXT, class TEXT,
        age INTEGER, score REAL
    )""")
    conn.executemany("INSERT INTO student VALUES (?,?,?,?,?,?)", [
        (1,"张三","男","数据1班",19,88),
        (2,"李四","女","数据1班",20,92),
        (3,"王五","男","数据2班",18,76),
        (4,"赵六","女","数据2班",21,85),
        (5,"钱七","男","数据1班",19,59),
        (6,"孙八","女","数据2班",20,95),
    ])
    conn.execute("""CREATE TABLE course (
        course_id INTEGER PRIMARY KEY, course_name TEXT, credit REAL
    )""")
    conn.executemany("INSERT INTO course VALUES (?,?,?)", [
        (1,"数据库原理",3.0),(2,"Python程序设计",3.5),(3,"数据结构",4.0)
    ])
    return conn

TASKS = {
"基础查询": {
    "title":"查询所有学生的姓名和成绩",
    "description":"从 student 表中查询 name、score 两列。",
    "hint":"SELECT name, score FROM student;",
    "check": lambda df: set(map(tuple, df.astype(str).values.tolist())) == set([
        ("张三","88.0"),("李四","92.0"),("王五","76.0"),
        ("赵六","85.0"),("钱七","59.0"),("孙八","95.0")
    ]) or (list(df.columns)==["name","score"] and len(df)==6)
},
"条件筛选": {
    "title":"查询成绩大于等于 85 分的学生",
    "description":"从 student 表查询符合条件的学生姓名和成绩。",
    "hint":"WHERE score >= 85",
    "check": lambda df: list(df.columns)==["name","score"] and set(df["name"])=={"张三","李四","赵六","孙八"}
},
"排序": {
    "title":"按成绩从高到低查询学生",
    "description":"查询姓名和成绩，并按 score 降序排列。",
    "hint":"ORDER BY score DESC",
    "check": lambda df: list(df.columns)==["name","score"] and df["score"].tolist()==sorted(df["score"].tolist(), reverse=True)
},
"聚合函数": {
    "title":"计算所有学生的平均成绩",
    "description":"结果只返回一个名为 avg_score 的平均分字段。",
    "hint":"AVG(score) AS avg_score",
    "check": lambda df: len(df)==1 and "avg_score" in df.columns and abs(float(df.iloc[0]["avg_score"])-82.5)<0.01
},
"分组查询": {
    "title":"统计每个班级的学生人数",
    "description":"结果包含 class 和人数两列，人数列命名为 student_count。",
    "hint":"GROUP BY class，COUNT(*) AS student_count",
    "check": lambda df: list(df.columns)==["class","student_count"] and dict(zip(df["class"],df["student_count"]))=={"数据1班":3,"数据2班":3}
}
}

with st.sidebar:
    st.subheader("训练任务")
    category = st.radio("选择知识点", list(TASKS.keys()))
    st.divider()
    st.markdown("**可用数据表**")
    st.code("student(id, name, gender, class, age, score)\ncourse(course_id, course_name, credit)", language="text")

task=TASKS[category]
st.subheader(task["title"])
st.write(task["description"])
with st.expander("查看表结构和样例数据"):
    conn=build_db()
    st.markdown("**student 表**")
    st.dataframe(pd.read_sql_query("SELECT * FROM student",conn), use_container_width=True)
    st.markdown("**course 表**")
    st.dataframe(pd.read_sql_query("SELECT * FROM course",conn), use_container_width=True)
    conn.close()

default_sql = {
"基础查询":"SELECT name, score FROM student;",
"条件筛选":"SELECT name, score FROM student WHERE score >= 85;",
"排序":"SELECT name, score FROM student ORDER BY score DESC;",
"聚合函数":"SELECT AVG(score) AS avg_score FROM student;",
"分组查询":"SELECT class, COUNT(*) AS student_count FROM student GROUP BY class;"
}
sql=st.text_area("在这里编写 SQL", value=default_sql[category], height=140)
if st.button("运行 SQL 并自动判题", type="primary"):
    cleaned=sql.strip()
    upper=cleaned.upper()
    forbidden=["INSERT","UPDATE","DELETE","DROP","ALTER","CREATE","REPLACE","ATTACH","DETACH","PRAGMA","VACUUM"]
    if not cleaned:
        st.error("请先输入 SQL。")
    elif not upper.startswith("SELECT"):
        st.error("当前练习区仅允许 SELECT 查询语句。")
    elif any(word in upper.split() for word in forbidden):
        st.error("检测到不允许的操作。本练习区仅开放查询功能。")
    elif ";" in cleaned.rstrip(";"):
        st.error("一次只允许执行一条 SQL 语句。")
    else:
        conn=build_db()
        try:
            conn.set_progress_handler(lambda: 1, 100000)
            result=pd.read_sql_query(cleaned,conn)
            st.success(f"SQL 执行成功，共返回 {len(result)} 行。")
            st.dataframe(result, use_container_width=True)
            if task["check"](result):
                st.balloons()
                st.success("🎉 自动判题通过！本题掌握情况良好。")
            else:
                st.warning("SQL 可以执行，但结果与本题要求不完全一致。请检查字段、筛选条件、排序或分组逻辑。")
                with st.expander("查看提示"):
                    st.code(task["hint"], language="sql")
        except Exception as e:
            st.error(f"SQL 执行失败：{e}")
            st.info("请检查表名、字段名、关键字拼写和 SQL 语法。")
        finally:
            conn.close()

st.info("说明：这是比赛原型中的教学沙箱，使用内存数据库和演示数据，不连接学校或个人真实数据库。自动判题目前针对指定练习任务进行结果核验。")
