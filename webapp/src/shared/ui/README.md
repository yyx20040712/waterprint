# shared/ui —— 基础组件与主题

AntD 5 深色主题（dark algorithm + 设计 token）与项目内基础组件。

## 文件清单（M0.5 结构接线已创建规格骨架；实装期填充实现）

| 文件 | 职责 |
|------|------|
| `theme.ts` | 主题 token（深色默认/亮色可切换、语义色定义） |
| `SemanticColor.tsx` | 语义色纪律封装（绿合格/橙警告/红错误/蓝水线/棕泥线，其余灰阶） |
| `NumberCell.tsx` | tabular-nums 等宽数字组件（单位灰阶小字） |

> 错误边界由 `app/ErrorBoundary.tsx` 唯一承担（M0 已创建）——
> 不在本目录重复规划（无重复资产规则，AGENTS.md §2）。

## 规则

- 语义色之外禁止彩色（§19.3）；紧凑模式（small/12px/8px 栅格）默认；
- 动画纪律：只保留功能性过渡，无装饰动画。
