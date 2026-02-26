# 容器读取宿主机资源状态

## 为什么现在看到的是容器资源
- 容器内 `psutil` 默认读取容器自身 namespace/cgroup，不是宿主机。
- 在 macOS/Windows 的 Docker Desktop 上，容器运行在 Linux VM 里，无法直接读取宿主机内核指标。

## 当前项目可用方案（推荐）
- 在宿主机启动 `host-metrics-agent.py`（只监听 `127.0.0.1:19100`）。
- 容器通过 `host.docker.internal` 拉取宿主机指标。

### 1) 启动宿主机指标代理
```bash
cd /Users/pipidan/sandbox/server-status-web
export HOST_METRICS_TOKEN='replace-with-random-token'
export HOST_METRICS_BIND='127.0.0.1'
python3 host-metrics-agent.py
```

### 2) 给容器配置代理地址
编辑 `.env` 增加：
```env
HOST_METRICS_URL=http://host.docker.internal:19100/api/host-status
HOST_METRICS_TOKEN=replace-with-random-token
```

### 3) 重启容器
```bash
cd /Users/pipidan/sandbox/server-status-web
docker compose up -d --build
```

## Linux 宿主机补充
- Linux 可用 host PID + 挂载 `/proc` `/sys` 等方式直接读宿主机指标；
- 但在 Docker Desktop（macOS/Windows）不适用，仍建议用上面的代理方式。
