# canvas —— React Flow 工艺画布

节点画布：建图/连线/参数入口/自动布局（ADR-001）。产品核心交互。

> 当前状态：**C2-canvas 画布标签重制完成（2026-09-10）**——FE4 只读
> 渲染骨架之上九处置（task-C2-canvas-plan.md）：画布深蓝点阵底+满高
> （wp-dotgrid 消费+Tabs 满高链）+UnitNode 域色象形重制（左 3px 域色
> bar+24px Unicode 象形图标+中文名主标+unit_id 等宽副标+选中**鎏金**
> 描边）+连线两色着色（水蓝/泥棕+域分宽——渲染层聚合 catalog
> business_line，投影层零触碰除 R-1）+图例（线型三项+当前图域色点）
> +MiniMap（左下域色缩略）+缩放工具条（右下 Controls 三钮）+端口域色
> （挂账④兑现）+**R-1 兜底布局 S 形折行**（ceil(sqrt(波数)) 波/行——
> 双链横幅 fitView 缩成细带的根治）；无头断言 11/11。挂账④⑤本批兑现
> （数据源 /api/units——META1 已实装）。
> **挂账余面（编辑面族——FE4 段二+）**：
> ① 编辑面（节点增删/拖线/参数面板——`canvasStore` 编辑态入 store）；
> ② 连线规则（`useConnectionRules` 与 core ports.validate 同源）；
> ③ 自动布局交互（`useAutoLayout` Ctrl+L）；⑥ 布局写侧（拖拽位置
> 持久化回 view.layout）；⑦ 节点 3D 缩略图（需求②——推荐案 R3F
> 离屏 sprite 在册，呈裁挂账后续批）；⑧ 节点 kv 参数摘要行（代表
> 参数选择=领域知识面，与 margin_ 裕度同族）。

## 文件清单（FE4 段一实装+C2-canvas 重制；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectFlow.ts` | 投影层纯函数（design JSON→React Flow nodes/edges：D6 窄化门/D3 布局[波次分层+R-1 S 形折行]/D1 端口方向聚合+recycle 虚线——零运行期库 import） |
| `lib/projectFlow.test.ts` | 投影层 vitest（node 环境 32 用例：版本轻门/形状逐类拒/悬空边/kind 徽标/端口聚合/虚线/布局优先与兜底折行确定性） |
| `lib/unitGlyph.ts` | 象形图标+域色纯函数（32 unit_id+4 内置 kind → Unicode 字形；business_line → 节点域色/边流色两色制——C2-canvas P3/P4） |
| `lib/unitGlyph.test.ts` | 字形/域色 vitest（9 用例：32 键全枚举防漏+聚类抽样+回退 ▢+域色五值+流色三态） |
| `components/CanvasFlow.tsx` | React Flow 画布容器（只读渲染：nodeTypes 注册/fitView/投影错误薄壳+点阵底/满高/边着色聚合/图例/MiniMap/Controls——C2-canvas） |
| `components/UnitNode.tsx` | 节点卡片（域色象形图标+左域色 bar+中文名+unit_id 等宽副标+kind 徽标+鎏金选中态+域色端口——C2-canvas 重制） |
| `components/PortHandle.tsx` | 方向端口渲染件（target=Left/source=Right Handle 封装+可选域色描边——挂账④兑现） |
| `hooks/useConnectionRules.ts` | 连线规则（骨架维持——段二实装，与 core contracts/ports.validate 同源） |
| `hooks/useAutoLayout.ts` | 自动布局（骨架维持——段二实装，Ctrl+L 拓扑分层） |
| `store/canvasStore.ts` | zustand slice（骨架维持——只读批无编辑态；服务端数据不进 store §17.2） |
| `api/useProjectQuery.ts` | 项目文件查询（orval hooks 消费封装：useReadProject…Get 薄壳） |

## 规格要点

- 节点 = 自包含 + 端口类型化；画布只管连接不管计算（Blender/n8n 契约借鉴）；
- 只读渲染面：design 数据投影唯一通道（服务端数据不进 store §17.2/D5），
  弱类型返回体在投影层窄化（D6 逐类显式拒——错误薄壳不白屏）；
- 50+ 节点不掉帧（§19.4）；节点摘要显示当前工况结果（工况切换不改图）
  ——摘要数据源挂账（kv 行=领域知识面⑧）；
- 内置节点（市政进水/汇流/水质编辑/回流汇流）与单元节点同一渲染管线；
- 域色四色制（municipal 水蓝/sludge 泥棕/mine_water 青绿/conveyance
  钢灰蓝——unitGlyph 单源+global.css 变量轴同值双源）；连线两色制
  （任一 sludge 端→泥棕；改色红线=N 处联动——R-G3 清单见 global.css
  头注）；选中=鎏金
  （C1 变量轴既定意图）。
