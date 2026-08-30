# 部署指南（Docker 双容器形态）

> 面向运维/演示场景的一条命令部署。开发态（本机 venv + vite dev）见根 README
> 「一键命令」；本文只管容器形态。compose 编排=`deploy/compose.yml`
> （server=FastAPI/uvicorn，webapp=nginx 承载前端静态产物并反代 `/api`）。

## 前置要求

| 项 | 要求 | 说明 |
|----|------|------|
| Docker Engine | 24+（含 BuildKit；本仓实测 29.7.2/WSL2） | `docker --version` 自查 |
| Docker Compose | v2+（`docker compose` 子命令；本仓实测 v5.5.0） | 旧版 `docker-compose` 独立二进制不在支持面 |
| 端口 | 8000（API 直连）+ 8080（Web 入口）空闲 | 占用改法见 FAQ-1 |
| 网络 | 构建期需可达 PyPI 镜像（aliyun，pyproject 已配）与 npm 镜像（npmmirror，.npmrc 已配）；运行期零外部请求 | 产品约束：无出站依赖 |

## 一条命令起（从零到可用）

```bash
# 仓库任意目录执行（compose 文件路径显式给出，无需 cd deploy）
docker compose -f deploy/compose.yml up -d --build
```

- 首次构建含全部依赖装配（预计 5~15 分钟，视网络；二次构建命中缓存秒级）；
- `webapp` 依赖 `server` 健康检查通过才启动（`depends_on: service_healthy`）；
- 就绪后入口=**http://localhost:8080**（API 直连口 http://localhost:8000）。

## 数据卷

| 卷 | 挂载点 | 内容 | 生命周期 |
|----|--------|------|----------|
| `waterprint_wp-projects` | /app/projects | 项目文件（*.wp.json） | `down` 保留；`down -v` 删除 |
| `waterprint_wp-exports` | /app/exports | 导出产物+任务注册表 | 同上 |

数据包（coefficients/unit_prices/templates，9.5M）**打入镜像**不占卷——
版本化资产随镜像版本走，用户数据走卷，两者不混。

## 环境变量（WATERPRINT_ 前缀，均可覆盖）

容器内已钉的默认值（`deploy/Dockerfile.server` ENV）：

| 变量 | 容器默认 | 说明 |
|------|----------|------|
| `WATERPRINT_PROJECTS_DIR` | /app/projects | 项目文件根（卷挂载点） |
| `WATERPRINT_EXPORTS_DIR` | /app/exports | 导出产物根（卷挂载点） |
| `WATERPRINT_DATA_DIR` | /app/data | 数据包根（镜像内） |
| `WATERPRINT_CALC_WORKERS` | CPU 数−1 | 计算进程池大小 |
| `WATERPRINT_LOG_LEVEL` | INFO | 日志级别 |
| `WATERPRINT_LOG_FILE` | /app/waterprint-server.log | 结构化日志（JSON 行）落点 |
| `WATERPRINT_MAX_UPLOAD_MB` | 10 | 上传体积闸 |

覆盖例（compose 自定 env 或 `docker compose run -e`）：

```yaml
services:
  server:
    environment:
      WATERPRINT_CALC_WORKERS: 4
```

> 单进程契约（§16 A5）：`server` 服务**不可水平扩副本**（api replicas=1 +
  calc workers=N）——任务注册表在容器本地卷，多副本=互相失忆。

## 冒烟自检清单（部署后 2 分钟过一遍）

1. 前端：`curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/` → `200`；
2. API（经反代）：`curl -s http://localhost:8080/api/projects` → JSON 数组（空数组亦算过）；
3. 计算全链：新建/导入项目 → 提交全流程计算 → 任务状态到 `done`（前端任务面板
   或 `GET /api/calc/tasks/{task_id}` 轮询）——覆盖 uvicorn→进程池→数据包装载；
4. 日志：`docker compose -f deploy/compose.yml logs server | grep -i error` → 空；
   （结构化日志面：`docker compose -f deploy/compose.yml exec server \
   grep -c '"level":"error"' /app/waterprint-server.log` → `0`）
5. 收尾（演示环境保留数据则跳过）：`docker compose -f deploy/compose.yml down`
   （加 `-v` 连卷清场——**会删全部项目/导出，先确认**）。

## 常见问题（FAQ）

1. **端口占用**：改 `deploy/compose.yml` 的 `ports` 左值
   （如 `"18080:80"`），或建 `deploy/compose.override.yml` 覆盖。
2. **镜像构建慢/失败**：网络面——PyPI 走 aliyun（pyproject `[[tool.uv.index]]`
   已配）、npm 走 npmmirror（根 `.npmrc` + 容器内 `COREPACK_NPM_REGISTRY`），
   均为国内可达源；仍失败查代理是否劫持 mirrors 域名。
3. **查看日志**：运行面 `docker compose -f deploy/compose.yml logs -f server`；
   计算事件面（structlog JSON）`docker compose -f deploy/compose.yml exec server
   tail -n 100 /app/waterprint-server.log`。
4. **卷迁移**：`docker run --rm -v waterprint_wp-projects:/from -v $PWD:/to \
   alpine cp -a /from/. /to/projects-backup/`（导出卷同法）。
5. **重建不丢数据**：`up -d --build` 复用既有卷；只有 `down -v` 或
   `docker volume rm` 删数据。
6. **healthcheck 一直 starting**：`docker compose logs server` 看启动失败原因
   （常见=数据卷权限/配置非法 fail fast）。
7. **WSL2 原生 Docker（无 Docker Desktop）容器"约一分钟自灭"**：WSL2 会在
   最后一个会话结束约 60 秒后回收整个 VM（dockerd/容器随之全灭，表现为容器
   反复重启、`docker events` 历史被清空——本仓 2026-08-30 冒烟实测）。
   长驻方案三选一：保持一个 WSL 会话（`wsl -d <发行版> -- sleep infinity` 挂
   后台）；注册表 `vmIdleTimeout` 调大；或改用 Docker Desktop。

## 30 分钟部署演练口径（从零到可用）

| 步骤 | 动作 | 预期耗时锚 |
|------|------|-----------|
| 1 | 装好 Docker+compose，`docker --version` 过 | 已含则 0 分钟 |
| 2 | 克隆仓库（或解包发行目录） | ~1 分钟 |
| 3 | `docker compose -f deploy/compose.yml up -d --build` | 首建 5~15 分钟（缓存后 <1 分钟） |
| 4 | 等 healthcheck 转 healthy（`docker compose ... ps`） | ~1 分钟 |
| 5 | 冒烟清单 1~4 项 | ~2 分钟 |
| 6 | 建项目/导模板/跑一轮计算验收 | ~10 分钟 |

合计首建口径 ≈ 20~30 分钟；二次部署（缓存命中）≈ 5 分钟。
