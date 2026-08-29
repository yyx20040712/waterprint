# canvas —— React Flow 工艺画布

节点画布：建图/连线/参数入口/自动布局（ADR-001）。产品核心交互。

> 当前状态：**FE4 段一只读渲染实装完成（2026-08-29）**——design 工艺图
> （GET /api/projects/{id} 弱类型 JSON）经投影层纯函数 `lib/projectFlow`
> （D6 窄化门逐类显式拒+D3 layout 优先/拓扑兜底确定性布局+D1 方向中性
> 端口+recycle 虚线）→ `components/CanvasFlow` React Flow 只读渲染
> （UnitNode 卡片+PortHandle 灰阶端口+fitView），`app/canvasPane.tsx`
> 默认标签首屏直渲染（URL `?project=` 单一真相+空态项目下拉+
> ErrorBoundary 隔离）；vitest 28 用例（golden municipal_34760 内联
> 全量节选+负例族）。
> **挂账六面（FE4 段二+）**：
> ① 编辑面（节点增删/拖线/参数面板——`canvasStore` 编辑态入 store）；
> ② 连线规则（`useConnectionRules` 与 core ports.validate 同源——待
> server 单元清单端点）；③ 自动布局交互（`useAutoLayout` Ctrl+L）；
> ④ 端口流体色（水蓝/泥棕）+端口表——数据源=server 单元清单端点
> （另批立项）；⑤ 中文单元名映射+节点结果摘要（D2，与 ④ 同源端点）；
> ⑥ 布局写侧（拖拽位置持久化回 view.layout）。

## 文件清单（FE4 段一实装；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectFlow.ts` | 投影层纯函数（design JSON→React Flow nodes/edges：D6 窄化门/D3 布局/D1 端口方向聚合+recycle 虚线——零运行期库 import） |
| `lib/projectFlow.test.ts` | 投影层 vitest（node 环境 28 用例：版本轻门/形状逐类拒/悬空边/kind 徽标/端口聚合/虚线/布局优先与兜底确定性） |
| `components/CanvasFlow.tsx` | React Flow 画布容器（只读渲染：nodeTypes 注册/fitView/colorMode=dark/投影错误薄壳） |
| `components/UnitNode.tsx` | 节点卡片（unit_id 等宽字体+内置 kind 徽标+左右方向端口排布——D2/D1） |
| `components/PortHandle.tsx` | 方向端口渲染件（target=Left/source=Right 灰阶中性色 Handle 封装——流体色挂账） |
| `hooks/useConnectionRules.ts` | 连线规则（骨架维持——段二实装，与 core contracts/ports.validate 同源） |
| `hooks/useAutoLayout.ts` | 自动布局（骨架维持——段二实装，Ctrl+L 拓扑分层） |
| `store/canvasStore.ts` | zustand slice（骨架维持——只读批无编辑态；服务端数据不进 store §17.2） |
| `api/useProjectQuery.ts` | 项目文件查询（orval hooks 消费封装：useReadProject…Get 薄壳） |

## 规格要点

- 节点 = 自包含 + 端口类型化；画布只管连接不管计算（Blender/n8n 契约借鉴）；
- 只读渲染面：design 数据投影唯一通道（服务端数据不进 store §17.2/D5），
  弱类型返回体在投影层窄化（D6 逐类显式拒——错误薄壳不白屏）；
- 50+ 节点不掉帧（§19.4）；节点摘要显示当前工况结果（工况切换不改图）
  ——摘要数据源挂账段二；
- 内置节点（市政进水/汇流/水质编辑/回流汇流）与单元节点同一渲染管线；
- 端口色=灰阶中性（§19.3 语义色之外禁彩色）——流体语义色挂账段二。
