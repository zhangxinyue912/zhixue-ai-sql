import json
from database import get_history, get_wrong_answers, get_practice_history

def get_mastery_stats(student):
    """根据历史诊断记录累计计算知识点正确率。"""
    totals = {}
    for item in get_history(student):
        try:
            stats = json.loads(item["topic_stats"])
        except (TypeError, ValueError):
            continue
        for topic, value in stats.items():
            slot = totals.setdefault(topic, {"correct": 0, "total": 0})
            slot["correct"] += int(value.get("correct", 0))
            slot["total"] += int(value.get("total", 0))
    result = []
    for topic, value in totals.items():
        total = value["total"]
        correct = value["correct"]
        result.append({
            "知识点": topic,
            "累计答对": correct,
            "累计作答": total,
            "掌握度": round(correct / total * 100, 1) if total else 0.0
        })
    return sorted(result, key=lambda x: (x["掌握度"], -x["累计作答"]))

def build_learning_path(student):
    stats = get_mastery_stats(student)
    wrongs = get_wrong_answers(student, unresolved_only=True)
    practices = get_practice_history(student)
    if not stats:
        return [
            "先完成一次“知识诊断”，建立个人 SQL 学习基线。",
            "完成诊断后，系统会根据各知识点表现生成复习顺序。"
        ]
    path = []
    for item in stats:
        mastery = item["掌握度"]
        topic = item["知识点"]
        if item["累计作答"] < 2:
            path.append(f"了解阶段｜{topic}：当前样本较少，建议再完成 2—3 道相关练习。")
        elif mastery < 60:
            path.append(f"优先补强｜{topic}：先阅读基础讲解，再完成专项练习并复测。")
        elif mastery < 80:
            path.append(f"巩固提升｜{topic}：重点复习错题，完成中等难度练习。")
        else:
            path.append(f"保持与进阶｜{topic}：当前记录表现较好，可尝试综合 SQL 题。")
    if wrongs:
        path.append(f"错题回顾｜目前有 {len(wrongs)} 条尚未标记为已掌握的错题，建议优先复习。")
    if practices:
        path.append("持续跟踪｜专项练习记录已纳入学习轨迹，完成新练习后可再次查看变化。")
    return path

def build_ai_study_prompt(student):
    stats = get_mastery_stats(student)
    wrongs = get_wrong_answers(student, unresolved_only=True)[:8]
    summary = {
        "知识点统计": stats,
        "未掌握错题摘要": [
            {"知识点": w["topic"], "题目": w["question"],
             "学生答案": w["user_answer"], "正确答案": w["correct_answer"]}
            for w in wrongs
        ]
    }
    return (
        "你是知学AI的SQL课程辅导老师。请只依据下面的学习记录，"
        "给出适合SQL初学者的复习优先级、解释重点和3天学习安排。"
        "不要编造学生没有做过的题目或学习成绩；样本不足时明确说明。\n\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
    )
