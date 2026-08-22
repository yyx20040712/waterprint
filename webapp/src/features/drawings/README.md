# drawings —— 图纸预览与导出

DXF 图纸预览（快照/PNG 预览）+ 导出发起 + 图纸目录。

## 文件规划（实装期创建，先登记 file-contracts.md）

| 文件 | 职责 |
|------|------|
| `components/DrawingPreview.tsx` | 图纸预览（SVG/canvas 线稿或服务端渲染位图，M2 定） |
| `components/SheetList.tsx` | 图纸目录（单体图/总图/纵断，含三元组摘要） |
| `components/ExportButton.tsx` | 导出发起（stale 守门：409 时弹"导出旧结果/先重算"） |
| `store/drawingsStore.ts` | 预览缩放/选中 slice |
| `api/` | 生成客户端调用 |

## 规格要点

- 预览消费 DXF 的纯投影渲染（禁止前端重建制图逻辑）；
- 导出结果文件名/目录来自服务端（路径安全在 server 层）；
- 批量出图走低优先级队列（§17.1），进度走 SSE。
