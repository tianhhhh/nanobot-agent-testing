# nanobot-agent-testing

这是一个面向 [nanobot](https://github.com/HKUDS/nanobot) 的独立测试项目。第一版只保留 4 条 API 测试和 4 条 UI 测试，重点展示如何准备测试环境、管理 Mock、复用公共操作、生成报告以及在 GitHub Actions 中运行。

## 为什么单独建仓库

nanobot 自己已经有大量单元测试。本项目从使用者角度启动真实服务，再通过 HTTP 和浏览器访问它，主要检查“安装、配置、启动、请求、页面显示”能否连成完整链路。

项目默认使用本地 Mock 模型。Mock 会返回固定内容，因此测试不花模型费用，也不会因为真实模型每次回复不同而随机失败。

## 目录说明

```text
mocks/             固定回复的本地模型服务
pages/             页面操作，例如发送消息和上传附件
tests/api/         OpenAI 兼容 API 测试
tests/ui/          Playwright 浏览器测试
tests/conftest.py  创建临时配置，启动和关闭测试服务
utils/             API 请求的公共代码
```

## 环境要求

- Python 3.11 或更高版本
- 已安装包含 API 功能的 nanobot
- Chromium 浏览器由 Playwright 安装

本项目不会修改个人的 `~/.nanobot/config.json`。每次运行都会在 pytest 临时目录中创建配置和工作区。

## 本地安装

在当前 nanobot 源码环境中验证：

```powershell
cd D:\nanobot\nanobot-agent-testing
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m playwright install --no-shell chromium
```

如果单独克隆本仓库：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install "nanobot-ai[api]==0.3.0"
.\.venv\Scripts\python.exe -m playwright install --no-shell chromium
```

## 运行测试

运行全部测试：

```powershell
python -m pytest
```

只运行 API 或 UI：

```powershell
python -m pytest -m api
python -m pytest -m ui
```

调试 UI 时显示浏览器：

```powershell
python -m pytest -m ui --headed
```

运行前请确认 `8765`、`8900`、`9999` 和 `18790` 没有被其他程序占用。测试会自动启动 Mock、Gateway 和 OpenAI API，结束后自动关闭。

## 测试报告

- HTML 报告：`reports/report.html`
- 服务日志：`reports/logs/`
- UI 失败截图和 trace：`test-results/`

trace 可以这样打开：

```powershell
python -m playwright show-trace test-results/<trace文件>
```

## 代码为什么这样组织

- `conftest.py`：pytest 会自动加载这里的 fixture，适合统一准备和清理环境。
- `ApiClient`：统一管理地址、鉴权和超时，测试用例不用重复写请求细节。
- Page Object：只保存页面操作，测试文件保留清晰的业务断言。
- Mock：让回复稳定、免费、离线可运行。
- GitHub Actions：证明项目能从一个空白环境自动安装并执行。

项目没有创建 `BasePage` 或复杂的框架父类，因为当前只有两个小页面对象，过早抽象会让代码更难理解。

## 已知问题

两条从原 TypeScript 脚本迁移的回归场景记录在 [BUGS.md](BUGS.md)。只有在当前版本真实复现后才会标记为预期失败。

## 当前被测版本

- 本地源码验证：`HKUDS/nanobot` commit `7cede64f078f4435053f4a33964ea719ce582684`
- GitHub Actions：`nanobot-ai[api]==0.3.0`
- 本地完整结果：`7 passed, 1 xfailed`；`xfailed` 对应已确认的附件排序问题
