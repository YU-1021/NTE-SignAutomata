# 塔吉多（异环）自动签到脚本

塔吉多社区自动签到脚本，支持社区签到和游戏签到。

## 快速开始

### 第一步：获取 Token

1. 在本地 Windows 电脑上安装 Python（如果没有）
2. 安装依赖：
   ```bash
   pip install requests cryptography
   ```
3. 运行获取 Token 脚本：
   ```bash
   python get_token.py
   ```
4. 按提示输入手机号和验证码
5. 复制输出的 JSON 内容

### 第二步：配置青龙面板

1. 登录青龙面板
2. 点击左侧「环境变量」
3. 点击「添加变量」
4. 填写：
   - **名称**：`TJD_TOKEN`
   - **值**：粘贴上一步获取的 JSON 内容
5. 点击确定保存

### 第三步：添加定时任务

1. 点击左侧「订阅管理」→「新建订阅」
2. 填写以下信息：

| 字段 | 值 |
|------|-----|
| 名称 | 塔吉多签到 |
| 类型 | 公开仓库 |
| 链接 | `https://github.com/你的用户名/NTE-SignAutomata.git` |
| 定时类型 | crontab |
| 定时规则 | `2 2 28 * *` |
| 白名单 | `tjd_task_.+\.sh` |
| 文件后缀 | `sh` |

3. 保存后点击「运行」拉取仓库
4. 拉取成功后，定时任务列表会自动出现「塔吉多签到」任务

---

## 详细配置教程

### 一、青龙面板配置文件修改

**重要**：拉库前需要先修改青龙配置文件，否则无法识别 Shell 脚本。

1. 点击左侧「配置文件」
2. 找到 `RepoFileExtensions` 配置项
3. 修改为：
   ```
   RepoFileExtensions="js py sh"
   ```
4. 点击保存

### 二、拉库方式

#### 方式一：订阅管理（推荐）

1. 点击「订阅管理」→「新建订阅」
2. 按下表填写：

```
名称：塔吉多签到
类型：公开仓库
链接：https://github.com/你的用户名/NTE-SignAutomata.git
分支：main
定时类型：crontab
定时规则：2 2 28 * *
白名单：tjd_task_.+\.sh
文件后缀：sh
```

3. 保存后点击「运行」

#### 方式二：定时任务拉库

1. 点击「定时任务」→「添加任务」
2. 填写：
   ```
   名称：拉取塔吉多签到库
   命令：ql repo https://github.com/你的用户名/NTE-SignAutomata.git "tjd_task_"
   定时规则：2 2 28 * *
   ```
3. 保存后点击「运行」

### 三、环境变量配置

#### 单账号配置

1. 点击「环境变量」→「添加变量」
2. 填写：
   - 名称：`TJD_TOKEN`
   - 值：运行 `get_token.py` 获取的 JSON 内容
3. 保存

#### 多账号配置

每个账号一行，例如：

```json
{"refreshToken":"账号1token","uid":"xxx","deviceId":"xxx","gameId":"1289","roleIds":["xxx"]}
{"refreshToken":"账号2token","uid":"xxx","deviceId":"xxx","gameId":"1289","roleIds":["xxx"]}
```

或者直接用 refreshToken（简化格式）：

```
账号1的refreshToken
账号2的refreshToken
```

### 四、手动运行测试

1. 在定时任务列表找到「塔吉多签到」
2. 点击右侧「运行」按钮
3. 点击「日志」查看运行结果

---

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `TJD_TOKEN` | 是 | 账号 Token，运行 get_token.py 获取 |
| `TGD_ROLE_IDS` | 否 | 角色ID，多个用逗号分隔（不填则自动获取） |

---

## 定时任务说明

| 任务名 | 定时规则 | 说明 |
|--------|----------|------|
| 塔吉多签到 | `0 9 * * *` | 每天早上9点执行签到 |

---

## 常见问题

### 1. Python 未安装

脚本会自动检测并安装。如安装失败，手动执行：

**Debian/Ubuntu：**
```bash
apt-get update && apt-get install -y python3 python3-pip
```

**Alpine：**
```bash
apk add python3 py3-pip
```

### 2. 依赖安装失败

手动安装：
```bash
pip3 install requests cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Token 失效

重新运行 `get_token.py` 获取新 Token，更新青龙环境变量。

### 4. 拉库后没有任务

检查配置文件中 `RepoFileExtensions` 是否包含 `sh`。

### 5. GitHub 拉取失败

使用国内加速代理，在仓库地址前添加：
```
https://gh-proxy.com/https://github.com/你的用户名/NTE-SignAutomata.git
```

---

## 项目结构

```
NTE-SignAutomata/
├── qinglong/
│   ├── tjd_task_base.sh    # 基础脚本
│   └── tjd_task_sign.sh    # 签到任务入口
├── get_token.py            # Token 获取工具（本地运行）
├── tjd_sign.py             # 签到主程序
├── requirements.txt        # Python 依赖
└── README.md
```

---

## 致谢

- [NTE-Auto-Sign-main](https://github.com/NTE-Auto-Sign-main) - 原始签到逻辑
- [BiliBiliToolPro](https://github.com/RayWangQvQ/BiliBiliToolPro) - 青龙脚本架构参考
