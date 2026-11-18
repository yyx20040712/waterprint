# validation —— 警告聚合视图

前端警告聚合切片（T3 批 2026-11-19）：消费 GET /api/calc/validation/{project_id}
响应的 warnings 聚合行（server services/validation 两源聚合投影——
docs/archive/warning-aggregation.md §1~§3 冻结规格；服务端已按
(scope,code,param_key) 聚合排序，客户端零去重零重排），三分区呈现
（声明级 ∅ 哨兵/工况聚合 ≥2/单工况直通）；v1 不消费 nodes 观测面
（用户定案）。输入=projectId（orval hook 薄封装+窄化门），输出=纯展示
面板（三分区 severity 徽标+message 全文+影响面·code·工况键 meta 行；
validation_available=false=降级提示条与源 B 警告行**并行**呈现——源 A
val 件缺席不吞服务端源 B 聚合面，零警告时仅降级条；空警告+有 val 件=
整体不渲染）；接线面=app/shellV4/analysisPane 全厂指标面（stale 横幅
后、出水指标前——违规面优先于指标阅读，错误局部呈现不阻断 compare
主面）。

## 文件清单

| 文件 | 职责 |
|------|------|
| `lib/validationView.ts` | 纯函数层：narrowValidationObservation 窄化门（顶层 11 键+warnings 行键域/severity 三值域逐项校验，非法抛 ValidationViewError）+partitionWarnings 三分区（§3：∅ 哨兵→声明级/≥2→工况聚合/单工况直通，服务端序稳定过滤）+severityTone/severityLabel 语义色与中文徽标+scopeLabel 影响面标签+conditionKeysText 工况键紧凑文案 |
| `api/useValidationQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/calc/validation/${projectId}']+select 窄化收口（useTrustQuery 同构先例；projectId null 禁用） |
| `components/WarningsPanel.tsx` | 警告聚合呈现件（纯展示薄壳）：三分区渲染（空分区不渲染）+降级条与源 B 警告行并行（源 A 缺席不吞聚合面）+空警告两态（薄壳 SSR 测） |
| `api/useValidationQuery.test.tsx` | 封装绑定测试（真 select 路径——仅替身 customInstance 取数面：合法→窄化产物/非法→ValidationViewError error 态/null 禁用零取数） |
