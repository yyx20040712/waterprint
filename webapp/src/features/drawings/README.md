# drawings —— 图纸预览与导出

DXF 图纸导出（下载/元数据预览+线稿渲染）+ 导出发起 + 图纸目录（FE9 批 6b 段七实装；B 批 Ruling B 落地线稿渲染 2026-08-30）。

## 文件清单（M0.5 骨架+FE9/B 批实装；规格见各文件头）

| 文件 | 职责 |
|------|------|
| `lib/drawingsView.ts` | 投影层：导出列表窄化门（ExportMeta 八字段值域拒→DrawingsViewError）+图纸目录行模型+工况选项投影+parseDisposition（node 纯函数） |
| `lib/drawingsView.test.ts` | 投影层 vitest（17 用例——窄化门正负例/行序=服务端序/工况索引面/文件名解析） |
| `lib/batchExport.ts` | 批量出图纯函数层（M5 D4：buildBatchExportRequests 每单元恰一项[condition_key 透传+options.unit_id 单发面+空串归一+顺序保持]；dedupe 责任归调用方注记——零 antd/零运行期库 import；R2 G1-01 删 URL 死代码常量） |
| `lib/batchExport.test.ts` | 批量出图 vitest（M5 D4：5 用例——空 units→[]/每单元恰一项纯数据逐请求/顺序保持/工况空串归一/重复项原样） |
| `lib/dxfScene.ts` | DXF→SVG 场景投影层（B 批 D2：dxf-parser 解析产物→path/text/solid 渲染模型纯函数——实体展开/Y 顶翻/extents 边距/ACI 色映射/DIMENSION 匿名块+INSERT 变换；解析残件包 DxfSceneError） |
| `lib/dxfScene.test.ts` | 投影层 vitest（10 用例——内联 fixture 四形态：基本投影+中文往返/Y 顶翻数值锚/extents 边距算术/ACI 正负例/块展开+INSERT 变换锚/DxfSceneError/1×1 空场景） |
| `components/DxfSvg.tsx` | 线稿渲染薄壳（B 批 D8：SvgScene→SVG 元素树，viewBox 自适应——零 antd/零运行期库，薄壳不测先例） |
| `components/DrawingPreview.tsx` | 图纸预览卡（元数据四行[FE9 保留面]+线稿渲染区三态[B 批 D7 重写]：scene→DxfSvg/sceneError→降级注记/皆空→绑定导出动作引导） |
| `components/SheetList.tsx` | 图纸目录清单（antd Table 元数据表：M5 序号列[index 派生 1..N]+kind/工况/文件名/design 摘要/版本/stale 徽标；受控单选驱动预览） |
| `components/ExportButton.tsx` | 导出发起（M5 单元多选[maxTagCount responsive/allowClear 自带形态]+工况选+导出动作三按钮：导出图纸 DXF[N=1 单发/N>1 客户端顺序循环批量——进度 info 原位更新+任一失败即停已成功计数入错]/导出模型 IFC[SC1 D7 恒单发]/导出全厂总图 DXF[M5 D5 default 型——ready 闸=工况选定+unit_id 空串=server bare POST]；409 stale 二选一 Modal[force 重发 vs 先重算]+404「先提交计算」引导+501 原文透传+onExported 成功回调[B 批 D5 缝]） |
| `api/useExportsQuery.ts` | 三查询薄封装：导出列表（orval GET，显式 project_id）+工况源（cost 同端点同键缓存共享）+单元源（projects 同端点同键缓存共享） |
| `api/useUnitCatalog.ts` | 单元目录薄封装（UX1 D3：同键 ['/api/units'] 缓存共享——params 面先例同键不互 import；select 投影 builtin 集合供可投影面过滤判别，四 kind 值域零硬编码） |
| `api/useExportArtifact.ts` | 产物导出下载薄壳 kind 泛化（SC1 D7 自 useExportDxf.ts 改名——手写 fetch POST 文件流 /api/exports/${kind}：orval hook 返回 unknown 无 blob 面不消费；非 2xx→WaterprintApiError 同款归一；2xx→blob+anchor 下载+缺省文件名后缀按 kind 映射[dxf→.dxf/ifc→.ifc]+dxf 面 blob.text()→projectDxf→ExportArtifactResult{fileName,scene,sceneError}[B 批 D4——解析失败不扰下载成功；ifc scene 恒 null]+列表键失效） |
| `store/drawingsStore.ts` | 预览缩放/选中 slice（占位维持——v1 缩放=DxfSvg viewBox 自适应即足，store 启用记挂账） |

## 规格要点

- 预览消费 DXF 的纯投影渲染（禁止前端重建制图逻辑）——**B 批已实装（Ruling B 2026-08-30 用户拍板前端渲染库路径）**：dxf-parser@^1.1.2 唯一新依赖（+传递 loglevel），导出 blob 直接喂解析器（useExportArtifact("dxf") 成功面顺手 projectDxf——零契约改动，E 冻结 §四唯一路径：无按文件 GET 端点，行选中重取需契约扩展出局记档）；SC1 起 ifc 模型导出无前端预览投影面（scene 恒 null 不猜）；
- 线稿渲染绑定导出动作（非行选中）：下载落盘先行，解析失败降级注记不扰下载（I-3 分级——预览是增强非门禁）；v1 全实线（dxf-parser 线型表 DASHED 缺失=解析器局限，引导注记诚实呈现）；文字尺寸=按图幅可读性放大（显示层裁量，dxfScene 头注记档）；
- 导出结果文件名/目录来自服务端（路径安全在 server 层；前端 Content-Disposition 解析仅显示层）；
- 批量出图=M5 D3 客户端编排形态（顺序循环 N 个单产物请求走即时 blob 面——零任务队列依赖、SSE/句柄消费零新增）；服务端批量任务面（无-unit dxf items 422 对偶拒绝挂账二期：SiteDesign 序列化通道+items per-unit 键位）。
