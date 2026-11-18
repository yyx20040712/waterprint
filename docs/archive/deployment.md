# 部署指南（Docker 双容器形态）

> 面向运维/演示场景的一条命令部署。开发态（本机 venv + vite dev）见根 README
> 「一键命令」；本文只管容器形态。compose 编排=`deploy/compose.yml`
> （server=FastAPI/uvicorn，webapp=nginx 承载前端静态产物并反代 `/api`）。

## 安全红线：入口语义（R2A 批1 修订）

**API token 鉴权（R2A 批1 起可用）**：服务层支持静态 Bearer token
（环境变量 `WATERPRINT_API_TOKEN`）——非空即对 21 端点生效（19 业务端点
仅认 `Authorization: Bearer <token>` 头；events 两 SSE 端点额外认
`?token=` 查询参数——EventSource 无法自定义头的现实通道）；`/api/units`、
`/api/assumptions`、`/api/constraints` 三静态只读端点豁免。**token 留空
（默认）= 鉴权关闭**，全部端点匿名可达——与升级前行为一致。因此：

- **红线是入口语义，不是绑定地址**：**任何经反代/端口映射对外可达的
  部署形态，无论 server 绑定地址，必须配置 token**。机器防线仅为
  best-effort（见下条），文档强制才是真红线。
- **机器防线（best-effort）**：token 为空且 `WATERPRINT_HOST` 不在回环
  集合 {127.0.0.1, ::1, localhost} 时，服务在启动期直接失败（fail fast，
  不留半启动态）。注意容器内绑定经 Dockerfile CMD 旗标（`--host 0.0.0.0`）
  不经该字段，此防线只覆盖裸机/开发态的 `WATERPRINT_HOST` 显式覆盖面。
- **token 强度要求**：非空 token 长度 ≥16（服务端启动校验；字母数字 62
  字符集 16 位 ≈4.8×10²⁸ 组合，为防暴力枚举的熵下界）。**推荐 32 位随机
  串**（如 `python -c "import secrets; print(secrets.token_hex(16))"`）。
  token 泄漏即全权——只应存在于服务端 env 与使用者的客户端配置中，禁止
  入库/入日志/入聊天渠道。
- **容器形态**：server `8000` **不发布宿主**（compose 无 ports 直映——只在
  容器网桥内供 nginx 经服务名 `waterprint-server` 反代）；对外唯一入口=
  webapp `8080`，只应在**可信内网/防火墙后**暴露，禁止直接映射公网。
  compose 经 env 插值透传 `WATERPRINT_API_TOKEN`（`.env` 或宿主环境变量
  提供）；healthcheck 已带同源 `Authorization` 头。
  **发版注记（破坏性变更）**：自 R2A 批1 起，compose 形态（容器内绑定
  0.0.0.0）**应视为强制配置 token 的破坏性变更**——升级现有部署时请
  同步设置 `WATERPRINT_API_TOKEN` 并向使用者分发；前端 Bearer 注入与
  设置页属 R2A 批2（本批服务端仅保证：token 未配=行为与升级前完全一致）。
- **裸机/开发态**：`python -m waterprint_server.main` 默认只听 `127.0.0.1:8000`
  （settings `host` 字段）；改绑局域网地址（`WATERPRINT_HOST` 覆盖）且未配
  token 将**直接拒绝启动**——这是上两条（显式信任决策+机器防线）的合流点。
- 调试需直连 API 时：`docker compose -f deploy/compose.yml exec server` 进
  容器内探（healthcheck 同路径同头），或临时加回 ports 映射——**用毕即撤**。

## 前置要求

| 项 | 要求 | 说明 |
|----|------|------|
| Docker Engine | 24+（含 BuildKit；本仓实测 29.7.2/WSL2） | `docker --version` 自查。批6h 实测注记（2026-09-27）：Docker 29 的 build CLI 已委派 buildx——`--no-buildkit` 旗标不存在（exit 125「unknown flag」）、`DOCKER_BUILDKIT=0` 亦仍走 BuildKit 前端=**classic builder 在现行工具链不可达**；Dockerfile.server 已全语法 classic 兼容化（COPY --chmod→COPY+RUN chmod，ENTRYPOINT 绝对路径 /app/ 钉死——旧守护进程可解析），部署按 BuildKit 内建引擎走即正常路径 |
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

数据包（coefficients/unit_prices/templates/constraint_kb，9.5M）**打入镜像**
不占卷——版本化资产随镜像版本走，用户数据走卷，两者不混。缺包启动校验
（`validate_data_packages`）覆盖双入口（R4 C-1 起，e2e-fix-round3
2026-09-25）：裸机 `python -m waterprint_server.main` 启动块+容器/运维
uvicorn 直启面 entrypoint 前置（`deploy/server-entrypoint.sh`——exec
uvicorn 前先校验，缺包或 manifest 空损=容器启动即以可执行文案退出、
healthcheck 永不转绿，非请求期 500 晚拒；卷遮蔽数据目录场景同受防护）。
残余边界：裸机 venv 内直接 `uvicorn waterprint_server.main:app`（不经
python -m 也不经 entrypoint）仍绕过校验——裸机部署请一律走
`python -m` 口径（根 README「一键命令」）；数据未就绪的空卷首启会因
校验拒绝而起不来（编排面 `depends_on: service_healthy` 将等待数据
就绪），请先备数据再起容器。

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
| `WATERPRINT_TYPST_PATH` | （空=PATH 发现） | typst CLI 可执行路径（B6 PDF 计算书导出引擎；空=服务进程 PATH 自动发现；详见「导出格式」节） |
| `WATERPRINT_TYPST_TIMEOUT_S` | 100 | 单次 PDF 编译子进程超时秒（超时=TypstCompileError 显式 500，PDF 未产出） |
| `WATERPRINT_API_TOKEN` | （空=鉴权关） | API Bearer token（R2A 批1：非空即 21 端点受保，≥16 位；**compose 插值透传自宿主 env/.env**——非 Dockerfile 钉值；强制口径见「安全红线」节） |

> 绑定面两字段 `WATERPRINT_HOST`/`WATERPRINT_PORT`（settings.py，裸机
> `python -m waterprint_server.main` 消费，默认 `127.0.0.1:8000`——只听
> 本地回环）容器内**不生效**：容器绑定由 Dockerfile CMD 旗标钉
> `0.0.0.0:8000`（nginx 跨容器反代所需），改绑=改信任面，见「安全红线」节。
>
> 裸机开发态语义注记（2026-09-30 补）：`WATERPRINT_DATA_DIR` 在裸机运行
> 时**只重定向数据包根**（coefficients/constraint_kb/templates/unit_prices
> 四包校验基点）；项目/导出产物根缺省仍按**工作目录相对路径**（projects/、
> exports/——与 `WATERPRINT_PROJECTS_DIR`/`WATERPRINT_EXPORTS_DIR` 显式
> 覆盖并存）。裸机隔离试验请同时设三个变量，勿只设 DATA_DIR 而误以为产物
> 也已隔离（实测踩坑记录：探针项目落进 server 运行目录）。

覆盖例（compose 自定 env 或 `docker compose run -e`）：

```yaml
services:
  server:
    environment:
      WATERPRINT_CALC_WORKERS: 4
```

> 单进程契约（§16 A5）：`server` 服务**不可水平扩副本**（api replicas=1 +
  calc workers=N）——任务注册表在容器本地卷，多副本=互相失忆。

> 重启语义（v1 明示——UF-26 闭项，批6f 2026-09-26）：服务重启后**不续跑
> 任何任务**。已落终态（done/failed/cancelled）的任务记录与结果经
> registry 落盘面恢复可查（TTL 保留窗内）；重启时仍在排队/运行的任务
> 自动转为 failed（错误类型 `InterruptedByRestart`——前端任务面板/
> 聊天失败横幅可见明细），幂等去重表不恢复——重新提交同名计算即新
> 任务；前端对失效任务 id 已有「重新提交」指引文案。多副本续跑=未来
> Redis 化路线（当前 ADR 不做）。

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

## 导出格式：PDF 计算书（Typst 引擎——部署依赖）

**PDF 计算书**（`POST /api/exports/report_pdf`）由 Typst 排版引擎编译产出
（A4/页眉页脚/页码/表格/数学公式）。该功能**要求服务主机安装 typst CLI**
（B6 计算说明批部署依赖申报——未安装时该端点返回 500 显式错误消息，其余
导出功能不受影响）：

1. Windows 主机推荐 winget 安装：`winget install Typst.Typst`——安装后
   可执行件位于
   `C:\Users\<用户>\AppData\Local\Microsoft\WinGet\Packages\Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe\typst-x86_64-pc-windows-msvc\typst.exe`
   （winget 包目录默认不进服务进程 PATH——新 shell 未继承时设
   `WATERPRINT_TYPST_PATH` 指向上路径，见 env 表）；
2. Linux/容器部署：从 `typst` 官方渠道安装（GitHub Releases 静态二进制
   或发行版包），可执行件在 PATH 即自动发现；
3. 路径解析三级序：`WATERPRINT_TYPST_PATH` 显式值 → 服务进程 PATH
   （`shutil.which("typst")`）→ 均缺=端点 500 显式消息（含安装指引）；
4. 字体面：PDF 内嵌 Times New Roman+SimSun——服务主机须具备两款系统
   字体（Windows 自带；Linux 容器需随镜像安装或映射字体目录）；
5. 失败语义：编译失败/超时（默认 100 秒，`WATERPRINT_TYPST_TIMEOUT_S`
   可调）=500 显式消息（stderr 摘要入消息）+临时文件零残留，不落半产物。

引擎中立申报：PDF 渲染器为「AST→排版源」接口的 Typst 实现（公式源=
sympy 表达式树单源双态打印机）；更换排版引擎（如 LaTeX 系 Tectonic）=
同接口另一渲染器实现，不影响计算说明书 AST 与 Markdown 通道。

## 冒烟自检清单（部署后 2 分钟过一遍）

1. 前端：`curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/` → `200`；
2. API（经反代；`$WATERPRINT_API_TOKEN` 为部署时设定的 token，未配则置空）：
   `curl -s -H "Authorization: Bearer $WATERPRINT_API_TOKEN"
   http://localhost:8080/api/projects` → JSON 数组（空数组亦算过；SSE 调试可
   改用 `?token=` 查询通道）；
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
