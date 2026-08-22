# params —— 参数与约束面板

选中对象的参数编辑 + 约束选择 + 假设清单查看（左侧面板，§19.2）。

## 文件清单（M0.5 结构接线已创建规格骨架；实装期填充实现，规格见各文件头）

| 文件 | 职责 |
|------|------|
| `components/ParamForm.tsx` | 参数表单（按 manifest 字段 ID 渲染；单位灰阶小字显示） |
| `components/ConstraintPicker.tsx` | 约束勾选（constraint_kb 条目 + UI 覆盖） |
| `components/AssumptionsPanel.tsx` | 设计假设清单（出处可见可改——core registry/assumptions 数据） |
| `store/paramsStore.ts` | 编辑态 slice（草稿/校验错误/脏标记） |
| `api/` | 生成客户端调用 |

## 规格要点

- 参数编辑走"草稿→校验→提交"：错误消息来自 core（字段路径级），
  禁前端自行复制校验规则（TS 侧零业务逻辑复制）；
- 输入单位换算在边界（core quantity.parse 语义）；显示单位可切换；
- 假设面板是"默认值显性化"的 UI 落点（§3 保证 7）。
