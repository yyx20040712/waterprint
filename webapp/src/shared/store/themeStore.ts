/**
 * 主题模式真源 store（b1 主题地基批 2026-11-19——三主题体系：正常·亮色
 * light/护眼·暖色 warm/夜间·暗色 dark；值域与联动机制源自己批准设计稿
 * .zcode/dev-troupe/frontend-redesign/index.html 三主题体系段）。
 *
 * 输入:  localStorage `waterprint.theme`（持久化——api token 键
 *        waterprint.* 同款命名域）+setMode 动作（UI 切换器调用）
 * 输出:  useThemeStore（zustand——mode 态+setMode 三面联动）+值域三导出
 *        （THEME_MODES/THEME_MODE_LABELS/isThemeMode）+机制两函数
 *        （readStoredThemeMode/applyThemeMode）
 *
 * 规格说明（落位裁量：跨 feature 横切 UI 态——app 壳/providers/后续
 *   features 消费面均在，按「同层晋升准入」落 shared/store 首件）：
 *   - 模式真源唯一：antd 配置面（app/themeModes 按模构建）与 CSS 轴
 *     （global.css html[data-theme] 三块）均消费本 store 的 mode 派生，
 *     不另持模式状态；
 *   - 无闪烁初始化：store 创建即同步 readStoredThemeMode（import 期求值
 *     先于首帧——首渲染即正确模）；DOM 侧 data-theme 属性+域色轴按模
 *     注入由 providers.tsx 组合根装载期 applyThemeMode 一次（import 期
 *     ——先于 createRoot）；
 *   - setMode 三面联动：zustand set（React 面即时换肤——antd
 *     ConfigProvider 主题对象重建+cssVar 重生成）+localStorage 持久化
 *     （隐私模式/配额满抛异常=保守视同未写，不阻断换肤）+applyThemeMode
 *     （CSS 轴面换肤——data-theme 属性切换 html 级变量块+域色四轴重注入）；
 *   - 值域校验：存储面只认 light/warm/dark（历史脏值回退 light——设计稿
 *     applyTheme 同款护栏）；
 *   - 作用域机制：document.documentElement data-theme 属性（vs body
 *     class 裁量：html 级=:root 伪类同元素——global.css 三块选择器
 *     :root/html[data-theme] 特异性天然有序，且 html 属性不随壳层重组
 *     〔b2 布局批次重挂载 body 以下节点零影响〕）。
 */
import { create } from "zustand";

import { installDomainColorAxis } from "../ui/semanticColors";

/** 三主题模式（值域=设计稿 data-theme 值）。 */
export type ThemeMode = "light" | "warm" | "dark";

/** 三模声明序（UI 切换器渲染序）。 */
export const THEME_MODES = ["light", "warm", "dark"] as const;

/** 三模中文标签（UI 切换器面——设计稿「正常/护眼/夜间」）。 */
export const THEME_MODE_LABELS: Record<ThemeMode, string> = {
  light: "正常",
  warm: "护眼",
  dark: "夜间",
};

/** 持久化键（waterprint.* 命名域——api token 键同款）。 */
export const THEME_STORAGE_KEY = "waterprint.theme";

/** 未知值→ThemeMode 值域判定（存储面校验消费）。 */
export const isThemeMode = (value: unknown): value is ThemeMode =>
  typeof value === "string" &&
  (THEME_MODES as readonly string[]).includes(value);

/** 读持久化主题（缺席/window 缺席/非法值/存储异常→light——单一空态）。 */
export function readStoredThemeMode(): ThemeMode {
  if (typeof window === "undefined") return "light";
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    return "light"; // 隐私模式/配额满：保守视同未配置
  }
  return isThemeMode(stored) ? stored : "light";
}

/** DOM 应用（CSS 轴面换肤）：html data-theme 属性切 global.css 三块+
 *  域色四轴按模重注入（inline 恒压样式表——UF-53 注入机制按模化）。
 *  document 缺席（SSR/纯 node 测试）=守卫 no-op。 */
export function applyThemeMode(mode: ThemeMode): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = mode;
  installDomainColorAxis(mode);
}

type ThemeStoreState = {
  /** 当前主题模式（init=持久化值同步读——零闪烁）。 */
  mode: ThemeMode;
  /** 切主题唯一通道：状态+持久化+DOM 三面联动。 */
  setMode: (mode: ThemeMode) => void;
};

/** 主题模式 store（模块级单例——StrictMode 双挂载共享）。 */
export const useThemeStore = create<ThemeStoreState>((set) => ({
  mode: readStoredThemeMode(),
  setMode: (mode) => {
    set({ mode });
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch {
      // 持久化失败不阻断换肤（会话内仍可用）
    }
    applyThemeMode(mode);
  },
}));
