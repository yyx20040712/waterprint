# canvas —— React Flow 工艺画布

节点画布：建图/连线/参数入口/自动布局（ADR-001）。产品核心交互。

## 文件规划（实装期创建，每个新文件先登记根 file-contracts.md）

| 文件 | 职责 |
|------|------|
| `components/CanvasFlow.tsx` | React Flow 画布容器（节点/边渲染注册） |
| `components/UnitNode.tsx` | 构筑物节点卡片（工程图例简笔轮廓 + 关键结果摘要一级可见） |
| `components/PortHandle.tsx` | 类型化端口（水蓝/泥棕/回流虚线——流体语义色） |
| `hooks/useConnectionRules.ts` | 连线规则（与 core contracts/ports.validate 同源：类型不匹配红色拒绝+原因） |
| `hooks/useAutoLayout.ts` | 自动布局（Ctrl+L，拓扑分层布局） |
| `store/canvasStore.ts` | zustand slice：节点/边/选中态（画布状态全经 store，StrictMode 安全 §11 R14） |
| `api/` | 经 shared/api 生成客户端调用（禁手写请求层） |

## 规格要点

- 节点 = 自包含 + 端口类型化；画布只管连接不管计算（Blender/n8n 契约借鉴）；
- 50+ 节点不掉帧（§19.4）；节点摘要显示当前工况结果（工况切换不改图）；
- 内置节点（市政输入/汇流/水质编辑）与单元节点同一渲染管线。
