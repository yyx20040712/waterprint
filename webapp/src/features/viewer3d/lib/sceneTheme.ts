/**
 * 三维场景三主题调色板（b4 功能面重涂 II 批 2026-11-19——开放问题 9
 * 裁决「随主题」：场景底/草地/网格/标注四族色按模取值；Three.js 材质
 * 不能 var() 消费 CSS 轴，故 JS 面经 themeStore mode + CSS 轴计算值
 * 双源解析，主题切换经 React 重渲染生效——与 unitGlyph 域色轴注入
 * 同判据的 JS 面形态）。
 *
 * 输入:  ThemeMode（shared/store/themeStore 模式真源——Scene 经
 *        useThemeStore 订阅）+document.documentElement 计算样式
 *        （--wp-canvas/--wp-text/--wp-bg-page 三轴键——resolveSceneTheme
 *        运行期读取）
 * 输出:  sceneThemeFor(mode)（纯表六键：grassWorld/grass/gridMajor/
 *        gridMinor + engineer/label/labelOutline 亮档回退值）+
 *        resolveSceneTheme(mode)（DOM 面：轴三键经 getComputedStyle
 *        真源读取，缺席/空白=纯表回退）
 *
 * 规格说明（值派生口径——稿无 3D 场景专项色，派生锚=已批准设计稿
 *   三主题色板，非稿值字面；逐模冻结锚=sceneTheme.test.ts）：
 *   - 工程底=--wp-canvas、标注字=--wp-text、描边=--wp-bg-page（轴真源
 *     运行期读取——亮期旧字面 #f5f6f8/#1f2329/#ffffff 由轴档替换；
 *     纯表回退值=轴亮档字面，providers 装载期注入先于首帧故运行期
 *     不可达，仅 node/jsdom 无注入面确定性路径）；
 *   - 草地/网格稿无对应轴键=派生字面：light 档草地沿承现值（像素零
 *     漂移——#e2ece0/#c8dcc2）；美感抛光批 #10 网格降权：light 主格
 *     #54719f→#8b9aa9（蓝饱和度收口）、次格 #d8dee8→#dee3e9；warm
 *     档=草地降饱和微暖移、网格向暖灰阶收敛（#878571/#e2ddce）；dark
 *     档=草地/网格降至暗档亮度带（非纯黑——与稿 surface 族同带），
 *     主格保持与底可辨分层（#4a5a72）。
 */
import type { ThemeMode } from "../../../shared/store/themeStore";

/** 场景调色板六键（消费面=Scene 场景底/GroundStage 草地+网格/Annotations 标注）。 */
export type SceneTheme = {
  /** 草地世界底（Scene 画布底色——草地层开）。 */
  grassWorld: string;
  /** 草地材质色（GroundStage 地面 mesh）。 */
  grass: string;
  /** 工程底（草地层关——--wp-canvas 轴同源）。 */
  engineer: string;
  /** 主格网格色（10m 工程格）。 */
  gridMajor: string;
  /** 次格网格色（2m 细分格）。 */
  gridMinor: string;
  /** 标注字色（troika 文本——--wp-text 轴同源）。 */
  label: string;
  /** 标注描边色（troika outline——--wp-bg-page 轴同源）。 */
  labelOutline: string;
};

/** 轴亮档字面（回退面——轴注入先于首帧，运行期不可达；jsdom/node 测试面
 *  确定性路径，值=global.css :root 块）。 */
const AXIS_FALLBACK = {
  canvas: "#edf2f0",
  text: "#202826",
  bgPage: "#f2f5f3",
} as const;

/** 三模纯表（草地/网格四键=派生字面冻结锚；轴三键=回退值。美感抛光
 *  批 #10：网格降权——gridMajor 蓝饱和度收口〔构筑物轮廓为第一对比，
 *  网格不再覆盖全屏抢眼〕+gridMinor 再弱一档；不透明度分层在
 *  GroundStage 材质面承载）。 */
const SCENE_THEMES: Record<ThemeMode, SceneTheme> = {
  light: {
    grassWorld: "#e2ece0",
    grass: "#c8dcc2",
    engineer: AXIS_FALLBACK.canvas,
    gridMajor: "#8b9aa9",
    gridMinor: "#dee3e9",
    label: AXIS_FALLBACK.text,
    labelOutline: AXIS_FALLBACK.bgPage,
  },
  warm: {
    // 暖档草地=暖橄榄向（无头实读回炉：首值灰绿偏冷与羊皮纸页框割裂
    // ——向纸底靠拢降环带跳变）
    grassWorld: "#eae4cf",
    grass: "#d2cdaa",
    engineer: AXIS_FALLBACK.canvas,
    gridMajor: "#878571",
    gridMinor: "#e2ddce",
    label: AXIS_FALLBACK.text,
    labelOutline: AXIS_FALLBACK.bgPage,
  },
  dark: {
    grassWorld: "#1d2622",
    grass: "#2a3530",
    engineer: AXIS_FALLBACK.canvas,
    gridMajor: "#4a5a72",
    gridMinor: "#2c3532",
    label: AXIS_FALLBACK.text,
    labelOutline: AXIS_FALLBACK.bgPage,
  },
};

/** 模式 → 纯表调色板（草地/网格派生值消费面+轴键回退面）。 */
export function sceneThemeFor(mode: ThemeMode): SceneTheme {
  return SCENE_THEMES[mode];
}

/** 计算样式读取器（注入面——测试替身/缺省 document 面）。 */
type VarReader = (name: string) => string;

/** document 面缺省读取器（jsdom/node 缺席=恒空串→回退纯表）。 */
const documentVarReader: VarReader = (name) => {
  if (typeof document === "undefined") {
    return "";
  }
  return getComputedStyle(document.documentElement).getPropertyValue(name);
};

/** 模式 → 场景调色板（DOM 面：轴三键运行期真源读取——--wp-canvas/
 *  --wp-text/--wp-bg-page 计算值〔trim 归一〕；缺席/空白=纯表回退。
 *  Scene 每渲染解析一次，主题切换=setMode 内 applyThemeMode 先写 DOM
 *  后重渲染，计算值与模一致）。 */
export function resolveSceneTheme(
  mode: ThemeMode,
  readVar: VarReader = documentVarReader,
): SceneTheme {
  const base = sceneThemeFor(mode);
  const canvas = readVar("--wp-canvas").trim();
  const text = readVar("--wp-text").trim();
  const bgPage = readVar("--wp-bg-page").trim();
  return {
    ...base,
    engineer: canvas !== "" ? canvas : base.engineer,
    label: text !== "" ? text : base.label,
    labelOutline: bgPage !== "" ? bgPage : base.labelOutline,
  };
}
