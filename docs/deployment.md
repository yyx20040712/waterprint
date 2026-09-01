# 部署指南（Docker 双容器形态）

> 面向运维/演示场景的一条命令部署。开发态（本机 venv + vite dev）见根 README
> 「一键命令」；本文只管容器形态。compose 编排=`deploy/compose.yml`
> （server=FastAPI/uvicorn，webapp=nginx 承载前端静态产物并反代 `/api`）。

## 安全红线：暴露即全权

**API 零鉴权**：服务层 24 端点当前无任何鉴权（token/简易鉴权=R2 roadmap）——
能触达服务的主体即拥有全权：读改全部项目文件、提交任意计算（进程池满载
即 CPU 耗尽面）。因此：

- **容器形态**：server `8000` **不发布宿主**（compose 无 ports 直映——只在
  容器网桥内供 nginx 经服务名 `waterprint-server` 反代）；对外唯一入口=
  webapp `8080`，只应在**可信内网/防火墙后**暴露，禁止直接映射公网。
- **裸机/开发态**：`python -m waterprint_server.main` 默认只听 `127.0.0.1:8000`
  （settings `host` 字段）；改绑局域网地址（`WATERPRINT_HOST` 覆盖）=**显式
  信任决策**，须自行确认该网络面内全部主体可信。
- 调试需直连 API 时：`docker compose -f deploy/compose.yml exec server` 进
  容器内探（healthcheck 同路径），或临时加回 ports 映射——**用毕即撤**。

## 前置要求

| 项 | 要求 | 说明 |
|----|------|------|
| Docker Engine | 24+（含 BuildKit；本仓实测 29.7.2/WSL2） | `docker --version` 自查 |
| Docker Compose | v2+（`docker compose` 子命令；本仓实测 v5.5.0） | 旧版 `docker-compose` 独立二进制不在支持面 |
| 端口 | 8080（Web 入口，唯一对外端口）空闲 | 占用改法见 FAQ-1；server 8000 不发布宿主 |
| 网络 | 构建期需可达 PyPI 镜像（aliyun，pyproject 已配）与 npm 镜像（npmmirror，.npmrc 已配）；运行期零外部请求 | 产品约束：无出站依赖 |

## 一条命令起（从零到可用）

```bash
# 在仓库根目录执行（-f 为仓库根相对路径——子目录执行需换算路径）
docker compose -f deploy/compose.yml up -d --build
```

- 首次构建含全部依赖装配（预计 5~15 分钟，视网络；二次构建命中缓存秒级）；
- `webapp` 依赖 `server` 健康检查通过才启动（`depends_on: service_healthy`）；
- 就绪后入口=**http://localhost:8080**（`/api` 经 nginx 反代 server 容器——
  8000 不出容器网桥，见上文「安全红线」）。

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
| `WATERPRINT_DWG_CONVERTER_PATH` | （空=关） | ODA File Converter 可执行路径（可选 DXF→DWG；详见「导出格式」节） |
| `WATERPRINT_DWG_CONVERTER_TIMEOUT_S` | 100 | 单次 DWG 转换子进程超时秒（超时=跳过 DWG，DXF 照常交付） |

> 绑定面两字段 `WATERPRINT_HOST`/`WATERPRINT_PORT`（settings.py，裸机
> `python -m waterprint_server.main` 消费，默认 `127.0.0.1:8000`——只听
> 本地回环）容器内**不生效**：容器绑定由 Dockerfile CMD 旗标钉
> `0.0.0.0:8000`（nginx 跨容器反代所需），改绑=改信任面，见「安全红线」节。

覆盖例（compose 自定 env 或 `docker compose run -e`）：

```yaml
services:
  server:
    environment:
      WATERPRINT_CALC_WORKERS: 4
```

> 单进程契约（§16 A5）：`server` 服务**不可水平扩副本**（api replicas=1 +
  calc workers=N）——任务注册表在容器本地卷，多副本=互相失忆。

## 导出格式：DXF 默认与 ODA DWG 可选

**DXF 是默认且恒定的交付格式**（R2018/AC1032）。兼容基线（§12.5）：
AutoCAD 2018+、中望 CAD、浩辰 CAD 均原生打开 DXF R2018——不装任何
转换器即可完整使用本产品的导出功能。

**DWG 为用户自装可选**：若希望服务端在导出 DXF 的同时自动产出同名
并排的 DWG（`<产物名>.dxf` + `<产物名>.dwg`，产物列表双行登记），
需自行安装 ODA File Converter 并配置开关：

1. 从官方渠道下载安装：`opendesign.com/guestfiles/oda_file_converter`
   （Windows/Linux/mac 可执行件；**产品与镜像不分发该转换器**——下载
   与安装由用户完成，许可关系建立在用户与 ODA 之间）；
2. 许可证提示：ODA 官方 FAQ 明文「非 ODA 会员仅限非商业用途」——
   教学/科研/内网自用符合；对外收费交付或产品化分发前须自行评估
   （会员/商业 SDK 路线），本项目对此零许可风险（不分发零依赖）；
3. 配置开关：设置 `WATERPRINT_DWG_CONVERTER_PATH` 为转换器可执行
   文件完整路径（如 `C:\Program Files\ODA\ODAFileConverter 26.x\ODAFileConverter.exe`；
   Linux 容器内为挂载路径）。默认空=功能关闭，行为与未引入该功能
   完全一致。

**失败语义（不可破承诺）**：转换失败、超时（默认 100 秒，可经
`WATERPRINT_DWG_CONVERTER_TIMEOUT_S` 调整）或转换器路径失效时，
服务端记录 warning 日志（事件 `dwg_convert_skipped`）并**跳过 DWG**，
**DXF 产物照常生成与交付**——DWG 永远只是锦上添花，不阻塞导出链。

**适用形态**：自装主机（Windows/Linux 裸机或内网服务器）与内网部署
（转换器挂载进容器+设环境变量）。默认容器镜像**不含**转换器=默认关
（§12.7 许可证隔离原则——转换器属部署侧组件，不进基础镜像）。

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

1. **端口占用**：仅 webapp 发布宿主端口（8080）——改 `deploy/compose.yml`
   的 `ports` 左值（如 `"18080:80"`），或建 `deploy/compose.override.yml`
   覆盖；server 8000 不发布宿主，无占用面。
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
