# params —— 参数与约束面板

选中对象的参数编辑 + 约束选择 + 假设清单查看（左侧面板，§19.2）。

## 文件清单（M0.5 结构接线创建骨架；FE5 批 6b 段三实装参数/假设两面）

| 文件 | 状态 | 职责 |
|------|------|------|
| `lib/designParams.ts` | FE5 实装 | 纯函数层：design 窄化门+draft 归一+脏比较+目录索引+假设合成行 |
| `lib/designParams.test.ts` | FE5 实装 | 五纯函数 node 测试（golden 内联节选+负例族） |
| `api/useUnitCatalog.ts` | FE5 实装 | 单元目录/假设清单查询薄封装（静态键） |
| `api/useProjectDesign.ts` | FE5 实装 | 项目 design 参数面查询（select 窄化；read 键 invalidate 面） |
| `components/ParamForm.tsx` | FE5 实装 | 参数表单：manifest 参数面+design 覆盖值→草稿→apply 提交重算 |
| `components/AssumptionsPanel.tsx` | FE5 实装 | 设计假设只读清单（DEFAULTS∪覆盖+覆盖标记；编辑挂账） |
| `components/ConstraintPicker.tsx` | 占位维持 | 约束勾选——数据通道待 constraint_kb 迁移批（D3：空槽+无读取端点） |
| `store/paramsStore.ts` | 占位维持 | 编辑态 slice——草稿态组件内 useState（单面板无跨组件态；zustand 首例留 canvas 编辑批） |

## 规格要点（FE5 批 6b 段三口径）

- 参数编辑走"草稿→提交"：draft 归一（string→number|null，null=禁提交态）
  与脏比较（design 覆盖 ?? manifest 默认为基准，等值不产空写）在
  `lib/designParams.ts` 纯函数收口；**前端零校验规则复制**（range/grid
  纯展示——range 无执行点，语义校验经 calc 任务 failed 回流挂账 solutions 批）；
- 提交通道=POST /api/calc/solutions/apply（服务端原子样板借用：merged.update
  →save→自动重算→失败回滚）；成功后 invalidate read 键
  （['/api/projects/&lt;id&gt;']——canvas/params/假设三面同步刷新）；
  params 专属端点归 server 批裁量挂账；
- 错误消息统一 WaterprintApiError.message 透出（422/404/409 归一面）；
- 假设面板是"默认值显性化"的 UI 落点（§3 保证 7）——21 条 registry 声明
  序只读+覆盖标记；覆盖编辑（design 态保存流程）挂账后续批；
- 工况面（checked_units/conditions/condition_mappings）无数据源出批挂账。
