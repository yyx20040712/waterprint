# app 层 —— 路由与 Provider 组合

**唯一允许组合 features 的层**（§13.5）。规则：features 互相禁止 import，
一切跨 feature 编排发生在本层。

## 文件清单（已创建；新文件先登记根 file-contracts.md 再建）

| 文件 | 职责 | 状态 |
|------|------|------|
| `App.tsx` | 应用布局壳（§19.2 骨架，见文件头规格） | 骨架屏可运行 |
| `providers.tsx` | Provider 组合：AntD ConfigProvider（深色默认）/ QueryClient | 规格冻结，接线期待实现 |
| `router.tsx` | 路由表：画布/三维（懒加载）/高程/图纸/概算 | 路由名冻结 |
| `ErrorBoundary.tsx` | 每 feature 一个边界的封装件 | 结构就位，上报待接线 |

## 交互规范基线（§19，实现期遵守）

- 深色主题默认、语义色纪律（绿合格/橙警告/红错误/蓝水线/棕泥线）；
- 键盘优先：F5 计算、Del 删除、Ctrl+L 自动布局、Ctrl+S 保存；
- 反馈三通道：即时（连线拒绝）/ 非阻塞（toast）/ 持久（诊断面板）。
