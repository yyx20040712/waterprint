# webapp 工程惯例（GR-39~41——原 engineering-conventions.md §12 整体迁移，
> GOV1 2026-09-12 拆文件守 500 行预算：宪法 §2"超限拆文件"正解。
> 条目格式与上位文件关系同 engineering-conventions.md 头注；GR 编号
> 沿册不变（代码/文档既有 GR-39/40/41 引用零改动）。

## 12. webapp 样式与主题（C1 批 2026-09-10）

### GR-39 webapp 色值两源制：antd token 主源+--wp-* 变量轴副源，联动红线
- 规则：webapp 色值真源两处——**组件面**（antd 组件样式/props）一律
  经 `providers.tsx` ConfigProvider token（含 components 微调）；
  **非 antd 消费面**（全局 CSS/inline style/自绘组件）经
  `webapp/src/app/global.css` 的 `--wp-*` 变量轴（`var()` 引用，禁
  再散写 hex——品牌装饰色例外，须头注登记）。两源同值色构成**双源
  联动清单**（global.css 头注契约：`--wp-bg-page ↔ colorBgLayout` 等）
  ——改任一色须双处联动改。antd v6 cssVar 变量挂组件作用域非
  `:root`（C1 无头实测零命中），跨组件消费不走 `--ant-*`，故变量轴
  是必要副源而非冗余。
- 为什么：C1 前 22 个 tsx 散写 inline 色值无单一真相源；antd token
  为 JS 字面量面无法被 CSS `var()` 引用，而变量轴又管不到 antd 组件
  内部——两源各守一面，缺联动契约则改色漏改一半（A2-N-01 双审
  Important 发现的收口形态）。
- 绑定：providers.tsx/global.css 头注契约、task-C1-plan.md §3a/§3b
  （含 R 轮勘误）；C1 批 2026-09-10 立。

### GR-40 新组件滚动域收敛：应用壳恒在视口，溢出走最近滚动容器
- 规则：webapp 新增/重制组件的高度行为遵守滚动骨架（C1 落地）：
  应用壳（顶栏/单元库/标签栏/状态栏）恒在视口；内容溢出滚动发生在
  标签内容区（`.ant-tabs-body-holder` 统一滚动域）或组件自管的
  `overflow:auto` 容器——**禁止依赖或触发 document 级整页滚动**
  （body `overflow:hidden` 全局根除）。画布类组件（React Flow/
  自绘 SVG）自管 pan/zoom 的例外须头注注明。
- 为什么：C1 前内容超高直接顶开 document 滚动，滚轮一滚顶栏/侧栏
  被顶出视口、暴露 body 底色（用户需求①，c-analysis S3 实证）；
  无此条则新组件可能重新引入整页滚动。
- 绑定：global.css 高度链+body-holder 滚动域、App.tsx 滚动骨架、
  shoot_c1_impl.py 无头断言（回归锚）；C1 批 2026-09-10 立。

### GR-41 数据表格列规格：定宽+固定首尾列+吸顶+工程数值格式化
- 规则：webapp 数据表格（动态列宽表）重制/新建遵守——`tableLayout:
  "fixed"`+按列型定宽（语义列型 width 单源组件内常量）；`scroll.x`=
  列宽和；首列 `fixed`（行身份）与操作列 `fixed:"right"`（入口）横滚
  恒在；表头吸顶用 `sticky`（吸附最近滚动容器，GR-40 单滚动域——**禁
  scroll.y 内滚域**）；数值列=右对齐+tabular-nums+`formatSolutionValue`
  形态（整数千分位/非整数恒 3 位小数/|v|<0.001 三位有效——列内小数位
  对齐），全精度经 `title` 悬浮保留；两行表头（标签主行+单位副行弱色
  mono，无量纲无副行）。
- 为什么：C2 前 antd 默认自适应压缩列宽致表头竖排一字一行/英文键截断
  （用户需求①余面，c-analysis S2 实证）；16 位浮点直出不可读；横滚
  失锚后行身份与应用入口双双滚出视口。
- 绑定：SolutionsTable.tsx 头注、solutionsView.ts（formatSolutionValue
  /FIXED_TITLES）、shoot_c2_impl.py 无头断言（回归锚）；C2 批
  2026-09-10 立。

