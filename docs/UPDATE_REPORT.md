# 更新报告：以线上为准同步与重启（2025-11-10）

本次操作目标：将本地仓库重指向并对齐到 `https://github.com/lijingpan/social-auto-upload` 的最新 `main`，随后重启后端与前端并验证接口。

## 摘要
- 已停止前后端并清理端口 `5409/5173`。
- 远端源重指向：`origin -> https://github.com/lijingpan/social-auto-upload`（移除个人仓库影响）。
- 本地 `main` 对齐到 `origin/main` 最新提交 `fe7bc16`。
- 修复配置缺陷：在 `conf.py` 增加缺失的 `_default_ai_timeout` 定义，使后端启动正常。
- 重新安装后端与前端依赖并重启服务（后端 5409、前端 5173）。

## 已执行命令
- 端口清理：`npx kill-port 5409 5173`
- 重指向远端：`git remote set-url origin https://github.com/lijingpan/social-auto-upload`
- 强制对齐：`git fetch --all --prune && git checkout -B main origin/main`
- 后端依赖：`python -m pip install -r requirements.txt`
- 前端依赖：`cd sau_frontend && npm ci || npm install`
- 启动后端：`python sau_backend.py`（监听 `http://127.0.0.1:5409`）
- 启动前端：`cd sau_frontend && npm run dev`（预览 `http://localhost:5173/`）

## 验证结果
- 前端页面：`http://localhost:5173/` 可正常打开，无启动错误日志。
- 后端接口：
  - `GET /getValidAccounts`：返回 `code=200`，有效账户列表正常。
  - `GET /getFiles`：返回 `code=200`，文件清单正常。
  - `POST /login`：返回 `405 Method Not Allowed`（路由方法未开放或需正确凭据）；不代表服务异常。登录请按实际流程和凭据进行。

## 使用说明（更新后）
- 启动后端：在项目根目录执行 `python sau_backend.py`，访问 `http://127.0.0.1:5409`
- 启动前端（开发）：`cd sau_frontend && npm run dev`，访问 `http://localhost:5173/`
- 再次“以线上为准”更新：
  - 对齐远端：`git fetch --all --prune && git checkout -B main origin/main`
  - 安装依赖：`python -m pip install -r requirements.txt && cd sau_frontend && npm ci || npm install`
  - 重启服务：按上述启动方式

## 注意事项
- 不自动推送到 GitHub。需要发布时，请在验证完成后手动 `git add/commit/push`。
- 固定端口：后端 `5409`、前端 `5173`。遇到冲突先执行端口清理。
- 配置项如 `AI_API_KEY` 建议通过环境变量传入，避免明文。

## TikTok 上传修复（Playwright 浏览器路径）
- 问题：`POST /postVideo` 触发 TikTok 上传时，Playwright 报错 `BrowserType.launch: Failed to launch: Error: spawn . EACCES`。
- 原因：当 `LOCAL_CHROME_PATH` 未设置或值不可执行时，代码无条件传入 `executable_path`，导致尝试以当前目录 `.` 作为可执行文件路径。
- 修复：`uploader/tk_uploader/main_chrome.py` 已改为仅在路径存在且可执行时传递 `executable_path`，否则回退到默认浏览器或系统 Chrome 渠道，避免 `spawn . EACCES`。
- 使用建议：
  - 如需使用系统 Chrome：在 shell 中设置 `export LOCAL_CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`（macOS 示例）。
  - 未设置时使用 Playwright 默认浏览器；首次使用可能需要安装浏览器：`python -m playwright install`（如只需 Chromium：`python -m playwright install chromium`）。
