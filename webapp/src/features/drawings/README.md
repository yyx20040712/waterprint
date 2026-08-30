# drawings —— 图纸预览与导出

DXF 图纸导出（下载/元数据预览+线稿渲染）+ 导出发起 + 图纸目录（FE9 批 6b 段七实装；B 批 Ruling B 落地线稿渲染 2026-08-30）。

## 文件清单（M0.5 骨架+FE9/B 批实装；规格见各文件头）

| 文件 | 职责 |
|------|------|
| `lib/drawingsView.ts` | 投影层：导出列表窄化门（ExportMeta 八字段值域拒→DrawingsViewError）+图纸目录行模型+工况选项投影+parseDisposition（node 纯函数） |
| `lib/drawingsView.test.ts` | 投影层 vitest（17 用例——窄化门正负例/行序=服务端序/工况索引面/文件名解析） |
| `lib/dxfScene.ts` | DXF→SVG 场景投影层（B 批 D2：dxf-parser 解析产物→path/text/solid 渲染模型纯函数——实体展开/Y 顶翻/extents 边距/ACI 色映射/DIMENSION 匿名块+INSERT 变换；解析残件包 DxfSceneError） |
| `lib/dxfScene.test.ts` | 投影层 vitest（10 用例——内联 fixture 四形态：基本投影+中文往返/Y 顶翻数值锚/extents 边距算术/ACI 正负例/块展开+INSERT 变换锚/DxfSceneError/1×1 空场景） |
| `components/DxfSvg.tsx` | 线稿渲染薄壳（B 批 D8：SvgScene→SVG 元素树，viewBox 自适应——零 antd/零运行期库，薄壳不测先例） |
| `components/DrawingPreview.tsx` | 图纸预览卡（元数据四行[FE9 保留面]+线稿渲染区三态[B 批 D7 重写]：scene→DxfSvg/sceneError→降级注记/皆空→绑定导出动作引导） |
| `components/SheetList.tsx` | 图纸目录清单（antd Table 元数据表：kind/工况/文件名/design 摘要/版本/stale 徽标；受控单选驱动预览） |
| `components/ExportButton.tsx` | 导出发起（单元/工况双 Select+导出动作：409 stale 二选一 Modal[force 重发 vs 先重算]+404「先提交计算」引导+501 原文透传+onExported 成功回调[B 批 D5 缝]） |
| `api/useExportsQuery.ts` | 三查询薄封装：导出列表（orval GET，显式 project_id）+工况源（cost 同端点同键缓存共享）+单元源（projects 同端点同键缓存共享） |
| `api/useUnitCatalog.ts` | 单元目录薄封装（UX1 D3：同键 ['/api/units'] 缓存共享——params 面先例同键不互 import；select 投影 builtin 集合供可投影面过滤判别，四 kind 值域零硬编码） |
| `api/useExportDxf.ts` | dxf 导出下载薄壳（手写 fetch POST 文件流——orval hook 返回 unknown 无 blob 面不消费；非 2xx→WaterprintApiError 同款归一；2xx→blob+anchor 下载+blob.text()→projectDxf→ExportDxfResult{fileName,scene,sceneError}[B 批 D4——解析失败不扰下载成功]+列表键失效） |
| `store/drawingsStore.ts` | 预览缩放/选中 slice（占位维持——v1 缩放=DxfSvg viewBox 自适应即足，store 启用记挂账） |

## 规格要点

- 预览消费 DXF 的纯投影渲染（禁止前端重建制图逻辑）——**B 批已实装（Ruling B 2026-08-30 用户拍板前端渲染库路径）**：dxf-parser@^1.1.2 唯一新依赖（+传递 loglevel），导出 blob 直接喂解析器（useExportDxf 成功面顺手 projectDxf——零契约改动，E 冻结 §四唯一路径：无按文件 GET 端点，行选中重取需契约扩展出局记档）；
- 线稿渲染绑定导出动作（非行选中）：下载落盘先行，解析失败降级注记不扰下载（I-3 分级——预览是增强非门禁）；v1 全实线（dxf-parser 线型表 DASHED 缺失=解析器局限，引导注记诚实呈现）；文字尺寸=按图幅可读性放大（显示层裁量，dxfScene 头注记档）；
- 导出结果文件名/目录来自服务端（路径安全在 server 层；前端 Content-Disposition 解析仅显示层）；
- 批量出图走低优先级队列（§17.1），进度走 SSE（M5 批量面——前端 v1 只发单图请求）。
