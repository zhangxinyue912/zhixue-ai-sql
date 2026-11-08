def explain_topic(topic):
    content = {
        "SELECT 基础查询": """
### 1. SELECT 基础查询
SELECT 用于指定要查询的列，FROM 用于指定数据表。

```sql
SELECT name, age
FROM student;
```
- `SELECT *`：查询所有列。
- `SELECT name, age`：只查询指定列。
- 多个字段之间用逗号分隔。
""",
        "WHERE 条件筛选": """
### 2. WHERE 条件筛选
WHERE 用于筛选满足条件的记录。

```sql
SELECT *
FROM student
WHERE score >= 60 AND age >= 18;
```
常见运算符：
- 比较：`>`、`<`、`>=`、`<=`、`=`、`<>`
- 逻辑：`AND`、`OR`、`NOT`
- 范围：`BETWEEN ... AND ...`
- 模糊匹配：`LIKE`，`%` 表示任意长度字符。
""",
        "ORDER BY 排序": """
### 3. ORDER BY 排序
ORDER BY 对查询结果排序。

```sql
SELECT name, score
FROM student
ORDER BY score DESC;
```
- `ASC`：升序（默认）。
- `DESC`：降序。
- 可按多个字段排序：`ORDER BY class ASC, score DESC`。
""",
        "聚合函数": """
### 4. 聚合函数
常用聚合函数：
- `COUNT(*)`：统计行数。
- `SUM(score)`：求和。
- `AVG(score)`：平均值。
- `MAX(score)`：最大值。
- `MIN(score)`：最小值。

```sql
SELECT AVG(score)
FROM student;
```
""",
        "GROUP BY 分组": """
### 5. GROUP BY 分组
GROUP BY 将具有相同字段值的记录归为一组，常与聚合函数一起使用。

```sql
SELECT class, COUNT(*) AS student_count
FROM student
GROUP BY class
HAVING COUNT(*) > 10;
```
- `GROUP BY`：分组。
- `HAVING`：筛选分组后的结果。
- `WHERE`：通常在分组前筛选原始记录。
""",
        "综合查询": """
### 6. 综合查询
常见查询结构：

```sql
SELECT class, AVG(score) AS avg_score
FROM student
WHERE score >= 60
GROUP BY class
HAVING AVG(score) >= 75
ORDER BY avg_score DESC
LIMIT 5;
```
记忆顺序：SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT。
"""
    }
    return content.get(topic, "暂时没有该知识点的讲解内容。")

def make_study_plan(accuracy):
    if accuracy < 60:
        return """
1. 先复习 SELECT、FROM 和 WHERE 的基本用法。
2. 每天完成 5 道基础查询题，并逐题阅读解析。
3. 熟悉后再学习排序和聚合函数。
4. 重新完成一次诊断测评，观察正确率变化。
"""
    if accuracy < 80:
        return """
1. 重点巩固本次测评中正确率较低的知识点。
2. 练习 WHERE 多条件筛选、ORDER BY 多字段排序。
3. 尝试 COUNT、AVG 与 GROUP BY 的组合查询。
4. 两天后进行一次复测。
"""
    return """
1. 当前基础掌握情况较好，可以进入综合查询练习。
2. 尝试将 WHERE、GROUP BY、HAVING 和 ORDER BY 组合使用。
3. 练习阅读真实数据表结构并独立编写查询语句。
4. 定期复测，保持知识熟练度。
"""
