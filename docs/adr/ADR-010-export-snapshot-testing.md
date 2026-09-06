# ADR-010：导出产物快照测试对象面规格（批 14 呈裁草案 2026-09-06）

- 状态：**Proposed（呈裁中）**——用户批复后随首样批转「已接受」
  （首样批=中批管道：设计→D 一审→A 二审→R 轮→锁窗→push）。
- 背景：三导出产物（Excel 计算书/DXF 图纸/审计报告 HTML）各自已有
  「同环境双跑字节同」自比对测试（`test_calcbook.py`/`test_audit.py`/
  `test_dxf_writer.py`），但该形态只能证实现内确定性，**锚不住跨版本
  回归**——依赖升级（openpyxl/ezdxf/syrupy）、渲染代码改动、模板变更
  导致的产物漂移会静默通过全部现有门禁。syrupy>=4.7 依赖已入册
  （core/pyproject dev 组）；`core/tests/snapshots/README.md`（M0 骨架
  期落盘，只读锁定）已预注规格：「计算书 Excel、DXF 图纸、审计报告
  HTML 的**内容哈希快照**锁定结构——任何输出变化必须显式
  `--snapshot-update` 并过审查；快照文件生成于本目录 `__snapshots__/`，
  不入锁定清单；接入节奏 M1（calcbook 单单元）→M2（DXF 首批单元）→
  M4（审计报告）」。AGENTS.md L142 同面挂账：「快照回归挂账（暂无
  快照测试——R2D 2026-09-02 口径对齐现状；快照测试落地时改输出…」。
  三产物实现面均已就绪且确定性纪律在册（calcbook R4 字节确定性/
  audit R4 同迹树同字节/dxf_writer R3 ezdxf fixed-meta 开关）——
  接入条件齐备，对象面规格细节与锁面/流程协议由本 ADR 冻结。
- 决策（D1~D7）：

| # | 决策 |
|---|------|
| D1 | **对象面 v1=三产物**：计算书 xlsx（`render_calcbook`）、DXF 图纸（`write_dxf`）、审计报告 HTML（`render_audit_html`）。scene JSON/IFC 不入 v1：IFC C3 随附物系沿册挂账（不吸收防蔓延）；scene 导出通道定型后另批扩面（D1 口径=增量登记，非封闭清单） |
| D2 | **快照形态=内容哈希**（沿承 snapshots/README.md M0 预注，不再拆分级）：三产物渲染后统一取 sha256（`__snapshots__/*.ambr` 内快照值为十六进制哈希）。二进制产物（xlsx/dxf）本无文本 diff 可读性；HTML 放弃全文文本快照（AMP 全文体积大且与 `test_audit` 结构断言面重叠）——哈希=唯一诚实且三面同构的形态。限界知情接受：哈希快照漂移时无内嵌诊断力，定位依赖既有单面测试+双跑测试+人工 diff 两产物 |
| D3 | **落位**：测试文件 `core/tests/snapshots/test_snapshots.py`；快照文件 `core/tests/snapshots/__snapshots__/test_snapshots.ambr`。镜像规则（arch/test_structure `test_mirror_rule`）单向扫描源→测试，新测试文件不违约（实测核过规则实现）；snapshots/ 目录 M0 已建且 README 预注 |
| D4 | **锁面协议**：测试文件新增加入锁定清单=授权锁窗内 `lock_tests.py` 显式重锁（221→222 键，[HUMAN-LOCK] 流——B15/B16 先例形态：用户呈批授权 AI 代锁+独立锁笔 commit）。快照文件 `__snapshots__/` 已在 M0 预置豁免（`check_readonly.py` IGNORED_DIR_NAMES 第 44 行实测在册）——不入锁、不被拦，更新走 `--snapshot-update`+人审 diff（README 预注「与只读测试的人类解锁流程互补」口径沿承） |
| D5 | **输入源纪律**：渲染输入=版本化数据——项目/迹树来自 `golden_data_dir` fixture（conftest session 级，golden_data 与测试同锁）；计算书模板沿用 `test_calcbook` 现行测试内最小模板同源形态（正式模板归 data/templates 录入批 UF-16 挂账，正式模板录入时随 D7 漂移流重录快照）。禁运行时随机/时钟/字典序不稳定输入（三产物自身确定性纪律 R3/R4 为前提） |
| D6 | **与既有测试分工**：双跑字节同测试（自证确定性）全数保留；快照=跨版本回归锚（他证回归）。正交不互替、不合并——快照测试文件引用现有 fixture 而不动现有锁定测试 |
| D7 | **漂移处置流**：快照红≠自动更新。先人审 diff 定性：①预期漂移（依赖升级批/渲染有意改动/模板录入）→ 走 `--snapshot-update` 重录+diff 审查入批注记+AGENTS.md L142 挂账条同步回改；②非预期漂移=回归缺陷→ R 轮修复，禁改快照遮蔽。宪章面：AGENTS.md「快照回归挂账（暂无快照测试）」条随首样批改写为现行口径（同笔律） |

- 呈裁问题：
  - **Q1** 对象面三件（xlsx/DXF/HTML）+scene/IFC 不入 v1 是否认可？
  - **Q2** 哈希快照统一形态（放弃 HTML 全文文本快照——D2 限界知情接受）是否认可？
  - **Q3** 首样批复后是否即刻进入中批管道（测试件+ambr 初版+重锁 221→222+testing.md 增节+README snapshots/ 行升实链+AGENTS.md L142 回改）？
- 后果：每次 openpyxl/ezdxf/syrupy 依赖升级或渲染面改动=一次快照人审义务（新增人审成本，换取跨版本回归防线——静默漂移面归零）；testing.md 增节与 core/tests/README.md snapshots/ 行升实链随首样批同笔；mypy/ruff/门禁面零新增豁免（测试文件常规纪律）。
- 细化归属（首样批 DoD）：test_snapshots.py 三用例（每产物一用例，红绿纪律——先以临时错值证红）；ambr 初版三哈希；锁窗重锁 221→222；testing.md「快照回归」节；README/AGENTS 回改双件；全套门禁+CI 8/8。
