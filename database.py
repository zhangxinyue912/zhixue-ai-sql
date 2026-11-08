import sqlite3
from datetime import datetime
from pathlib import Path
import json

DB_PATH = Path(__file__).with_name("zhixue.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """创建基础表，并为旧版本数据库安全补充第四阶段所需表。"""
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            topic_stats TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS wrong_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            question_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            user_answer TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_at TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS practice_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS learning_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            topic TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

def save_attempt(student, score, total, topic_stats):
    accuracy = score / total * 100 if total else 0
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO attempts(student,score,total,accuracy,topic_stats,created_at) VALUES(?,?,?,?,?,?)",
            (student, score, total, accuracy,
             json.dumps(topic_stats, ensure_ascii=False),
             datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def get_history(student):
    with connect() as conn:
        rows = conn.execute(
            "SELECT score,total,accuracy,created_at,topic_stats FROM attempts WHERE student=? ORDER BY created_at DESC",
            (student,)
        ).fetchall()
    return [{"score":r["score"],"total":r["total"],"accuracy":r["accuracy"],
             "created_at":r["created_at"],"topic_stats":r["topic_stats"]} for r in rows]

def get_student_summary(student):
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(AVG(accuracy),0) FROM attempts WHERE student=?",
            (student,)
        ).fetchone()
    return {"attempts":row[0],"answered":row[1],"accuracy":row[2]}

def record_wrong_answers(student, questions, answers):
    """保存本次答错题目；同一道题重复答错会形成新的学习记录。"""
    now = datetime.now().isoformat(timespec="seconds")
    records = []
    for q in questions:
        user_answer = answers.get(q["id"])
        if user_answer != q["answer"]:
            records.append((
                student, str(q["id"]), q["topic"], q["question"],
                user_answer or "", q["answer"], q.get("explanation", ""),
                now, 0
            ))
    if records:
        with connect() as conn:
            conn.executemany(
                """INSERT INTO wrong_answers
                (student,question_id,topic,question,user_answer,correct_answer,explanation,created_at,resolved)
                VALUES(?,?,?,?,?,?,?,?,?)""", records
            )
    return len(records)

def get_wrong_answers(student, unresolved_only=False):
    sql = """SELECT id,question_id,topic,question,user_answer,correct_answer,
             explanation,created_at,resolved
             FROM wrong_answers WHERE student=?"""
    params = [student]
    if unresolved_only:
        sql += " AND resolved=0"
    sql += " ORDER BY created_at DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

def mark_wrong_resolved(student, wrong_id):
    with connect() as conn:
        conn.execute(
            "UPDATE wrong_answers SET resolved=1 WHERE id=? AND student=?",
            (wrong_id, student)
        )

def save_practice_record(student, topic, score, total):
    accuracy = score / total * 100 if total else 0
    with connect() as conn:
        conn.execute(
            """INSERT INTO practice_records(student,topic,score,total,accuracy,created_at)
            VALUES(?,?,?,?,?,?)""",
            (student, topic, score, total, accuracy,
             datetime.now().isoformat(timespec="seconds"))
        )

def get_practice_history(student):
    with connect() as conn:
        rows = conn.execute(
            """SELECT topic,score,total,accuracy,created_at
            FROM practice_records WHERE student=? ORDER BY created_at DESC""",
            (student,)
        ).fetchall()
    return [dict(r) for r in rows]

def add_learning_note(student, topic, note):
    with connect() as conn:
        conn.execute(
            "INSERT INTO learning_notes(student,topic,note,created_at) VALUES(?,?,?,?)",
            (student, topic, note, datetime.now().isoformat(timespec="seconds"))
        )

def get_learning_notes(student):
    with connect() as conn:
        rows = conn.execute(
            """SELECT topic,note,created_at FROM learning_notes
            WHERE student=? ORDER BY created_at DESC""", (student,)
        ).fetchall()
    return [dict(r) for r in rows]
