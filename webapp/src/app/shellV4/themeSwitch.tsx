/**
 * 主题切换器（b1 主题地基批 2026-11-19——壳层常驻最小切换器：三钮组
 * 「正常/护眼/夜间」，形态=已批准设计稿 .theme-switch〔示意 chip+文字
 * 标签+aria-pressed 单选语义〕）。
 *
 * 输入:  shared/store/themeStore（mode 订阅+setMode 切换唯一通道）
 * 输出:  三钮组（.wp-theme-switch——样式在 global.css v4 段，消费
 *        --wp-* 轴自主题换肤）
 *
 * 规格说明：
 *   - 位置=v4 状态条右端（statusBar .r 内——b2 壳重组批自 zoneBand
 *     工具区尾迁入）；
 *   - 点击=setMode（store 内三面联动：React 状态/localStorage 持久化/
 *     DOM data-theme+域色轴）——本组件零自有状态；
 *   - 示意 chip 三恒值=设计稿 --chip-light/warm/dark（展示各模底色，
 *     不随当前主题变）；
 *   - 纯展示件（无 antd 依赖——顶带语境工具区按钮族外的独立形）。
 */
import {
  THEME_MODES,
  THEME_MODE_LABELS,
  useThemeStore,
  type ThemeMode,
} from "../../shared/store/themeStore";

/** 示意 chip 底色（设计稿 --chip-* 三恒值——不随当前主题变）。 */
const CHIP_COLORS: Record<ThemeMode, string> = {
  light: "#f2f5f3",
  warm: "#eee9dd",
  dark: "#242b29",
};

export function ThemeSwitch() {
  const mode = useThemeStore((state) => state.mode);
  const setMode = useThemeStore((state) => state.setMode);
  return (
    <span className="wp-theme-switch" role="group" aria-label="界面主题">
      {THEME_MODES.map((candidate) => (
        <button
          key={candidate}
          type="button"
          className={`wp-theme-opt${mode === candidate ? " on" : ""}`}
          aria-pressed={mode === candidate}
          data-theme-mode={candidate}
          onClick={() => setMode(candidate)}
        >
          <span
            className="wp-theme-chip"
            style={{ background: CHIP_COLORS[candidate] }}
            aria-hidden
          />
          {THEME_MODE_LABELS[candidate]}
        </button>
      ))}
    </span>
  );
}
