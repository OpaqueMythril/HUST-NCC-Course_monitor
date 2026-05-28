import requests
import time
import random
import json
import sys
import os
from dotenv import load_dotenv

# 加载同级目录下的 .env 文件
load_dotenv()

# ================= 配置区=================
# 1. 内网 API 地址 (校园网专用，移除尾部斜杠防止若依路由匹配失效)
BASE_URL = "http://222.20.126.201"
COURSE_API_URL = f"{BASE_URL}/dev-api/xuanke/course/student"

# 2. 身份凭证（动态从环境变量读取）
RAW_TOKEN = os.getenv("NCC_RAW_TOKEN", "")
USER_COOKIE = os.getenv("NCC_USER_COOKIE", "")

AUTH_TOKEN = f"Bearer {RAW_TOKEN}" if RAW_TOKEN else ""

# 3. 云服务器 Webhook 配置（动态从环境变量读取）
BOT_WEBHOOK_URL = os.getenv("BOT_WEBHOOK_URL", "http://127.0.0.1:8080/report_course")
WEBHOOK_KEY = os.getenv("BOT_WEBHOOK_KEY", "DEFAULT_SECRET")

# 4. 运行参数
CHECK_INTERVAL = 240  # 每 4 分钟扫描一次
DATA_FILE = "../course_history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Authorization": AUTH_TOKEN,
    "Cookie": USER_COOKIE,
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Host": "222.20.126.201",
    "Referer": f"{BASE_URL}/student/student/course",
    "Connection": "keep-alive"
}
# ===========================================

def get_courses():
    """从校园网抓取课程数据"""
    if not RAW_TOKEN or not USER_COOKIE:
        print(f"[{time.strftime('%H:%M:%S')}] 未检测到本地凭证配置，请检查 .env 文件！")
        return None

    params = {
        "activeSemester": "true",
        "chosen": "false",
        "choosable": "true",
        "pageNum": 1,
        "pageSize": 100
    }
    try:
        # 强制随机休眠，模仿人类行为
        time.sleep(random.uniform(2.0, 4.0))
        response = requests.get(COURSE_API_URL, headers=HEADERS, params=params, timeout=15)

        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("code") == 200:
                return res_json.get("rows", [])
            elif res_json.get("code") == 401 or "认证失败" in res_json.get("msg", ""):
                print(f"[{time.strftime('%H:%M:%S')}] 认证已失效，请重新抓取 Token")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 业务逻辑异常: {res_json.get('msg')}")
        elif response.status_code == 401:
            print(f"[{time.strftime('%H:%M:%S')}] 认证已失效，请重新抓取 Token！")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 接口请求失败: {response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 网络异常: {e}")
    return None


def report_to_cloud(newly_added, all_courses):
    """向云服务器发送情报，包含新课和全量课表"""
    if not BOT_WEBHOOK_URL or "127.0.0.1" in BOT_WEBHOOK_URL:
        print(f"[{time.strftime('%H:%M:%S')}] 当前 Webhook URL 为默认或本地回路，请确认是否已配置。")

    try:
        payload = {
            "new_courses": newly_added,
            "all_courses": all_courses
        }
        headers = {"X-Secret-Key": WEBHOOK_KEY, "Content-Type": "application/json"}

        resp = requests.post(BOT_WEBHOOK_URL, json=payload, headers=headers, timeout=15)

        if resp.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] 成功同步！新课数: {len(newly_added)}，全量缓存数: {len(all_courses)}")
            return True
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 云端拒绝接收，返回: {resp.text}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 无法连接至云服务器: {e}")
    return False


def main():
    print("=" * 40)
    print(f" 扫描频率: 每 {CHECK_INTERVAL} 秒一次")
    print("=" * 40)

    # 加载历史快照
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_courses = json.load(f)
        print(f"[{time.strftime('%H:%M:%S')}] 加载本地快照成功。")
    except:
        old_courses = []
        print(f"[{time.strftime('%H:%M:%S')}] 无历史快照，准备建立初始记录...")

    while True:
        current_list = get_courses()

        if current_list is not None:
            old_ids = {str(c.get('courseCode')) for c in old_courses if c.get('courseCode')}
            newly_added = []

            for course in current_list:
                c_id = str(course.get('courseCode'))
                if c_id not in old_ids:
                    newly_added.append(course)

            # 只有在新课上报并同步全量数据成功后，才更新本地快照
            if report_to_cloud(newly_added, current_list):
                if newly_added:
                    print(f"🔔 发现新课并已推送：{[c.get('courseName') for c in newly_added]}")

                # 持久化存储
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(current_list, f, ensure_ascii=False, indent=4)
                old_courses = current_list
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 扫描完成，但同步云端失败，暂不更新本地记录。")

        # 随机冷却
        sleep_time = CHECK_INTERVAL + random.randint(5, 15)
        time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n下班睡觉咯~")
        sys.exit(0)