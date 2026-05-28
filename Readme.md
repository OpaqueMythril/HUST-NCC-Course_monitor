# NCCcourse_monitor - 学院选课系统课程智能监测上新助手

这是一个专为华科网安选课系统打造的课程智能监测与自动上新提醒工具。娱乐性大一些，主要是个人学习用

本工具在严格遵守系统限流规则（绕过“1秒内重复请求提交”、规避“12小时限流 200 次”）的前提下，能够实现长时间、安全、平稳地周期性轮询监控。工具支持**单机独立控制台监测**与 **NoneBot 机器人 Webhook 联动群消息广播**两种运行模式。

## 核心特性

- **严格限流保护**：内置延迟控制，严格规避“1秒内防重复提交”限制；默认每 240 秒（4分钟）检测一次，全天候运行不触发 12h/200次 的限流拉黑阈值。
- **多模式自由切换**：
  - **单机极简版**：开箱即用，通过控制台或日志输出变化。
  - **Bot 联动版**：支持本地寝室/低功耗设备抓取，通过 Webhook 实时同步至云端服务器，控制 QQ 机器人向指定群组广播上新消息。



##  环境准备

在开始之前，请确保您的 Python 环境已安装依赖库：

```
pip install requests python-dotenv fastapi
```

##  关键步骤：如何获取最新的 Cookie 与 Token 凭证

由于学校选课系统安全性较强（限制图形验证码登录），我们通过在浏览器登录一次并提取 Cookie 链的方式进行免登身份维持：

1. **登录系统**：在电脑浏览器打开选课系统，手动完成登录，点击进入 **「选课中心」** 页面。
2. **打开抓包**：按下键盘上的 **F12**（或右键 -> 检查），切换到 **「网络 (Network)」** 标签页，勾选 **「保留日志 (Preserve log)」**。
3. **定位数据包**：刷新一次选课页面，在请求列表中寻找名字为 `list?pageNum=1...` 的 XHR/Fetch 请求。
4. **提取值**：
   - **`NCC_RAW_TOKEN`**：在右侧「标头 (Headers)」的 **「请求标头 (Request Headers)」** 中，找到 `Authorization` 字段，复制 `Bearer` 后面的那一长串乱码（通常以 `eyJhbGciOiJIUzUxMiJ9` 开头，代表 HS512 签名算法）。
   - **`NCC_USER_COOKIE`**：在同一栏下找到 `cookie:` 字段，复制后面的整段长字符串（格式为 `username=...; password=...; Admin-Token=...`）。

*提示：为了防失效，获取到 Cookie 串之后请不要在网页上点击“退出登录”或“注销账号”，直接关闭浏览器标签页即可。若依系统凭证有效期根据学校设置而定（通常为数小时或数天不等），失效后只需重新登录重复此步骤并覆盖本地 `.env` 文件。*

##  运行指南

### 模式 A：单机独立监测版（适合不需要机器人的同学）

1. 在项目根目录下，新建一个 `.env` 文件，内容如下（注意等号两边不要有空格，Cookie 推荐使用双引号包裹）：

   ```
   NCC_RAW_TOKEN=这里粘贴你获取到的Token长乱码
   NCC_USER_COOKIE="username=学号; rememberMe=true; ...sidebarStatus=0"
   ```

2. 直接在终端运行主程序：

   ```
   python course_monitor.py
   ```

3. 首次运行会建立初始课程列表缓存（保存为 `course_history.json`），之后每 4 分钟自动无感知比对，一旦发现有新上线的课程，将在控制台高亮输出。

### 模式 B：Bot Webhook 联动群通知版（适合有云服务器和 NoneBot2 机器人的同学）

本模式下，本地脚本作为侦察兵 Agent保持连接内网抓取，一有新情报就利用 Webhook 跨公网跨防火墙推送到云端机器人发送至指定的 QQ 群。

#### 1. 宿舍/本地电脑客户端部署

1. 打开 `webhook` 目录，在 `webhook` 文件夹下新建 `.env` 文件，填入如下内容：

   ```
   NCC_RAW_TOKEN=这里粘贴你获取到的Token长乱码
   NCC_USER_COOKIE="username=学号; rememberMe=true; ...sidebarStatus=0"
   
   # 配置你的云服务器 Bot 接口地址与通信暗号
   BOT_WEBHOOK_URL=[http://服务器ip:8080/report_course](http://服务器ip:8080/report_course)
   BOT_WEBHOOK_KEY=HUST_SECRET_666
   ```

2. 启动本地侦察主程序：

   ```
   python webhook/main.py
   ```

#### 2. 云服务器 NoneBot 机器人端部署

1. 将 `webhook/course_webhook.py` 文件放入你云服务器上 NoneBot 项目的 `src/plugins/` 或 `plugins/` 插件目录下。

2. 打开服务器 NoneBot2 项目根目录下的配置文件（`.env.dev` 或 `.env.prod`），在文件末尾追加以下两行：

   ```
   course_authorized_group=108672097    # 允许通知的目标 QQ 群号
   course_webhook_key="HUST_SECRET_666"    # 与本地 Agent 对应的通信暗号
   ```

3. 启动或重启你的 NoneBot 机器人实例。本地监测程序一有风吹草动，群里就会立刻收到猫娘风趣、可爱的上新催促通知！

