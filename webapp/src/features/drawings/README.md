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
| `components/SheetList.tsx` | 图纸目录清单（antd Table 元数据表：M5 序号列[index 派生 1..N]+kind/工况/文件名/design 摘要/版本/stale 徽标；受控单选驱动预览；EXPD 操作列下载按钮[useExportDownload 行级 pending 仅当前行禁用——错误 message.useMessage 呈现沿 ExportButton 先例，成功零额外消息]） |
| `components/ExportButton.tsx` | 导出发起（M5 单元多选[maxTagCount responsive/allowClear 自带形态]+工况选+导出动作三按钮：导出图纸 DXF[N=1 单发/N>1 服务端批量任务——useExportBatch 单 body 提交]/导出模型 IFC[SC1 D7 恒单发]/导出全厂总图 DXF[M5 D5 default 型——ready 闸=工况选定+unit_id 空串=server bare POST]；409 stale 二选一 Modal[force 重发 vs 先重算]+404「先提交计算」引导+501 原文透传+onExported 成功回调[B 批 D5 缝]；B5 D2/D3——三按钮统一 in-flight 门[IFC loading 并入 batching]+进度 toast 内嵌 Progress 行内条[duration=0 持有+终态 destroy 销毁]+挂 BatchStatusLine 常驻回溯行） |
| `components/BatchStatusLine.tsx` | 批量任务常驻状态行（B5 D3——deepseek 体验质疑采纳：导出按钮旁「最近一次批量任务」三态回溯[进行中 percent·i/N｜完成 N 项｜失败 kind·unit·原因；取消=已产计数行]；文案派生单源=useExportBatch.batchStatusText 纯函数 node 直测，antd 薄壳不测先例；色调 Typography type 映射） |
| `api/useExportsQuery.ts` | 三查询薄封装：导出列表（orval GET，显式 project_id）+工况源（cost 同端点同键缓存共享）+单元源（projects 同端点同键缓存共享） |
| `api/useUnitCatalog.ts` | 单元目录薄封装（UX1 D3：同键 ['/api/units'] 缓存共享——params 面先例同键不互 import；select 投影 builtin 集合供可投影面过滤判别，四 kind 值域零硬编码） |
| `api/useExportArtifact.ts` | 产物导出下载薄壳 kind 泛化（SC1 D7 自 useExportDxf.ts 改名——手写 fetch POST 文件流 /api/exports/${kind}：orval hook 返回 unknown 无 blob 面不消费；非 2xx→WaterprintApiError 同款归一；2xx→blob+anchor 下载+缺省文件名后缀按 kind 映射[dxf→.dxf/ifc→.ifc]+dxf 面 blob.text()→projectDxf→ExportArtifactResult{fileName,scene,sceneError}[B 批 D4——解析失败不扰下载成功；ifc scene 恒 null]+列表键失效） |
| `api/useExportBatch.ts` | 批量导出任务 hook（SVRB D6②：单 body POST→句柄 task_id→GET 兜底→SSE 订阅至终态 outcome[files/failures/error]+列表失效；自建 EventSource 同款复制——features 互不 import 门禁；B5 D3/D4——progress 透传原始 percent+lastOutcome 最近终态[BatchStatusLine 消费源]+sourceRef 覆盖前 close 旧流+batchStatusText 状态行文案单源纯函数） |
| `api/useExportDownload.ts` | 产物下载 hook（EXPD：手写 fetch GET /api/exports/${encodeURIComponent(file_name)} 文件流——orval 对应 GET hook 无 blob 通道不消费仅契约同步存在；Bearer 条件注入[getApiToken 非空才带——空态不发空头，仅新 hook 修复 M5 鉴权缺口旧面挂账]；非 2xx→WaterprintApiError 同款归一；2xx→blob+parseDisposition 文件名+saveBlob anchor 薄壳不测；行级 pendingFileName——成功零额外消息） |
| `store/drawingsStore.ts` | 预览缩放/选中 slice（占位维持——v1 缩放=DxfSvg viewBox 自适应即足，store 启用记挂账） |

## 规格要点

- 预览消费 DXF 的纯投影渲染（禁止前端重建制图逻辑）——**B 批已实装（Ruling B 2026-08-30 用户拍板前端渲染库路径）**：dxf-parser@^1.1.2 唯一新依赖（+传递 loglevel），导出 blob 直接喂解析器（useExportArtifact("dxf") 成功面顺手 projectDxf——零契约改动；B 批时点无按文件 GET 端点系 E 冻结 §四出局记档，EXPD 起已兑现 GET /api/exports/{file_name} 行级下载，注记注销）；SC1 起 ifc 模型导出无前端预览投影面（scene 恒 null 不猜）；
- 线稿渲染绑定导出动作（非行选中）：下载落盘先行，解析失败降级注记不扰下载（I-3 分级——预览是增强非门禁）；v1 全实线（dxf-parser 线型表 DASHED 缺失=解析器局限，引导注记诚实呈现）；文字尺寸=按图幅可读性放大（显示层裁量，dxfScene 头注记档）；
- 导出结果文件名/目录来自服务端（路径安全在 server 层；前端 Content-Disposition 解析仅显示层）；
- 批量出图=M5 D3 客户端编排形态（顺序循环 N 个单产物请求走即时 blob 面——零任务队列依赖、SSE/句柄消费零新增）；服务端批量任务面（无-unit dxf items 422 对偶拒绝挂账二期：SiteDesign 序列化通道+items per-unit 键位）。
