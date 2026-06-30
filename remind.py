"""
暑假课程提醒脚本
- 读取 schedule.json（从课程表编辑器导出）
- 检查当前时间，距开课约 30 分钟时通过 PushPlus 群组推送到微信
- 配合 GitHub Actions 每 30 分钟自动运行
"""

import json
import os
import datetime

import requests

# ── 配置 ──────────────────────────────────────────────
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSHPLUS_TOPIC = os.environ.get("PUSHPLUS_TOPIC", "")

if not PUSHPLUS_TOKEN:
    print("未设置 PUSHPLUS_TOKEN，跳过推送")
    exit(0)

REMIND_MINUTES = 30          # 提前多少分钟提醒
TOLERANCE_MINUTES = 15       # 容错窗口

# ── 推送函数 ──────────────────────────────────────────
def send_wx(title: str, content: str) -> bool:
    """通过 PushPlus 群组发送微信消息（群内所有人都能收到）"""
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content.replace("\n", "<br>"),
        "template": "html",
    }
    if PUSHPLUS_TOPIC:
        payload["topic"] = PUSHPLUS_TOPIC

    try:
        r = requests.post(
            "http://www.pushplus.plus/send",
            json=payload,
            timeout=10,
        )
        result = r.json()
        if result.get("code") == 200:
            print(f"推送成功: {title}")
            return True
        else:
            print(f"推送失败: {result}")
            return False
    except Exception as e:
        print(f"推送异常: {e}")
        return False

# ── 主逻辑 ────────────────────────────────────────────
def main():
    # 北京时间
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    today_str = now.strftime("%Y-%m-%d")

    # 加载课程表
    with open("schedule.json", encoding="utf-8") as f:
        classes = json.load(f)

    sent_count = 0
    for cls in classes:
        # 只检查今天的课程
        if cls.get("date", "") != today_str:
            continue

        name = cls.get("name", "未知课程")
        location = cls.get("location", "")
        start_str = cls.get("start", "")
        end_str = cls.get("end", "")

        if not start_str:
            continue

        # 解析上课开始时间
        try:
            start_h, start_m = map(int, start_str.split(":"))
        except ValueError:
            continue

        start_dt = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        remind_at = start_dt - datetime.timedelta(minutes=REMIND_MINUTES)

        # 检查当前时间是否在提醒窗口内
        diff_seconds = abs((now - remind_at).total_seconds())
        if diff_seconds > TOLERANCE_MINUTES * 60:
            continue

        # 构造消息
        title = f"{name} 还有 {REMIND_MINUTES} 分钟开始"
        content = (
            f"**课程**：{name}\n\n"
            f"**时间**：{start_str} — {end_str}\n\n"
            f"**地点**：{location}\n\n"
            f"请准时出发！"
        )

        if send_wx(title, content):
            sent_count += 1

    print(f"本次共发送 {sent_count} 条提醒")

if __name__ == "__main__":
    main()
