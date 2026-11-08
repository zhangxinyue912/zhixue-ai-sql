import os
import requests

def get_ai_config():
    """Read API settings from Streamlit secrets first, then environment variables."""
    def read(name, default=""):
        try:
            value = st_secrets_get(name)
            if value:
                return str(value)
        except Exception:
            pass
        return os.getenv(name, default)
    return {
        "api_key": read("AI_API_KEY"),
        "base_url": read("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "model": read("AI_MODEL", "gpt-4o-mini"),
    }

def st_secrets_get(name):
    import streamlit as st
    return st.secrets.get(name, "")

def ask_ai(messages, temperature=0.4):
    cfg = get_ai_config()
    if not cfg["api_key"]:
        return None, "尚未配置 API Key。请先在项目根目录创建 .streamlit/secrets.toml 并填写配置。"
    if not cfg["base_url"] or not cfg["model"]:
        return None, "API 地址或模型名称未配置完整。"
    url = cfg["base_url"] + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            return None, f"模型服务返回 HTTP {response.status_code}：{response.text[:500]}"
        data = response.json()
        return data["choices"][0]["message"]["content"], None
    except requests.Timeout:
        return None, "请求超时，请检查网络或稍后重试。"
    except requests.RequestException as e:
        return None, f"网络请求失败：{e}"
    except (KeyError, IndexError, ValueError):
        return None, "模型返回格式不符合 OpenAI 兼容接口规范，请检查 API 服务商配置。"

SYSTEM_PROMPT = """你是“知学 AI”的数据库课程辅导老师，面向大学本科初学者。
请遵守：
1. 使用中文，解释清楚、循序渐进，不嘲讽学生。
2. 优先根据学生给出的 SQL、题目、报错和学习知识点回答，不臆测数据库中不存在的表或字段。
3. 讲解 SQL 时说明关键字作用，并给出可运行的小例子。
4. 学生答错时先定位可能原因，再给修改方向，最后给一道相近练习题。
5. 如果信息不足，明确指出缺少什么，不要编造执行结果。
6. 不要声称你已经实际运行 SQL；SQL 执行结果以系统沙箱为准。
"""

def build_messages(topic, question, sql, error, chat_history):
    context = f"""当前知识点：{topic}
练习题/学习问题：{question or '学生未提供'}
学生 SQL：{sql or '学生未提供'}
执行报错或判题反馈：{error or '暂无'}
请结合以上上下文帮助学生。"""
    return [{"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":context}] + chat_history
