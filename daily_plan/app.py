import os
from zoneinfo import ZoneInfo
import json
from datetime import datetime, timedelta
import time
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from telegram import send_telegram_message,get_telegram_updates
import requests
import threading
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

UPDATE_ID_FILE = "last_update_id.txt"

def load_last_update_id():
    if os.path.exists(UPDATE_ID_FILE):
        with open(UPDATE_ID_FILE, "r") as f:
            return int(f.read().strip())
    return None

def save_last_update_id(update_id):
    with open(UPDATE_ID_FILE, "w") as f:
        f.write(str(update_id))

endpoint = os.getenv("LLM_URL")
model_name = "gpt-4.1"
token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider,
)

def format_plan_as_text(plan):
    lines = []
    for item in plan:
        time = item["time"]
        topic = item["topic"]
        goal = item["goal"]
        advice = item["advice"]
        lines.append(f"{time}：{topic}，目标：{goal}，建议：{advice}")
    return "\n".join(lines)

#今天可用时间段为：10:00到23:00。
# ==== 构建 Prompt ====
def build_study_prompt(user_input):
    return f"""
你是一个高效的学习规划助手。

以下是用户今天的学习计划和可用时间，请根据内容推断用户今天的学习计划和可用学习时间范围，并合理制定详细的今天的学习计划：

「{user_input}」

请你根据用户的时间安排，合理划分任务节奏（例如短任务可用 15 分钟，深度阅读可安排 40-60 分钟），并合理穿插休息时间。

每段学习任务输出以下字段：
- time：起止时间段（如 10:00-10:40）
- topic：学习主题
- goal：该时间段的目标
- advice：学习建议

输出格式为 JSON 数组，例如：
[
  {{"time": "10:00-10:40", "topic": "xxx", "goal": "xxx", "advice": "xxx"}},
  ...
]

注意：请只输出符合 JSON 格式的数组内容，不要额外解释说明。
"""

# ==== 调用 LLM 生成学习计划 ====
def generate_daily_plan(goal):
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": build_study_prompt(goal)}],
        #max_completion_tokens=800,
        temperature=1.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    content = response.choices[0].message.content
    print("GPT 返回原始内容：\n", content)

    try:
        plan = json.loads(content)
        return plan
    except Exception as e:
        print("JSON 解析失败：", e)
        return []


def parse_message(msg):
    chat_id = msg["message"]["chat"]["id"]
    text = msg["message"].get("text", "")
    return chat_id, text

def handle_message(chat_id, text):
    goal = text.strip()
    if not goal.startswith("今日计划和可用时间"):
        return

    goal = goal[len("今日计划和可用时间"):].strip()

    send_telegram_message(f"收到你的今日计划和可用时间：{goal}\n正在生成今日学习计划...", chat_id)
    plan = generate_daily_plan(goal)
    if not plan:
        send_telegram_message("生成失败，请稍后再试。", chat_id)
        return

    summary = format_plan_as_text(plan)

    send_telegram_message(summary, chat_id)

    schedule_plan_notification(plan,chat_id)

    #for item in plan:
    #    msg = f"{item['time']} - {item['topic']}\n {item['goal']}\n{item['advice']}"
    #    send_telegram_message(msg, chat_id)


local_u=ZoneInfo("UTC")
local_z=ZoneInfo("America/Los_Angeles")

def schedule_plan_notification(plan, chat_id):
    now_utc = datetime.utcnow()
    now = now_utc.replace(tzinfo=local_u).astimezone(local_z)
    print("当前系统本地时间：", now.strftime("%Y-%m-%d %H:%M:%S"))
    for item in plan:
        start_str = item["time"].split("-")[0]
        try:
            start_time = datetime.strptime(start_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day, tzinfo=local_z 
            )
            s = start_time.strftime("%Y-%m-%d %H:%M")
            print(f"触发时间：{s} -> {item['topic']} 目标：{item['goal']}")

            delay = (start_time - now).total_seconds()
            if delay > 0:
                threading.Timer(delay, send_telegram_message, args=[f"现在开始：{item['topic']} 目标：{item['goal']} 建议：{item['advice']}", chat_id]).start()
        except Exception as e:
            print(f"跳过调度失败项：{item}, 错误：{e}")

# ==== 主函数 ====
if __name__ == "__main__":
    LAST_UPDATE_ID = load_last_update_id()
    print(f"正在监听 Telegram 用户输入每日目标...，从{LAST_UPDATE_ID}开始读取消息")
    while True:
        updates = get_telegram_updates(offset=LAST_UPDATE_ID)
        for result in updates.get("result", []):
            chat_id, text = parse_message(result)
            handle_message(chat_id, text)
            LAST_UPDATE_ID = result["update_id"] + 1
            save_last_update_id(LAST_UPDATE_ID)
        time.sleep(5)
