<h1 align='center'>Campus Network Auto-Login Daemon</h1>

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2011%2F10-lightgrey.svg)](https://www.microsoft.com/windows)
[![Code style: Google](https://img.shields.io/badge/code%20style-google-blueviolet.svg)](https://google.github.io/styleguide/pyguide.html)

针对每日凌晨 02:00 强制断网的校园网环境设计的自动重连守护进程。

---

## 简介

本项目实现了一个轻量级的校园网自动登录守护进程，用于解决以下场景：

- 🌙 **凌晨断网重连**：校园网每日 02:00 强制踢线后自动重新认证
- 🔄 **网络保活**：持续监控网络状态，断网时立即触发登录
- 🛡️ **安全加密**：采用与官方网关一致的 RC4 加密算法
- 🚀 **轻量运行**：基于 Python 标准库和 `requests`，资源占用低

---

## 系统要求

### 必需环境

- **操作系统**：Windows 11 / Windows 10
- **Python**：3.9 或更高版本
- **网络**：已连接到校园网（有线或无线）

### 依赖库

- `requests >= 2.31.0`

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-lab/campus-network-keepalive.git
cd campus-network-keepalive
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
  "username": "YourID",     // 改为您的学号/一卡通号
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
2024-12-30 09:00:00 - INFO - Username: 20210001
2024-12-30 09:00:00 - INFO - Check interval: 60s
2024-12-30 09:00:00 - INFO - ============================================================
```

> 注：按 `Ctrl+C` 可停止程序。如果看到 `✓ Login successful`，说明配置正确。

---

## 自动化部署（Windows 任务计划程序）

### 为什么需要任务计划程序？

为了实现开机自动启动和后台运行，我们使用 Windows 内置的"任务计划程序"（Task Scheduler）创建系统服务。

### 详细配置步骤

#### 步骤 1：打开任务计划程序

**方式A**（推荐）：
1. 按 `Win + R` 打开运行对话框
2. 输入 `taskschd.msc`
3. 按回车

**方式B**：
1. 在开始菜单搜索"任务计划程序"
2. 点击打开

#### 步骤 2：创建基本任务

1. 在右侧"操作"面板，点击 **"创建基本任务..."**
2. **名称**：`校园网自动登录`
3. **描述**：`Campus Network Auto-Login Daemon`
4. 点击"下一步"

#### 步骤 3：配置触发器

1. **触发器类型**：选择 **"计算机启动时"**
   - ✅ 开机自动运行
   - ✅ 无需登录即可启动（适合服务器/实验室电脑）

2. 点击"下一步"

> 📝 **备选方案**：如果只需要登录后启动，可选择"登录时"

#### 步骤 4：配置操作

1. **操作类型**：选择 **"启动程序"**
2. 点击"下一步"

**关键配置**（请仔细填写）：

| 字段 | 填写内容 | 示例 |
|:----:|:-------:|:----:|
| **程序或脚本** | Python 解释器的完整路径 | `C:\Python39\pythonw.exe` |
| **添加参数** | Python 脚本的完整路径 | `E:\Code\campus-network-keepalive\campus_net_keepalive.py` |
| **起始于** | 脚本所在目录 | `E:\Code\campus-network-keepalive\` |

> ⚠️ **重要提示**：
> - 使用 `pythonw.exe`（而非 `python.exe`），可避免显示黑色控制台窗口
> - 所有路径必须是**绝对路径**
> - "起始于"字段必须填写，否则无法读取 `config.json`

**如何找到 Python 路径**：

```bash
# 在命令提示符中运行
where python
```

示例输出：

```
C:\Python39\python.exe
C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe
```

将 `python.exe` 改为 `pythonw.exe` 即可。

#### 步骤 5：高级设置（重要）

完成创建后，右键点击新建的任务 → **"属性"**，进行以下配置：

##### 5.1 常规选项卡

- ✅ **勾选"使用最高权限运行"**
  - 确保有权限修改网络设置
- ✅ **勾选"不管用户是否登录都要运行"**
  - 开机即启动，无需登录
- **配置**：选择"Windows 10"

##### 5.2 触发器选项卡

- 双击触发器 → **勾选"延迟任务时间"** → 设置为 **1 分钟**
  - 等待网络初始化完成后再启动

##### 5.3 条件选项卡

- ❌ **取消勾选"只有在计算机使用交流电源时才启动"**
  - 笔记本电脑使用电池时也能运行
- ❌ **取消勾选"如果计算机改用电池电源..."**

##### 5.4 设置选项卡

- ✅ **勾选"如果请求后任务还在运行，强行将其停止"**
- ✅ **勾选"如果此任务已经运行，以下规则适用："** → 选择 **"请勿启动新实例"**

#### 步骤 6：验证配置

1. 点击"确定"保存所有设置
2. 右键点击任务 → **"运行"**
3. 检查任务状态：
   - ✅ "状态"列显示"正在运行"
   - ✅ "上次运行结果"为 `0x0`（表示成功）

**故障排查**：

- 如果状态显示错误代码（如 `0x1`），检查：
  1. Python 路径是否正确
  2. 脚本路径是否正确
  3. "起始于"目录是否存在
  4. `config.json` 是否在脚本同级目录

#### 步骤 7：测试重启

重启电脑，观察以下行为：

1. ✅ 开机约 1 分钟后，任务自动运行
2. ✅ 任务管理器中能看到 `pythonw.exe` 进程
3. ✅ 能够正常访问外网（自动登录成功）

---

## 查看运行日志

由于使用 `pythonw.exe` 后台运行，无法直接看到控制台输出。建议启用日志文件：

修改 `config.json`，添加日志配置：

```json
{
  "username": "20210001",
  "password": "YourPassword",
  "login_url": "http://1.1.1.3/ac_portal/login.php",
  "check_interval": 60,
  "log_level": "INFO"
}
```

然后在任务计划程序中修改"添加参数"为：

```
campus_net_keepalive.py > keepalive.log 2>&1
```

日志将保存到 `keepalive.log` 文件中。

---

## 补充：技术细节

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

| 方式 | 目标 | 超时 | 优先级 | 优点 |
|:----:|:----:|:----:|:------:|:----:|
| DNS Ping | 223.5.5.5<br>8.8.8.8 | 3s | 🥇 高 | 快速、不消耗流量 |
| HTTP 请求 | baidu.com | 5s | 🥈 中 | 准确检测劫持 |

### 指数退避重试

避免频繁请求对网关造成压力：

| 重试次数 | 延迟时间 | 累计等待 |
|:-------:|:-------:|:-------:|
| 第 1 次 | 立即 | 0s |
| 第 2 次 | 5s | 5s |
| 第 3 次 | 10s | 15s |
| 第 4 次 | 20s | 35s |
| 第 5 次 | 40s | 75s |

---

## 重要：故障排查

### 问题 1：提示"Configuration file not found"

**原因**：未创建 `config.json`

**解决**：

```bash
copy config.json.example config.json
```

然后编辑 `config.json` 填写账号密码。

### 问题 2：提示"Placeholder values in configuration"

**原因**：`config.json` 中仍使用模板占位符

**解决**：检查以下字段是否已修改为真实值：

```json
{
  "username": "your_student_id",  // ← 需要修改
  "password": "your_password"     // ← 需要修改
}
```

### 问题 3：任务计划程序中任务无法运行

**检查清单**：

- [ ] Python 路径是否正确（使用 `where python` 查看）
- [ ] 脚本路径是否使用绝对路径
- [ ] "起始于"字段是否填写
- [ ] 是否勾选"使用最高权限运行"
- [ ] `config.json` 是否在脚本同级目录

### 问题 4：登录失败，提示"HTTP 404"

**原因**：登录接口地址可能不同

**解决**：

1. 打开浏览器开发者工具（F12）
2. 访问 `http://1.1.1.3` 并手动登录
3. 在 Network 标签中查看实际的登录请求 URL
4. 修改 `config.json` 中的 `login_url`

---

## 配置参数说明

`config.json` 完整参数列表：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:----:|:----:|:----:|:------:|:----:|
| `username` | string | ✅ | - | 学号/一卡通号 |
| `password` | string | ✅ | - | 密码 |
| `login_url` | string | ✅ | - | 登录接口地址 |
| `check_interval` | int | ❌ | 60 | 网络检测间隔（秒）|
| `max_retry` | int | ❌ | 5 | 最大重试次数 |
| `retry_base_delay` | int | ❌ | 5 | 重试基础延迟（秒）|
| `dns_servers` | array | ❌ | ["223.5.5.5", "8.8.8.8"] | DNS 服务器列表 |
| `http_check_url` | string | ❌ | "http://www.baidu.com" | HTTP 检测 URL |
| `dns_timeout` | int | ❌ | 3 | DNS Ping 超时（秒）|
| `http_timeout` | int | ❌ | 5 | HTTP 请求超时（秒）|
| `log_level` | string | ❌ | "INFO" | 日志级别（DEBUG/INFO/WARNING/ERROR）|

---

## 停止守护进程

### 方法 1：任务计划程序（推荐）

1. 打开任务计划程序
2. 找到"校园网自动登录"任务
3. 右键 → **"结束"**

### 方法 2：任务管理器

1. 打开任务管理器（`Ctrl+Shift+Esc`）
2. 切换到"详细信息"标签页
3. 找到 `pythonw.exe` 进程
4. 右键 → **"结束任务"**

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT License 开源，详见 [LICENSE](LICENSE) 文件。

---

## 致谢

- 感谢校园网管理团队提供稳定的网络服务
- 本项目仅用于学习和研究目的，请合理使用

---

## 联系方式

- **Issues**：[GitHub Issues](https://github.com/your-lab/campus-network-keepalive/issues)
- **Email**：your-email@example.com

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

