/**
 * Provider 组合：AntD ConfigProvider（三主题按模配置）+ QueryClient。
 *
 * 输入:  子组件树+shared/store/themeStore（模式真源——localStorage 持久
 *        化+DOM 应用机制在彼）
 * 输出:  QueryClientProvider+ConfigProvider 包裹的子组件树
 *
 * 规格说明（FE3 批 6b 段一 D2 实装；C1 主题骨架→B4 亮色基线→b1 主题
 *   地基批 2026-11-19 三主题体系〔值=已批准设计稿三主题色板——正常
 *   light/护眼 warm/夜间 dark〕）：
 *   - 三主题双面换肤：antd 面=globalThemeConfigFor(mode)（app/themeModes
 *     ——algorithm light·warm=default/dark=dark+全量 seed 覆写+Layout/
 *     Tabs/Table components；密度 13/28/6 M1 冻结值不动）；CSS 轴面=
 *     global.css html[data-theme] 三块（--wp-* 变量轴）——模式切换=store
 *     setMode 三面联动〔状态/持久化/data-theme 属性+域色轴重注入〕；
 *   - 无闪烁初始化：本模块装载期 applyThemeMode(store 初始模)——import
 *     期先于 createRoot 首帧（批6n 域色轴启动期注入沿承+data-theme 属性
 *     扩面；store init 同步读 localStorage——首渲染即正确模的 antd 面）；
 *     入口分层规则禁 main 直引 shared，故样式底座接线随组合根；
 *   - token 映射切分（b1 裁量）：antd 有槽位色进 ConfigProvider（值=
 *     MODE_COLORS）+global.css 轴同值对〔themeLinkage.test 三态契约〕；
 *     鎏金/soft 三键/canvas/shadow 无 antd 槽位→global.css 轴自持；
 *   - cssVar：antd v6 默认已开 CSS 变量模式（省略即默认开，运行时样式
 *     零重编译）；
 *   - QueryClient 默认项在 ./queryClient（D3 领域错误 retry 口径）；
 *     StrictMode 双挂载安全：模块级单例（组件外创建）。
 */
import { QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";

import { applyThemeMode, useThemeStore } from "../shared/store/themeStore";
import { createQueryClient } from "./queryClient";
import { globalThemeConfigFor } from "./themeModes";

// b1 三主题：装载期 DOM 应用（data-theme 属性+域色轴按模注入）——先于
// 首帧零 FOUC（store init 已同步读 localStorage，此处取初始模）
applyThemeMode(useThemeStore.getState().mode);

// 模块级唯一实例（D2「组件外创建」——StrictMode 双挂载共享同一 client）
const queryClient = createQueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  // 模式订阅：setMode 即时换肤（antd 面配置对象重建+cssVar 重生成；
  // CSS 轴面由 store setMode 内 applyThemeMode 承担）
  const mode = useThemeStore((state) => state.mode);
  return (
    <QueryClientProvider client={queryClient}>
      {/* P0-2 顺手收口（F10/教训 24）：两汉字按钮自动插空格根除（「应 用」
          →「应用」——antd Button 默认在中日韩两字符间插半角空格；SSR 测试
          实证：方案表应用钮「应 用」）。antd v6 面=ConfigProvider button
          prop（theme.components.Button.autoInsertSpace 为已弃用旧位）。 */}
      <ConfigProvider
        theme={globalThemeConfigFor(mode)}
        button={{ autoInsertSpace: false }}
      >
        {children}
      </ConfigProvider>
    </QueryClientProvider>
  );
}
