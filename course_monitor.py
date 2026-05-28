import requests
import time
import random
import json
import os
from dotenv import load_dotenv

# 加载同级目录下的 .env 文件
load_dotenv()

# ================= 核心配置区 =================
BASE_URL = "http://222.20.126.201"
COURSE_API_URL = f"{BASE_URL}/dev-api/xuanke/course/student"

# 从运行 environment 或 .env 中动态读取凭证
RAW_TOKEN = os.getenv("NCC_RAW_TOKEN", "")
USER_COOKIE = os.getenv("NCC_USER_COOKIE", "")

AUTH_TOKEN = f"Bearer {RAW_TOKEN}" if RAW_TOKEN else ""

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

PARAMS = {
    "activeSemester": "true",
    "chosen": "false",
    "choosable": "true",
    "pageNum": 1,
    "pageSize": 50
}

CHECK_INTERVAL = 240
DATA_FILE = "course_history.json"


def get_courses():
    """获取课程列表数据"""
    if not RAW_TOKEN or not USER_COOKIE:
        print(f"[{time.strftime('%H:%M:%S')}] 未检测到环境变量配置，请检查.env文件")
        return None

    try:
        # 严格绕过“1秒内重复请求”监测
        time.sleep(random.uniform(1.5, 2.5))

        response = requests.get(COURSE_API_URL, headers=HEADERS, params=PARAMS, timeout=10)

        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("code") == 200:
                return res_json.get("rows", [])
            elif res_json.get("code") == 401 or "认证失败" in res_json.get("msg", ""):
                print(f"[{time.strftime('%H:%M:%S')}] 认证已失效，Token可能已被刷新！")
                return None
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 业务逻辑异常: {res_json.get('msg')}")
        elif response.status_code == 401:
            print(f"[{time.strftime('%H:%M:%S')}] 认证已失效，网关拒绝访问")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 请求失败：{response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] 网络异常: {e}")
    return None


def main():
    print("=== NCC选课监测 ===")
    print(f"策略：每 {CHECK_INTERVAL} 秒自动检查一次。安全限流中...")

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_courses = json.load(f)
    except:
        old_courses = []

    while True:
        current_list = get_courses()

        if current_list is not None:
            old_ids = {str(c.get('courseCode')) for c in old_courses if c.get('courseCode')}
            newly_added = []

            for course in current_list:
                c_id = str(course.get('courseCode'))
                if c_id not in old_ids:
                    newly_added.append(course)

            if newly_added:
                print(f"\n🔔 [{time.strftime('%H:%M:%S')}] 检测到新课程！")
                for c in newly_added:
                    name = c.get('courseName', '未知')
                    teacher = c.get('teacherName', '未知')
                    print(f"  - 课程: {name} ({c_id}) | 教师: {teacher}")

                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(current_list, f, ensure_ascii=False, indent=4)
                old_courses = current_list
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 暂无新增课程。")

        time.sleep(CHECK_INTERVAL + random.randint(5, 15))


if __name__ == "__main__":
    main()