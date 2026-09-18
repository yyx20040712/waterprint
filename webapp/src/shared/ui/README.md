# shared/ui —— 基础组件与主题

AntD v6 深色主题（dark algorithm + 设计 token，实装于 `app/providers.tsx`）
与项目内基础组件。

## 文件清单

| 文件 | 职责 |
|------|------|
| `semanticColors.ts` | 语义色真源表（token→hex 唯一映射+FALLBACK 兜底+查表函数——全 webapp 渲染/2D 描绘统一消费，SC1 收编字面平行拷贝；C2-3d +pipe_water/pipe_sludge 管廊两键——画布域色轴同值 R-G3 清单；C2VD V1 +section_cap 剖切帽盖键[缩略图半剖剖面封盖灰——冻结测试同步]；B3-b +domain_* 四域色+中性五键[JS 面单源——unitGlyph 域色/流色与 CanvasFlow 图例线色收编；pipe 两键改 DOMAIN_COLORS 单源引用；CSS 轴 --wp-* 同值保留=UF-53 双轴债]） |

> M0.5 期的 `theme.ts`/`SemanticColor.tsx`/`NumberCell.tsx` 结构预留骨架
> 已于复杂度治理清理批（2026-09-18）删除：主题实装面=app/providers.tsx、
> 语义色真源=semanticColors.ts、数字格式化=SolutionsTable 本地实现
> ——预留位与实装位漂移，按「死代码即删」收口。

> 错误边界由 `app/ErrorBoundary.tsx` 唯一承担（M0 已创建）——
> 不在本目录重复规划（无重复资产规则，AGENTS.md §2）。

## 规则

- 语义色之外禁止彩色（§19.3）；紧凑模式（small/12px/8px 栅格）默认；
- 动画纪律：只保留功能性过渡，无装饰动画。
