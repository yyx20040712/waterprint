# 智水蓝图（WaterPrint）monorepo

污水处理工艺设计计算平台：计算内核（纯 Python）+ FastAPI 服务 + React 前端。

> 当前状态：**C 批一期「主题骨架」收官（2026-09-10）——M4/M5 功能主体
> 与后续四批之上，webapp 观感与体验面开工**。功能底盘（2026-09-09
> M4/M5 收官）：计算面三线 32/32 单元四件套（UF-32 对照表 507 键）+
> 布置编辑器（边界红线+间距校核黄红标示，L4）/全厂总图与单单元 CAD
> 图纸（DXF）/高程纵断面图链（PROFILE1~3）/概算书与审计报告导出/
> IFC 全厂模型导出/服务端批量导出任务面（SVRB2）/DWG 转换挂点（ODA
> 边车，可选）/三维场景与画布 webapp/下载端点（路径安全双闸）/鉴权
> 与 SSE 限流（可配置）。后续四批：B2 全界面中文化（单元库/参数面板
> /方案表中文列头）；FD 可行域引导（93 连续参数 1D 区间条+2D 热力图
> +可行域点击回填吸附）；**C1 主题骨架（方向 A「深海工程台」用户裁选
> ——antd v6 全量 token 定制+global.css 全库首个 CSS 底座+滚动容器
> 重构[整页滚动越界根治]+顶栏品牌区/项目徽章/底部状态栏；方向 A
> 两方向视觉稿经 glm-5.3-flash 三轮看图评审后呈裁）**；D/A 双审管道
> 常态化（每批 Kimi 一审+deepseek 二审+R 轮处置）。**C2 首子面已收官
> （方案表标签重制：列宽策略/固定首尾列/表头两行制吸顶/数值 3 位
> 小数千分位+悬浮全精度/固定列名中文/语义色 token 收敛——D Kimi
> 0 Important+A deepseek 有条件通过+R 轮六处置束）**；**C2 第二
> 子面已收官（画布标签重制：节点域色象形卡片+左域色条+选中鎏金
> +连线水/泥两色着色+图例+MiniMap+缩放工具条+深蓝点阵底+满高
> +兜底布局 S 形折行——无头断言 11/11）**；**C2 第三子面已收官
> （参数面板表单化：单行 field+field_id 隐藏[用户裁选]+单位入控件
> +grid 档位 chips 回填+foot 常驻提交/重置+侧栏拖拽把手[240~480
> 用户裁选]+声明面悬浮[用户裁选]——无头 12/12+用户呈裁应答三增量
> 落地）**；**C2 第四子面已收官（单元库图标行重制[原拟两列结构——
> 呈裁改判码不显示]+选中联动水蓝光环[「仅光环」用户裁定·挂账并入]
> +foot 计数条——glm 设计五轮+实现态三轮收敛+用户四点应答；无头
> L 族 12/12+三族回归零回归）**；**C2 第五子面已收官（三维空旷
> 议题：地面工程网格+雾边融/光影档/中文名标签/取景微调/单元间高架
> 管廊[core 扩面 scene-6 两色制]——glm 四轮+无头 T 族 8/8+锁面 264 键；
> D 一审有条件通过[R 轮七处置]+A 二审规格符合放行[R2 轮四修一反驳]）**；
> **C2 第六子面已收官（节点 3D 缩略图②：96×96 离屏舞台[node_id 首段
> 分组+V4 取景/光比口径复用+顺序 rAF 队列]+节点卡片 44×44 双态回退
> 象形+TASK_EVENT scene 失效第六监听——无头 thumb 族 13/13+D 一审
> [GD-01 Important R 轮真修+T7 实证]/A 二审[R2 轮 GD-N-01~06 处置]）**
> **+操作链 P0 已收官（P0-1 建项入口[F1/F3/F4-文案面：CTA Modal 两态
> +view.name 显示名+导入全链]+P0-2 方案应用深链死锁[F5：result unit_id/
> design_hash 扩源+回填 effect+应用三闸/漂移二次确认]——无头 21 断言
> 全过；op-chain-fix-plan v2 全文沿推荐；[HUMAN-LOCK] 251b706 沿册）**；
> **P0-3 画布编辑最小闭环已收官（F2 结构性大面：单元库双入口加单元
> [包单元={} 空参/内置={kind}——引擎 v1 单实例闸实装修正]+端口拖拽连线
> [规则判断唯一源=校验时点 core validate_design_structure 新正门——
> 边端点/端口在册/方向+流体三查]+✕/键盘删除级联清[边/site.structures/
> checked_units——D3 悬空防线]+编辑会话快照隔离[事件桥刷新零回流草稿]
> +校验 Alert 警告放行⑦甲+保存 dirty/toast+常驻提交计算⑥甲[F4 残余
> 根治]——无头 edit 族全过+五族回归；D 一审通过无 Important/A 二审
> R2 四修一反驳；[HUMAN-LOCK] cbcf1a3 沿册 265 键）**；
> **C2 视觉对照+缩略图迭代批已收官（方向 A 逐 token 对账：页签行
> 面板蓝 #12213a+下边框+8px 内距/主区 gutter 分策[内容流 16px+画布/
> siteplan 满铺]/泥线-鎏金-工程蓝全对齐零改+#434343 八处扫尾；缩略图
> 纵向对角半剖+waters 入图+192=2x+hover 悬浮大图 portal+亮度分源；
> P1 搭车 F6 枚举下拉过滤/showSearch/错误映射+F8 浮点归一+F9 摆放
> 横幅——v6 DOM 勘正[tabpane 包装层零命中]；视觉三段流闭环[glm 两轮
> +亲核修正→ds→glm 终裁「验收通过」]；无头 visual 族 17/17+八族回归；
> D 一审无 Important[A 二审 GV-N 全收口]）**。
> **剩余面**：纵断
> 真实站距与 L0 独立管底（专业精度，停档待裁决）/表尺寸 ODA E2E
> 验收与字体随附（用户承办）/软著申请与开源准备（用户目标）。工程面：
> 门禁 11 项（含 GR-21 弃用到期门禁，TD1）/GR-01~GR-41 治理规则/
> test-lock 265 键只读锁/快照四哈希锚。里程碑：M0 骨架→M1 内核→M2
> 四块→M3 三线战役→M4 工业化→M5 图纸面→B2/FD→C1 主题骨架→C2（进行中）。
> 数据面键计数基准（ENG3 2026-08-28 探针实测：load_coefficients/
> load_prices/templates manifest 装载正门）：coefficients 1.1.0（577 键）
> +unit_prices 1.0.0（81 键）+templates 1.1.0（3 模板）；norms 手算表
> 32 份（AI 起草+追认制，全部已追认——余 I3 已裁待回填/条号章级挂账）。
> 测试数/覆盖率以 CI 输出为准，文档不手写数字。

## 快速导览（新成员/AI 按此顺序阅读）

1. `AGENTS.md` —— 项目宪法（硬规则，CI 强制，违反即失败）
2. `../重写计划-技术路线与框架.md` —— 总体计划（架构、里程碑、风险、§20 执行记录；**本地工作区文件，仓库外**——克隆后此文件不在库内，总计划快照以本 README 与 `docs/` 为准）
3. `../AI辅助开发经验教训.md` —— 前车之鉴（本仓库所有规则的理由来源）
4. `docs/file-contracts.md` —— 逐文件职责表（新增/改名文件必须同步，CI 校验）
5. `docs/structure-graph.md` —— 结构图谱（谁依赖谁/调用链/32 单元业务身份，CI 校验）
6. `docs/business-logic.md` —— 业务逻辑规格（参数链/耦合归属/守恒点/可行解流程）
7. `docs/adr/` —— 已拍板决策（ADR-001~009）
8. 各源码文件头部的"规格说明"节 —— 实现该文件前必读，实现必须满足规格

## 一键命令（环境就绪后）

```bash
# Python 内核（需要 uv，见下方环境待办）
cd core && uv sync && uv run pytest          # 全量测试（含架构门禁测试）
uv run python ../scripts/run_gates.py        # 门禁脚本 11 项（清单见 scripts/run_gates.py——行数/契约头/弃用到期/占位符/乱码/只读/信任根/结构图谱/webapp/魔法数字/ruff）

# 前端（需要 pnpm，经 corepack 启用）
pnpm install && pnpm -C webapp dev

# 服务（默认只听 127.0.0.1:8000——对外绑定=WATERPRINT_HOST 显式覆盖）
cd server && uv sync && uv run python -m waterprint_server.main
```

## 部署（Docker 双容器）

一条命令起全栈（对外唯一入口=前端 nginx http://localhost:8080，`/api` 经
反代；server 8000 不发布宿主——安全口径见 deployment.md「安全红线」节，
项目/导出持久化卷）：`docker compose -f deploy/compose.yml up -d --build`。
前置、环境变量、冒烟清单与 FAQ 见 [`docs/deployment.md`](docs/deployment.md)。

> 本地开发用已装备的 `core/.venv`（46 个 wheel）与 `server/.venv`；`uv sync`
> 待网络恢复可生成锁文件后启用；测试入口 = 分包进入 `core/`、`server/`
> 目录运行（根目录聚合收集有已知 conftest 冲突）。

## 环境待办（M0 第 0 天）

- [x] ~~镜像源配置~~（已入库：uv 走阿里云源见两个 pyproject 的
      `[[tool.uv.index]]`；pnpm 走 npmmirror 见根 `.npmrc`——本机网络
      实测官方源断流，见下节）
- [x] ~~git 安装与 M0.5 入库~~（2026-08-22/23）
- [x] ~~uv 0.9.9 安装~~（wheel 直装，镜像索引异常绕过——见下节网络
      对策表；解释器版本见 `.python-version`，依赖以两个 pyproject 为准）
- [x] ~~pnpm 经 corepack 可用~~（pnpm@10.34.5，node-linker=hoisted
      应对 exFAT）
- [x] ~~推 GitHub + CI 全绿~~（github.com/yyx20040712/waterprint，
      CI 首跑 4/5 失败→修复批→run #12 五 job 成功；推送代理见下节
      网络对策表）
- [x] ~~uv.lock 生成与 CI frozen~~（core/uv.lock T7 期入库；server/
      uv.lock SERVER 批 2026-08-26 入库——两 job 均已 `--frozen`）
- [ ] Docker Desktop 推迟到 M4 部署阶段

### 网络状况与对策（2026-08-22 本机实测）

| 目标 | 现象 | 对策（已落地/待办） |
|------|------|--------------------|
| PyPI 直连（files.pythonhosted.org） | 读超时 / SSL EOF 断流 | 已入库 uv 阿里云镜像（两个 pyproject） |
| pnpm 官方 registry | 不稳 | 已入库 `.npmrc`（npmmirror） |
| GitHub push/clone | 计划 §11 R13 记录直连 ~1.5KB/s 频繁重置；本机实测系统代理（127.0.0.1:7890）可用 | 仅对 github.com 启用代理：`git config --global http.https://github.com.proxy http://127.0.0.1:7890`（不影响其他远程；代理关闭时删除该配置）；备选 SSH-443 |
| winget 源更新 | 偶发失败（需管理员修复 `winget source reset`） | 重试或离线包安装 |
| uv（rustls/native-tls）拉镜像 wheel | 间歇 TLS 断流，uv sync/lock 均不可用 | 本地依赖改 curl 拉 wheel + pip 离线装（会话工作区 fetch_deps.py）；CI 用 UV_DEFAULT_INDEX 官方源 |
| E 盘 exFAT | 不支持符号链接，pnpm 默认 linker 失败 | .npmrc node-linker=hoisted（本地/CI 同口径） |

## 目录

```
core/           计算内核（纯 Python，分层 L0~L4，见 docs/file-contracts.md）
server/         FastAPI 服务（routers → services → jobs）
webapp/         React 前端（feature 切片）
data/           版本化数据资产（单价/约束/系数/Excel 模板，全部带出处）
docs/           ADR、逐文件职责表、结构图谱、业务逻辑规格、规范摘录、测试说明
api-contracts/  OpenAPI 契约源（FastAPI 导出 → orval 生成前端客户端）
scripts/        CI 门禁脚本（纯标准库，无第三方依赖）
```

## 测试文件只读机制

`core/tests/` 与 `server/tests/` 下全部文件（含 golden 数据）为**只读**：
由 `scripts/lock_tests.py` 生成 `test-lock.manifest.json`（sha256 清单）并
设置只读属性（仅 Windows 本地；CI/Linux 由哈希校验承担内容完整性）；
`scripts/check_readonly.py` 与 `core/tests/arch/test_lock.py` 在本地和 CI
双重校验。修改测试 = 人类执行的显式解锁流程（见 AGENTS.md §7），AI 不得
改动测试文件与清单。
