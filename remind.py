"""
暑假课程提醒脚本
- 读取 schedule.json（从课程表编辑器导出）
- 检查当前时间，距开课约 30 分钟时通过 Server酱 推送到微信
- 配合 GitHub Actions 每 30 分钟自动运行
"""

import json
import os
import datetime

import requests

# ── 配置 ──────────────────────────────────────────────
# Server酱 SendKey，通过 GitHub Secrets 传入
SEND_KEY = os.environ.get("SEND_KEY", "")
if not SEND_KEY:
    print("未设置 SEND_KEY，跳过推送")
    exit(0)

REMIND_MINUTES = 30          # 提前多少分钟提醒
TOLERANCE_MINUTES = 15       # 容错窗口（>=15 避免同一条被两次检查重复发送）

# ── 推送函数 ──────────────────────────────────────────
def send_wx(title: str, content: str) -> bool:
    """通过 Server酱 发送微信消息"""
    try:
        r = requests.post(
            f"https://sctapi.ftqq.com/{SEND_KEY}.send",
            data={"title": title, "desp": content},
            timeout=10,
        )
        result = r.json()
        if result.get("code") == 0:
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
