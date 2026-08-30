# drawings —— 图纸预览与导出

DXF 图纸导出（下载/元数据轻量预览）+ 导出发起 + 图纸目录（FE9 批 6b 段七实装）。

## 文件清单（M0.5 骨架+FE9 实装；规格见各文件头）

| 文件 | 职责 |
|------|------|
| `lib/drawingsView.ts` | 投影层：导出列表窄化门（ExportMeta 八字段值域拒→DrawingsViewError）+图纸目录行模型+工况选项投影（node 纯函数） |
| `lib/drawingsView.test.ts` | 投影层 vitest（13 用例——窄化门正负例/行序=服务端序/工况索引面） |
| `components/DrawingPreview.tsx` | 图纸元数据卡（D1 保守预裁：三元组摘要/engine/data 版本/stale 标注+「DXF 线稿渲染未实装」诚实注记——渲染形态待 Ruling） |
| `components/SheetList.tsx` | 图纸目录清单（antd Table 元数据表：kind/工况/文件名/design 摘要/版本/stale 徽标；受控单选驱动预览） |
| `components/ExportButton.tsx` | 导出发起（单元/工况双 Select+导出动作：409 stale 二选一 Modal[force 重发 vs 先重算]+404「先提交计算」引导+501 原文透传） |
| `api/useExportsQuery.ts` | 三查询薄封装：导出列表（orval GET，显式 project_id）+工况源（cost 同端点同键缓存共享）+单元源（projects 同端点同键缓存共享） |
| `api/useExportDxf.ts` | dxf 导出下载薄壳（手写 fetch POST 文件流——orval hook 返回 unknown 无 blob 面不消费；非 2xx→WaterprintApiError 同款归一；2xx→blob+anchor 下载+列表键失效） |
| `store/drawingsStore.ts` | 预览缩放/选中 slice（占位维持——FE9 选中态组件内 useState，FE5~FE8 先例同款） |

## 规格要点

- 预览消费 DXF 的纯投影渲染（禁止前端重建制图逻辑）——渲染形态（SVG/canvas/服务端位图）待 Ruling，渲染库属新依赖红线挂账；FE9 预览=元数据轻量面（过渡形态）；
- 导出结果文件名/目录来自服务端（路径安全在 server 层；前端 Content-Disposition 解析仅显示层）；
- 批量出图走低优先级队列（§17.1），进度走 SSE（M5 批量面——前端 v1 只发单图请求）。
