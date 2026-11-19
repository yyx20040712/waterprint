/**
 * 语义色真源表：token→色值唯一映射（SC1 真源化——全 webapp 渲染/2D
 * 描绘统一消费；features 互不 import 的字面平行拷贝全数收编于此）。
 *
 * 输入:  语义 token 字符串（渲染描述/组件携带的 semantic 键）
 * 输出:  SEMANTIC_COLORS（34 键字面表——B3-b 增 domain_* 五键）+
 *        FALLBACK_COLOR（未登记兜底灰阶）+semanticColor()（查表函数
 *        ——未登记语义回退兜底，禁抛错打断渲染）+DOMAIN_COLORS/
 *        domainCssVarsFor(mode)/installDomainColorAxis(mode)（批6n UF-53
 *        双轴归一+b1 三模化——域色 CSS 变量轴按模注入面，经
 *        shared/store/themeStore applyThemeMode 调用：装载期+切换期）
 *
 * 迁移口径（SC1 D1/D2）：3D 图元色族 12 键自 PoolBox 本地表迁移、
 * 2D 场面色族 7 键自 SiteRoutes/SiteBoundary/SiteCanvas 平行拷贝收编、
 * 2D 单点彩色语义族 6 键自 SiteCanvas 收编（SC1 5 键+SPC2
 * boundary_error——测试键集冻结注释同口径）——全部原值迁移零色值变更
 * （像素零漂移）。灰阶族（结构/网格/UI 边框灰）与图表色族
 * （profileChart）不收编（非本批漂移面）。键集冻结锚=
 * semanticColors.test.ts（增删键/改值必须同步字面清单）。
 * B3-b 增补（《裁决书》方案二 2b）：四域色+中性 JS 面单源收编——
 * unitGlyph.domainColorOf/streamColorOf 与 CanvasFlow LEGEND_LINES 的
 * 域色字面量收敛至 domain_* 键（同值搬家零漂移；global.css --wp-* 轴
 * 保留——SVG 属性面不能 var() 的 CSS/JS 双轴根因性债=UF-53 另立挂账）。
 * b4 功能面重涂 II 批（2026-11-19）管廊键三态收口：域派生键
 * （pipe_ 与 domain_ 前缀族）运行期查表改按当前模读 DOMAIN_COLORS——
 * CSS 轴注入（installDomainColorAxis）同步记录 JS 面当前模，Three.js
 * 管廊图元色随主题换肤；静态表值=light 档参照锚（semanticColors.test
 * 冻结）不变。
 * 批6n 增补（UF-53 双轴归一收口——2026-09-29，设计裁量二案取
 * CSS-in-JS 注入案，卷宗=.workflow/backend-calc-complete/b6n-design.md）：
 * 域色 CSS 变量轴改为本表启动期注入（global.css :root 域色字面量退役）
 * ——改色单源=DOMAIN_COLORS 一处，JS 面（domain_* 与 pipe_* 派生键）与
 * CSS 面（注入轴 var() 消费）两轴同步；SVG/Canvas/Three 不能 var() 的
 * 根因面零改动（本就消费 JS 键）；双轴同值机器断言=semanticColors.test
 * 冻结锚扩 CSS 侧。
 */
import type { ThemeMode } from "../store/themeStore";

/** 四域色+中性（域色唯一真源——批6n 双轴归一后 CSS 轴四键经
 * installDomainColorAxis(mode) 自本表按模注入〔neutral=JS 面键不入轴
 * ——零 var() 消费方〕；改色=改本表一处两轴同步）。
 * b1 主题地基批（2026-11-19）：扩三模记录——值=已批准设计稿域色三态
 * （稿口径「水线与泥线始终可区分」——暗色提亮/暖色降饱和各自校准；
 * 稿无 neutral 键→回退灰三模恒值）。b3 功能面重涂批（2026-11-19）：
 * DOM/SVG 消费面经注入轴 var(--wp-*) 三态取值〔unitGlyph
 * DOMAIN_COLOR_VARS〕——本表=轴注入单源，画布/图例/连线随主题换肤。 */
export const DOMAIN_COLORS = {
  light: {
    water: "#286b86", // 市政水线（municipal）
    sludge: "#7d573e", // 污泥线
    mine: "#3f7d6a", // 矿井水线
    convey: "#64788a", // 输配水线
    neutral: "#595959", // 未收录/清单未达回退灰
  },
  warm: {
    water: "#456a72",
    sludge: "#765239",
    mine: "#65775c",
    convey: "#77766e",
    neutral: "#595959",
  },
  dark: {
    water: "#78acc0",
    sludge: "#c09a78",
    mine: "#83b49c",
    convey: "#9aabb9",
    neutral: "#595959",
  },
} as const satisfies Record<ThemeMode, Record<string, string>>;

/** 域色 CSS 变量轴注入映射（批6n UF-53——`--wp-<域>` 键自
 * DOMAIN_COLORS[mode] 单源派生；global.css :root 域色字面量已退役，
 * CSS 消费面 var(--wp-*) 经注入取值。键集=实际 CSS 消费面四键〔水/泥/
 * 矿/输配〕——neutral 零 var() 消费方不入轴〔A2-N-06 死变量纪律——
 * 门一回炉双席 W 共指处置〕；键集冻结锚=semanticColors.test。 */
export const domainCssVarsFor = (
  mode: ThemeMode,
): {
  "--wp-water": string;
  "--wp-sludge": string;
  "--wp-mine": string;
  "--wp-convey": string;
} => ({
  "--wp-water": DOMAIN_COLORS[mode].water,
  "--wp-sludge": DOMAIN_COLORS[mode].sludge,
  "--wp-mine": DOMAIN_COLORS[mode].mine,
  "--wp-convey": DOMAIN_COLORS[mode].convey,
});

/** 域色 JS 面当前模（b4 功能面重涂 II 批 2026-11-19——管廊 pipe_* 键
 *  三态收口）：Three.js/Canvas 图元不能 var() 消费注入轴，故 CSS 轴
 *  注入时同步记录当前模，semanticColor 对域派生键（pipe_ 与 domain_ 族）
 *  按模查 DOMAIN_COLORS——启动期 installDomainColorAxis 首模+切换期
 *  重注入双径覆盖；缺省 light=纯 node 测试基线（semanticColors.test
 *  冻结锚 light 档值保持）。 */
let activeDomainMode: ThemeMode = "light";

/** 注入域色 CSS 变量轴（批6n=providers 装载期一次；b1 按模化=经
 * shared/store/themeStore applyThemeMode 调用——装载期首模+切换期
 * 重注入，import 期先于 createRoot 首帧无 FOUC；b4：同步记录 JS 面
 * 当前模；document 缺席〔SSR/纯 node 测试〕=守卫 no-op——本项目纯
 * CSR，缺席面仅测试环境；接线行为级守卫=src/app/domainColorAxis.test。
 * 缺省参=light 兼容面）。 */
export const installDomainColorAxis = (mode: ThemeMode = "light"): void => {
  activeDomainMode = mode;
  if (typeof document === "undefined") return;
  for (const [name, value] of Object.entries(domainCssVarsFor(mode)))
    document.documentElement.style.setProperty(name, value);
};

/** 语义色表（token→色值唯一映射处——全 webapp 渲染/2D 描绘统一消费）。 */
export const SEMANTIC_COLORS = {
  // 3D 图元色族（自 PoolBox 迁移，12 键；批3 首族视觉验收迭代[2026-09-12
  // 用户批注 a]：混凝土族调中性灰——pool_wall 蓝偏置 +25→+10）
  pool_wall: "#a3a9ad",
  partition: "#8f9599",
  channel: "#7f8a93",
  ground: "#cfd6dc",
  water_surface: "#2f7fd1", // 蓝水线
  sludge: "#8c5a2b", // 棕泥线
  aerator: "#d48806",
  paddle: "#d48806",
  media: "#6a7f5a",
  gate: "#5b8db8",
  pipe: "#5b8db8",
  decant: "#5b8db8",
  // 2D 场面色族（自 SiteRoutes/SiteBoundary/SiteCanvas 平行拷贝收编，7 键）
  road: "#6b6f76",
  boundary: "#d4380d",
  corridor_water: "#2f7fd1",
  corridor_power: "#f2a93b",
  corridor_gas: "#3fa34d",
  corridor_comm: "#9a6dd7",
  corridor_fallback: "#8c8c8c",
  // C2-3d 管廊两键（三维管线两色制——值=域色轴 water/sludge 单源引用，
  // R-G3 联动清单成员，改色以 DOMAIN_COLORS 为基准）
  pipe_water: DOMAIN_COLORS.light.water,
  pipe_sludge: DOMAIN_COLORS.light.sludge,
  // B3-b 四域色 JS 面（unitGlyph 域色/stream 色+CanvasFlow 图例线色收编
  // ——同值搬家；CSS 轴 --wp-* 联动义务见 UF-53；b3 功能面重涂批
  // 2026-11-19：DOM/SVG 消费面改经 unitGlyph DOMAIN_COLOR_VARS 取注入轴
  // 〔var(--wp-*)——三态随 installDomainColorAxis 换肤〕；本组键=非 DOM
  // JS 消费面（Canvas/Three 等不能 var() 的图元）light 档参照值保留，
  // 三态接管真源=DOMAIN_COLORS 按模记录）
  domain_water: DOMAIN_COLORS.light.water,
  domain_sludge: DOMAIN_COLORS.light.sludge,
  domain_mine: DOMAIN_COLORS.light.mine,
  domain_convey: DOMAIN_COLORS.light.convey,
  domain_neutral: DOMAIN_COLORS.light.neutral,
  // C2VD V1 剖切帽盖键（缩略图半剖剖面封盖灰——pool_wall #8d99a6 与
  // ground #cfd6dc 之间档；材质区断面封实，水体/空腔区不入[无 writer]）
  section_cap: "#a8b4c2",
  // 2D 单点彩色语义族（自 SiteCanvas 收编，5 键；B4 亮底复核
  // 〔任务书 D4〕：pending 有文本级消费面〔Scene/PlacementBanner
  // stale 横幅 12px 文本〕→ #8a6100（白底 5.54:1 文本级达标）；
  // spacing_warn/maintenance 为图形级消费面→白底 ≥3:1 档
  // 〔#ad6800 4.41:1/#d46b08 3.56:1——暗期 #faad14/#fa8c16 白底
  // 1.90/2.38:1 不达标退役〕；selected/measure/spacing_error/
  // boundary_error 白底 5.19/4.14/3.27/3.31:1 保持——对比度实录=
  // .workflow/b4b5-20261009/contrast-b4.txt）
  selected: "#1668dc",
  pending: "#8a6100",
  measure: "#2f7fd1",
  spacing_warn: "#ad6800", // L4b 校核 WARN 黄
  spacing_error: "#ff4d4f", // L4b 校核 ERROR 红（三色并存：pending=未计算）
  boundary_error: "#fa541c", // SPC2 红线越界 ERROR（红族异相橙红——与 spacing_error 语义区分）
  // S11 检修缺位占位（viewer3d 警示面——图示语义警示橙，与 pending
  // 同族暖色档但独立键：池组检修占位非「未计算」语义）
  maintenance: "#d46b08",
} as const;

/** 未登记语义兜底灰阶（禁抛错打断渲染）。 */
export const FALLBACK_COLOR = "#9aa5b1";

/** 域派生键集（b4 三态收口——查表按当前模改读 DOMAIN_COLORS：管廊
 *  pipe_water/pipe_sludge〔Three.js 面消费〕+domain_* 五键〔JS 非达
 *  消费面参照值〕；表内静态值=light 档参照锚〔semanticColors.test
 *  冻结〕，运行期取值以本映射为准）。 */
const DOMAIN_DERIVED_KEYS: Record<string, keyof (typeof DOMAIN_COLORS)["light"]> = {
  pipe_water: "water",
  pipe_sludge: "sludge",
  domain_water: "water",
  domain_sludge: "sludge",
  domain_mine: "mine",
  domain_convey: "convey",
  domain_neutral: "neutral",
};

/** 语义 token → 色值（未登记语义=灰阶兜底——禁抛错打断渲染；域派生键
 *  按当前模查 DOMAIN_COLORS〔b4——CSS 轴注入同步记录的 activeDomainMode〕）。 */
export const semanticColor = (semantic: string): string => {
  const domainKey = DOMAIN_DERIVED_KEYS[semantic];
  if (domainKey !== undefined) {
    return DOMAIN_COLORS[activeDomainMode][domainKey];
  }
  return SEMANTIC_COLORS[semantic as keyof typeof SEMANTIC_COLORS] ?? FALLBACK_COLOR;
};
