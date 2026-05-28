from fastapi import FastAPI, Request
from nonebot import get_app, get_bot, logger, get_driver

# 动态获取 NoneBot 本地全局配置项
global_config = get_driver().config

# 💡 配置区
AUTHORIZED_GROUP = getattr(global_config, "course_authorized_group", 0)
WEBHOOK_KEY = getattr(global_config, "course_webhook_key", "DEFAULT_SECRET")

app: FastAPI = get_app()

# 部署在云服务器的 NoneBot 根目录下的 .env.dev 或 .env.prod 文件：
# course_authorized_group=想要通知的群聊
# course_webhook_key=对话密钥

@app.post("/report_course")
async def receive_course_report(request: Request):
    # 1. 验证暗号
    key = request.headers.get("X-Secret-Key")
    if not key or key != WEBHOOK_KEY:
        logger.warning(" [Webhook] ⚠️ 收到未知源发来的不合法请求，暗号校验失败！")
        return {"status": "error", "msg": "暗号不对喵！"}

    data = await request.json()
    newly_added = data.get("new_courses", [])

    if not newly_added:
        return {"status": "ok"}

    # 2. 构造猫猫风格消息
    msg_lines = ["🔔 报告！发现新课了喵！", "──────────────"]
    for c in newly_added:
        msg_lines.append(f"课程: {c.get('courseName', '未知')}")
        msg_lines.append(f"教师: {c.get('teacherName', '未知')}")
        msg_lines.append(f"代码: {c.get('courseCode', '未知')}")
        msg_lines.append("──────────────")

    final_msg = "\n".join(msg_lines)

    # 3. 广播给指定群
    if AUTHORIZED_GROUP == 0:
        logger.error(" [Webhook] ❌ 云端未正确配置 course_authorized_group 环境变量！")
        return {"status": "error", "msg": "云端未指定目标通知群号"}

    try:
        bot = get_bot()
        await bot.send_group_msg(group_id=int(AUTHORIZED_GROUP), message=final_msg)
        return {"status": "success"}
    except Exception as e:
        logger.error(f" [Webhook] 推送失败: {e}")
        return {"status": "error", "msg": str(e)}