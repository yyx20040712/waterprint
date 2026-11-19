# shared/ui —— 基础组件与主题

AntD v6 三主题体系（b1 主题地基批 2026-11-19：正常·亮色/护眼·暖色/夜间·
暗色——模式真源=shared/store/themeStore，antd 配置面=app/themeModes，
实装于 `app/providers.tsx`+`app/shellV4/shellV4.tsx`）与项目内基础组件。

## 文件清单

| 文件 | 职责 |
|------|------|
| `semanticColors.ts` | 语义色真源表（token→hex 唯一映射+FALLBACK 兜底+查表函数——全 webapp 渲染/2D 描绘统一消费，SC1 收编字面平行拷贝；C2-3d +pipe_water/pipe_sludge 管廊两键——画布域色轴同值 R-G3 清单；C2VD V1 +section_cap 剖切帽盖键[缩略图半剖剖面封盖灰——冻结测试同步]；B3-b +domain_* 四域色+中性五键[JS 面单源——unitGlyph 域色/流色与 CanvasFlow 图例线色收编；pipe 两键改 DOMAIN_COLORS 单源引用；批6n UF-53 双轴归一收口：CSS 轴 --wp-* 启动期自本表注入，global.css :root 域色字面量退役；b1 主题地基批：DOMAIN_COLORS 扩三模记录〔值=已批准设计稿域色三态〕+domainCssVarsFor(mode)+installDomainColorAxis(mode) 按模注入；b3 功能面重涂批 2026-11-19：DOM/SVG 消费面经注入轴 var(--wp-*) 三态取值〔unitGlyph DOMAIN_COLOR_VARS〕；b4 功能面重涂 II 批：域派生键〔pipe_ 与 domain_ 族〕运行期查表按当前模读 DOMAIN_COLORS——installDomainColorAxis 注入时同步记录 JS 面当前模〔管廊 Three.js 图元随主题换肤〕，静态表值=light 档参照锚不变；美感抛光批 2026-11-20 #10：MATERIAL_COLORS 三模材质坡道〔pool_wall/partition/channel/ground 四键按模取值——固定亮灰构筑物与暗色世界脱节根除，light 档=静态表同值零漂移〕） |
| `saveConflictModal.tsx` | 保存冲突对话单源（F2 并发丢更新批 2026-11-20）：baseHashOf 读时基线提取（metadata.content_hash→PUT ?base_hash 载荷源）+confirmSaveConflict 三选对话呈现（antd Modal.confirm 自定义 footer：用我的覆盖/放弃我的改动/稍后处理）+surfaceSaveConflict 调度（409 ProjectConcurrentWriteError→覆盖=重拉最新新基线重发/放弃=消费面清编辑态重拉/稍后=留本地）；判别=isSaveConflict（shared/api/http——409 族与锁冲突分立）；消费面=topBar 保存/保存即算+AssumptionsPanel+enumerateModal+SiteplanPane 四保存链 |

> M0.5 期的 `theme.ts`/`SemanticColor.tsx`/`NumberCell.tsx` 结构预留骨架
> 已于复杂度治理清理批（2026-09-18）删除：主题实装面=app/providers.tsx、
> 语义色真源=semanticColors.ts、数字格式化=SolutionsTable 本地实现
> ——预留位与实装位漂移，按「死代码即删」收口。

> 错误边界由 `app/ErrorBoundary.tsx` 唯一承担（M0 已创建）——
> 不在本目录重复规划（无重复资产规则，AGENTS.md §2）。

## 规则

- 语义色之外禁止彩色（§19.3）；紧凑模式（small/12px/8px 栅格）默认；
- 动画纪律：只保留功能性过渡，无装饰动画。
