# JapanneseWebsite

全日文私域代购站（后端 Flask + 前端 Vue）。支持用户注册/登录、积分、管理员操作，以及 Mercari 内容代理展示。

## 技术栈
- 后端：Python 3 + Flask
- 前端：Vite + Vue 3
- 数据库：SQLite（默认，开箱即用）/ MySQL（通过环境变量切换）
- 缓存：Redis（不可用时自动回退到内存令牌）

## 目录结构
- `web/backend`：后端代码（Flask 蓝图：login/register/user/home/admin）
- `web/frontend`：前端代码（Vite + Vue）

## 快速开始（Windows PowerShell）
### 后端（默认 SQLite，无需安装数据库）
1. 创建并激活虚拟环境
```
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. 安装依赖
```
pip install -r requirements.txt
```
3. 启动后端（默认使用项目根的 `dev.db`）
```
python -m web.backend.app
```
访问健康检查：`http://127.0.0.1:5000/api/health`

4. 初始化数据库（可在 Admin 页触发；也可直接调用）
```
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/admin/init-db" -Method POST -Headers @{ "X-ADMIN-KEY" = "change-admin-key" } | Select-Object -Expand Content
```

### 切换到 MySQL（可选）
设置环境变量后重启后端（检测到 `MYSQL_HOST` 后，将自动改用 MySQL）：
```
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_DB="jp_site"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="你的密码"
python -m web.backend.app
```
也可直接提供完整连接串：
```
$env:SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:你的密码@127.0.0.1:3306/jp_site?charset=utf8mb4"
python -m web.backend.app
```

### 前端
1. 安装 Node（≥ 18），安装依赖并启动
```
cd web\frontend
npm install
npm run dev
```
打开：`http://localhost:5173`

## 账号与权限
- 测试管理员账号（仅测试环境）：用户名 `admin`，密码 `123456`
  - 首次登录会自动创建 `admin@local` 用户
  - 管理接口仍需请求头：`X-ADMIN-KEY: change-admin-key`（请修改为强随机值）
- 普通用户：在“新規登録”注册后使用邮箱+密码登录

## 主要接口
- `GET /api/health` 健康检查
- `POST /api/auth/register` 注册
- `POST /api/auth/login` 登录（返回 token）
- `GET /api/user/me` 我的信息（需 Bearer token）
- `GET /api/user/points` 积分与流水（需 Bearer token）
- `GET /api/home/proxy?path=/search?...` Mercari 代理
- 管理端：
  - `POST /api/admin/init-db` 一键数据库检查/建表
  - `POST /api/admin/points/adjust` 调整积分（需 `X-ADMIN-KEY`）

## 配置项（环境变量）
- 通用：`SECRET_KEY`、`ADMIN_API_KEY`
- 数据库：
  - 默认：SQLite 项目根 `dev.db`
  - 直连：`SQLALCHEMY_DATABASE_URI`
  - MySQL：`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_DB`、`MYSQL_USER`、`MYSQL_PASSWORD`
- Redis：`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`、`REDIS_PASSWORD`
- CORS：`CORS_ALLOW_ORIGINS`
- 外部服务：`MERCARI_BASE`

## 说明
- 首次启动会自动检查库与表，缺失时自动创建；MySQL 数据库不存在会自动创建库。
- 生产环境请移除硬编码管理员登录，并配置强随机的 `SECRET_KEY` 和 `ADMIN_API_KEY`。 