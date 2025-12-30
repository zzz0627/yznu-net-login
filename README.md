<h1 align='center'>Campus Network Auto-Login Daemon</h1>

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

本项目提供一个轻量级、低资源占用的校园网自动重连守护进程。专为解决凌晨 02:00 强制断网及网络不稳定场景设计，支持 RC4 加密认证与双重网络检测机制。

---

## ✨ 简介

本项目实现了一个轻量级的校园网自动登录守护进程，用于解决以下场景：

-  **凌晨断网重连**：校园网每日 02:00 强制踢线后自动重新认证
-  **网络保活**：持续监控网络状态，断网时立即触发登录
-  **安全加密**：采用与官方网关一致的 RC4 加密算法
-  **轻量运行**：基于 Python 标准库和 `requests`，资源占用低

---

## 🛠️ 系统要求

### 必需环境

- **操作系统**：Windows 11 / Windows 10
- **Python**：3.9 或更高版本
- **网络**：已连接到校园网（有线或无线）

### 依赖库

- `requests >= 2.31.0`

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/zzz0627/yznu-net-login.git
cd yznu-net-login
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或使用国内镜像加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置认证信息

复制配置模板并填写您的账号密码：

```bash
copy config.json.example config.json
```

编辑 `config.json`：

```json
{
  "username": "YourID",     // 改为您的账号
  "password": "YourPassword", // 改为您的密码
}
```

### 4. 测试运行

```bash
python campus_net_keepalive.py
```

**预期输出**：

```
2024-12-30 09:00:00 - INFO - Configuration loaded successfully
2024-12-30 09:00:00 - INFO - ============================================================
2024-12-30 09:00:00 - INFO - Campus Network Auto-Login Daemon Started
2024-12-30 09:00:00 - INFO - Username: xxxxxxx
2024-12-30 09:00:00 - INFO - Check interval: 60s
2024-12-30 09:00:00 - INFO - ============================================================
```

> 注：按 `Ctrl+C` 可停止程序。如果看到 `✓ Login successful`，说明配置正确。

____

## ⚙️ 部署指南 (Windows Service)

推荐使用 **Windows 任务计划程序** 实现开机自启与守护。

<details>
<summary><strong>点击展开详细配置步骤</strong></summary>

1. **创建任务**：按 `Win + R` 打开运行对话框，输入 `taskschd.msc`，点击 "创建基本任务"，命名为 `CampusAutoLogin`。
2. **触发器**：选择 **"计算机启动时"** (At Startup)。
3. **操作**：

|      字段      |        填写内容         |                       示例                       |
| :------------: | :---------------------: | :----------------------------------------------: |
| **程序或脚本** | Python 解释器的完整路径 |            `E:\Anaconda3\pythonw.exe`            |
|  **添加参数**  |  Python 脚本的完整路径  | `E:\Code\yznu-net-login\campus_net_keepalive.py` |
|   **起始于**   |      脚本所在目录       |            `E:\Code\yznu-net-login\`             |

> ⚠️ **重要提示**：
>
> - 使用 `pythonw.exe`（而非 `python.exe`），可避免显示黑色控制台窗口
> - 所有路径必须是**绝对路径**
> - "起始于"字段必须填写，否则无法读取 `config.json`

* **安全选项** (重要)：
  * [x] 不管用户是否登录都要运行
  * [x] 使用最高权限运行
* 条件页
  * [ ] 取消勾选 "只有在计算机使用交流电源时才启动"
* 设置页
  * [x] 如果此任务已经运行：请勿启动新实例

</details>

**如何找到 Python 路径**：

```bash
# 在命令提示符中运行
where python
```

示例输出：

```
C:\Users\Administrator>where python
E:\Anaconda3\python.exe
```

将 `python.exe` 改为 `pythonw.exe` 即可。

---

## 🔧 常见问题 (FAQ)

**Q: 提示"Configuration file not found"**

A: 问题出在未创建 `config.json`，请执行`copy config.json.example config.json`，然后编辑 `config.json` 填写账号密码。

**Q: 提示"Placeholder values in configuration"**

A: 问题出在`config.json` 中仍使用模板占位符，请检查`"username"`和`"password"`字段是否已修改为真实值。

**Q: 登录失败，一直提示 Retrying？**

A: 校园网网关地址可能变更。请在浏览器按 `F12` 抓包手动登录过程，更新 `config.json` 中的 `login_url`。

**Q: 需要一直开着电脑吗？**

A: 是的。本程序运行在您的 PC 上。如果需要 24 小时在线，建议部署在树莓派或闲置工控机上。

---

## 🛡️ 技术细节

### RC4 加密算法

校园网网关采用 RC4 流密码对密码进行加密。本项目完全复现了 JavaScript 源码中的加密逻辑：

```python
def rc4_encrypt(plaintext: str, key: str) -> str:
    """Encrypts password using RC4 algorithm."""
    # KSA: Key-Scheduling Algorithm
    # PRGA: Pseudo-Random Generation Algorithm
    # Output: Hex-encoded encrypted string
```

**加密流程**：

1. 生成 13 位毫秒时间戳作为密钥
2. 使用 KSA 初始化 256 字节的 S-box
3. 使用 PRGA 生成伪随机密钥流
4. 明文与密钥流 XOR 运算
5. 转换为十六进制字符串

### HTTP 劫持检测

校园网在未认证状态下会劫持所有 HTTP 请求，重定向到登录页面：

```
访问 baidu.com → 302 重定向 → 1.1.1.3/ac_portal/... → 返回 200
```

**检测逻辑**：

```python
# 检查最终 URL 是否包含校园网网关特征
if '1.1.1.3' in response.url or 'ac_portal' in response.url:
    return False  # 判定为断网
```

### 网络检测策略

采用双重检测机制，兼顾速度和准确性：

|   方式    |         目标         | 超时 | 优先级 |       优点       |
| :-------: | :------------------: | :--: | :----: | :--------------: |
| DNS Ping  | 223.5.5.5<br>8.8.8.8 |  3s  |  🥇 高  | 快速、不消耗流量 |
| HTTP 请求 |      baidu.com       |  5s  |  🥈 中  |   准确检测劫持   |

### 指数退避重试

避免频繁请求对网关造成压力：

| 重试次数 | 延迟时间 | 累计等待 |
| :------: | :------: | :------: |
| 第 1 次  |   立即   |    0s    |
| 第 2 次  |    5s    |    5s    |
| 第 3 次  |   10s    |   15s    |
| 第 4 次  |   20s    |   35s    |
| 第 5 次  |   40s    |   75s    |

---

## 🔄 配置参数说明

`config.json` 完整参数列表：

|        参数        |  类型  | 必填 |          默认值          |                 说明                 |
| :----------------: | :----: | :--: | :----------------------: | :----------------------------------: |
|     `username`     | string |  ✅   |            -             |            学号/一卡通号             |
|     `password`     | string |  ✅   |            -             |                 密码                 |
|    `login_url`     | string |  ✅   |            -             |             登录接口地址             |
|  `check_interval`  |  int   |  ❌   |            60            |          网络检测间隔（秒）          |
|    `max_retry`     |  int   |  ❌   |            5             |             最大重试次数             |
| `retry_base_delay` |  int   |  ❌   |            5             |          重试基础延迟（秒）          |
|   `dns_servers`    | array  |  ❌   | ["223.5.5.5", "8.8.8.8"] |            DNS 服务器列表            |
|  `http_check_url`  | string |  ❌   |  "http://www.baidu.com"  |            HTTP 检测 URL             |
|   `dns_timeout`    |  int   |  ❌   |            3             |         DNS Ping 超时（秒）          |
|   `http_timeout`   |  int   |  ❌   |            5             |         HTTP 请求超时（秒）          |
|    `log_level`     | string |  ❌   |          "INFO"          | 日志级别（DEBUG/INFO/WARNING/ERROR） |

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**