/**
 * 三主题 antd 配置面（b1 主题地基批 2026-11-19——值源=已批准设计稿
 * .zcode/dev-troupe/frontend-redesign/index.html :root〔正常〕/
 * html[data-theme="warm"]〔护眼〕/html[data-theme="dark"]〔夜间〕三块
 * 色板，token 名与值直接自稿内提取）。
 *
 * 输入:  ThemeMode（shared/store/themeStore 模式真源）
 * 输出:  MODE_COLORS（三模色板记录——antd 槽位色 18 键/模；CSS 轴
 *        global.css 三块同值联动=themeLinkage.test 三态契约）+
 *        globalThemeConfigFor(mode)（providers 全局面——密度 13/32/6
 *        阅读档）+v4ThemeConfigFor(mode)（v4 壳 scoped 面——密度
 *        13/30/6 阅读档）
 *
 * 规格说明（稿 token→antd/--wp-* 轴映射切分裁量——沿双源联动契约分界：
 *   antd 有槽位者进 ConfigProvider token+轴同值对，无槽位者
 *   〔accent-soft/success-soft/warning-soft/canvas/shadow〕
 *   留 global.css 轴自持）：
 *   - 稿 bg/surface/paper/surface-2 四层底 → colorBgLayout/Layout.siderBg/
 *     colorBgContainer·Elevated/Table.headerBg·rowHoverBg（--wp-bg-*
 *     四档轴同值）；
 *   - 稿 line/line-soft → colorBorder/colorBorderSecondary（+Table.
 *     colorSplit 派生消费）；
 *   - 稿 ink/muted/faint → 文字三档；accent → colorPrimary/Info/Link+
 *     Tabs inkBar/itemSelected（G1-02 沿承：选中指示=AC 同值锚——本批
 *     AC 自工程蓝换稿青绿三态）；on-accent → colorTextLightSolid
 *     （夜间浅青底配深字，非默认纯白）；
 *   - 稿 ok/warn/error → colorSuccess/colorWarning/colorError；
 *   - algorithm：light·warm=defaultAlgorithm（护眼=亮算法+暖 token
 *     覆盖——稿 warm color-scheme:light 同义）、dark=darkAlgorithm；
 *   - 密度（美感抛光批 #2/#12——字级与控件阅读尺寸上调）：全局
 *     fontSize 13/controlHeight 32/borderRadius 6；v4 scoped 13/30/6；
 *   - 字体栈沿承现值（稿 font 栈非主题差分面——字体改革随后续批次）。
 * 美感抛光批（aesthetic-polish 2026-11-20）：warm/dark 表面色板随
 *   global.css 轴同值联动重调（#3/#9——暗色表面阶梯/暖色面差，双源
 *   联动契约 themeLinkage.test 三态断言同步）；gold 族轴退役（#14，
 *   本文件本无 gold 键）。
 */
import { theme } from "antd";
import type { ThemeConfig } from "antd";

import type { ThemeMode } from "../shared/store/themeStore";

/** 三模色板（antd 槽位色——轴自持色〔soft/canvas/shadow 等〕同值入
 *  global.css 三块，此处为 JS 面真源；键值=设计稿字面）。 */
export const MODE_COLORS = {
  light: {
    bgPage: "#f2f5f3", // 稿 bg（页面底）
    bgContainer: "#fafcfa", // 稿 surface（侧栏/面板面）
    bgElevated: "#fdfefc", // 稿 paper（阅读面/浮层）
    bgDeep: "#f5f7f5", // 稿 surface-2（次级面/表头/悬停）
    border: "#d4dcd7", // 稿 line
    border2: "#e5eae6", // 稿 line-soft
    accent: "#246b63", // 稿 accent（操作色）
    accentSoft: "#e2eeea", // 稿 accent-soft（轴自持）
    onAccent: "#f7fbfa", // 稿 on-accent（主操作面文字）
    text: "#202826", // 稿 ink
    text2: "#5c6965", // 稿 muted
    text3: "#65716b", // 稿 faint
    success: "#2f7151", // 稿 ok
    successSoft: "#e4efe7", // 稿 ok-soft（轴自持）
    warning: "#87600f", // 稿 warn
    warningSoft: "#f4ecd9", // 稿 warn-soft（轴自持）
    error: "#a3453d", // 稿 error
    errorSoft: "#f5e6e3", // 稿 error-soft（轴自持）
    canvas: "#edf2f0", // 稿 canvas（画布底——轴自持）
    shadow: "rgba(39, 55, 49, 0.08)", // 稿 shadow（轴自持）
    infoSoft: "#e4edf1", // 稿 info-soft（水线徽标软底——轴自持；b3 功能面重涂批）
    gridDot: "#cbd5d0", // 稿 grid-dot（画布点阵格点——轴自持；b3 功能面重涂批）
  },
  warm: {
    // 美感抛光批 #9：elevated 向中性米白移+面差 1.04→1.14（泛黄收口）
    bgPage: "#eae4d3",
    bgContainer: "#f3ecda",
    bgElevated: "#fcfbf8",
    bgDeep: "#eee6d2",
    border: "#d7cebc",
    border2: "#e2d8c3",
    accent: "#76613d",
    accentSoft: "#eae0cd",
    onAccent: "#fffaf0",
    text: "#302f29",
    text2: "#666459",
    text3: "#6b675b",
    success: "#52704c",
    successSoft: "#e7eadb",
    warning: "#765214",
    warningSoft: "#eee2c8",
    error: "#8b493e",
    errorSoft: "#eee0d7",
    canvas: "#eae3d5",
    shadow: "rgba(74, 61, 39, 0.08)",
    infoSoft: "#e4e5dc",
    gridDot: "#d3c8b4",
  },
  dark: {
    // 美感抛光批 #3：表面阶梯重调（page/container 1.24、container/
    // elevated 1.25、border2/container 1.42——文字三档不动）
    bgPage: "#0d1211",
    bgContainer: "#1f2725",
    bgElevated: "#2e3735",
    bgDeep: "#171d1b",
    border: "#3d4743",
    border2: "#36403c",
    accent: "#7bb9ac",
    accentSoft: "#263c36",
    onAccent: "#112823",
    text: "#e3e9e6",
    text2: "#aab6b1",
    text3: "#8b9892",
    success: "#88bb96",
    successSoft: "#24382b",
    warning: "#d2ae6b",
    warningSoft: "#3b3323",
    error: "#df9289",
    errorSoft: "#402b29",
    canvas: "#131817",
    shadow: "rgba(0, 0, 0, 0.18)",
    infoSoft: "#26363c",
    gridDot: "#35413c",
  },
} as const satisfies Record<ThemeMode, Record<string, string>>;

/** 字体两栈（B4 冻结值——主题差分外，字体改革随后续批次）。 */
const FONT_SANS =
  '"Segoe UI", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif';
const FONT_MONO = '"Cascadia Code", "JetBrains Mono", Consolas, monospace';

/** 主题算法（light·warm=亮算法；dark=暗算法）。 */
function algorithmFor(mode: ThemeMode): ThemeConfig["algorithm"] {
  return mode === "dark" ? theme.darkAlgorithm : theme.defaultAlgorithm;
}

/** antd 全局面主题（providers.tsx 消费——密度 13/32/6 阅读档）。 */
export function globalThemeConfigFor(mode: ThemeMode): ThemeConfig {
  const c = MODE_COLORS[mode];
  return {
    algorithm: algorithmFor(mode),
    token: {
      colorPrimary: c.accent,
      colorInfo: c.accent,
      colorLink: c.accent,
      colorBgLayout: c.bgPage,
      colorBgContainer: c.bgElevated,
      colorBgElevated: c.bgElevated,
      colorBorder: c.border,
      colorBorderSecondary: c.border2,
      colorText: c.text,
      colorTextSecondary: c.text2,
      colorTextTertiary: c.text3,
      colorSuccess: c.success,
      colorWarning: c.warning,
      colorError: c.error,
      colorTextLightSolid: c.onAccent,
      borderRadius: 6,
      controlHeight: 32,
      fontSize: 13,
      fontFamily: FONT_SANS,
      fontFamilyCode: FONT_MONO,
    },
    components: {
      Layout: {
        headerBg: c.bgPage,
        headerHeight: 48,
        siderBg: c.bgContainer,
        bodyBg: c.bgPage,
      },
      Tabs: {
        // 选中指示=AC 同值锚（G1-02 沿承）；未选/悬浮按压=文字轴同值
        // 双源（antd token 为 JS 字面量无法 var() 引轴——A2-N-01 联动面）
        inkBarColor: c.accent,
        horizontalItemPadding: "10px 14px",
        itemColor: c.text2,
        itemHoverColor: c.text,
        itemActiveColor: c.text,
        itemSelectedColor: c.accent,
      },
      Table: {
        headerBg: c.bgDeep,
        rowHoverBg: c.bgDeep,
        colorSplit: c.border2,
      },
    },
  };
}

/** v4 壳 scoped 面主题（shellV4.tsx 消费——密度 13/30/6 阅读档；
 *  回炉 R4 沿承：components 三族显式覆写防外层组件级 token 渗入）。 */
export function v4ThemeConfigFor(mode: ThemeMode): ThemeConfig {
  const c = MODE_COLORS[mode];
  return {
    algorithm: algorithmFor(mode),
    token: {
      colorPrimary: c.accent,
      colorInfo: c.accent,
      colorLink: c.accent,
      colorBgLayout: c.bgPage,
      colorBgContainer: c.bgElevated,
      colorBgElevated: c.bgElevated,
      colorBorder: c.border,
      colorBorderSecondary: c.border2,
      colorText: c.text,
      colorTextSecondary: c.text2,
      colorTextTertiary: c.text3,
      colorSuccess: c.success,
      colorWarning: c.warning,
      colorError: c.error,
      colorTextLightSolid: c.onAccent,
      borderRadius: 6,
      controlHeight: 30,
      fontSize: 13,
      fontFamily: FONT_SANS,
      fontFamilyCode: FONT_MONO,
    },
    components: {
      Table: {
        headerBg: c.bgDeep,
        rowHoverBg: c.bgDeep,
        colorSplit: c.border2,
      },
      Tabs: {
        inkBarColor: c.accent,
        itemColor: c.text2,
        itemHoverColor: c.text,
        itemActiveColor: c.text,
        itemSelectedColor: c.accent,
      },
      Layout: {
        headerBg: c.bgPage,
        siderBg: c.bgContainer,
        bodyBg: c.bgPage,
      },
    },
  };
}
