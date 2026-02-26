# server-status-web

一个带登录鉴权的服务器状态面板（Docker 部署）。

## 功能
- 登录后查看：CPU、内存、磁盘、网络、运行时间
- 支持容器内运行
- 支持通过宿主机代理读取宿主机资源（避免只看到容器资源）

## 快速开始
```bash
cd /Users/pipidan/sandbox/server-status-web
cp .env.example .env
# 修改 .env 里的用户名/密码/密钥
docker compose up -d --build
```

访问：
- `http://127.0.0.1:18080/login`

## 默认端口
- 宿主机端口：`18080`
- 容器端口：`8080`

## 启用宿主机资源数据（推荐）
1. 在 `.env` 中设置：
```env
HOST_METRICS_URL=http://host.docker.internal:19100/api/host-status
HOST_METRICS_TOKEN=your-random-token
```

2. 启动宿主机指标代理：
```bash
cd /Users/pipidan/sandbox/server-status-web
./start-host-agent.sh
```

3. 重启容器：
```bash
docker compose up -d --build
```

页面会显示 `source=host-agent`，表示当前展示的是宿主机资源。

## 常用命令
```bash
# 启动/重建
docker compose up -d --build

# 查看日志
docker compose logs -f status-web

# 停止
docker compose down

# 启动/停止宿主机代理
./start-host-agent.sh
./stop-host-agent.sh
```
