/**
 * Provider 组合：AntD ConfigProvider（C1 主题骨架全量 token）+ QueryClient。
 *
 * 输入:  子组件树
 * 输出:  QueryClientProvider+ConfigProvider 包裹的子组件树
 *
 * 规格说明（FE3 批 6b 段一 D2 实装；C1 批 2026-09-10 主题骨架——方向 A
 *   暗色冻结；B4 亮色基线替换批 2026-10-09 全量亮值化〔plan §三分层白
 *   色板——任务书 D1 逐键表〕；C1 期「亮色切换维持 UX 批挂账」就此闭合
 *   ——仅亮色无双主题，切换器零建零拆〔D7〕）：
 *   - 亮色基线（B4）：algorithm=defaultAlgorithm+全量 seed token 覆盖
 *     （值源=shellV4 v4LightTheme——B1 视觉验收 PASS 面同源）；
 *   - 鎏金双源契约 B4 更新（G1-02）：Tabs inkBarColor=AC #1677ff
 *     （亮基线选中指示=AC 蓝）——与 global.css --wp-gold 不再同值，
 *     装饰金面单源=global.css 轴（改鎏金只动 CSS 侧一处）；
 *   - token 层级：seed 色（colorPrimary AC #1677ff）+分层白三底
 *     （Layout #f5f6f8 页面/Container #ffffff 面板/Elevated #ffffff
 *     浮层〔siderBg #fafbfc 面板底一档〕）+文字三档（#1f2329/#646a73/
 *     #8a93a0——plan §三 FG-1/FG-2 实测 AA 达标）+语义三色（成功/
 *     警告/错误——语义色纪律 §19：绿合格/橙警告/红错误，亮底深字值
 *     #2e7d32/#8a6100/#b3261e）；鎏金/水线/泥线三色无 antd token 槽位
 *     →global.css 变量轴（--wp-gold/--wp-water/--wp-sludge——inline
 *     消费点经 var() 引用；批6n UF-53 后域色轴真源=semanticColors.ts
 *     启动期注入，gold 仍 global.css 轴字面量）；
 *   - 批6n（UF-53 双轴归一 2026-09-29）：域色四轴（--wp-water/sludge/
 *     mine/convey）注入接线在本模块装载期（installDomainColorAxis
 *     模块顶层调用——import 期先于 createRoot 首帧，CSS var() 消费面零
 *     闪烁；入口分层规则禁 main 直引 shared，故样式底座接线随组合根）；
 *   - 度量：fontSize 13（工程密度）/controlHeight 28/borderRadius 6/
 *     fontFamily UI 栈+fontFamilyCode 等宽（工程数值对齐——Cascadia
 *     Code 系）——B4 密度冻结值不动（仅换色不换密度）；
 *   - cssVar：antd v6 默认已开 CSS 变量模式（显式 true 的类型面为
 *     {prefix/key} 对象——省略即默认开，运行时样式零重编译）；
 *   - components 微调：Layout 头底同页面底 #f5f6f8/sider 面板底
 *     #fafbfc+Tabs 墨条=AC 蓝（选中指示）+Table 表头/悬停 #f0f2f5
 *     （数据密度面基线；colorSplit=#e8eaed——亮底分割灰，Table 面
 *     该 token 仅消费于 fix 列阴影+虚拟滚动条[未用]，覆写不泄漏表
 *     分割线；列宽/格式化随 C2 方案表重制落 SolutionsTable 组件）；
 *   - QueryClient 默认项在 ./queryClient（D3 领域错误 retry 口径）；
 *     StrictMode 双挂载安全：模块级单例（组件外创建）。
 *   - 2A5：themeConfig 导出=联动机检测试消费面〔GR-39 锚〕
 *     （消费面=app/themeLinkage.test.ts 同值断言——GR-39 联动清单机检化；
 *     导出零行为变更：模块级 const 导出不改求值时序与引用）。
 */
import { QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, theme } from "antd";
import type { ThemeConfig } from "antd";

import { installDomainColorAxis } from "../shared/ui/semanticColors";
import { createQueryClient } from "./queryClient";

// 批6n UF-53：域色 CSS 变量轴启动期注入（模块装载期执行——先于首帧；
// 真源=semanticColors DOMAIN_COLORS，global.css :root 域色字面量已退役）
installDomainColorAxis();

// 模块级唯一实例（D2「组件外创建」——StrictMode 双挂载共享同一 client）
const queryClient = createQueryClient();

/** 主题骨架配置（B4 亮色基线——plan §三分层白色板；值源=shellV4
 *  v4LightTheme〔B1 视觉验收 PASS 面〕。C1 期方向 A 暗色冻结值整体退役
 *  ——仅亮色无双主题。密度三值=fontSize 13/controlHeight 28/
 *  borderRadius 6 为 M1 冻结值不动。 */
export const themeConfig: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#1677ff",
    colorInfo: "#1677ff",
    colorLink: "#1677ff",
    colorBgLayout: "#f5f6f8",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#ffffff",
    colorBorder: "#d6d9de",
    colorBorderSecondary: "#e8eaed",
    colorText: "#1f2329",
    colorTextSecondary: "#646a73",
    colorTextTertiary: "#8a93a0",
    colorSuccess: "#2e7d32",
    colorWarning: "#8a6100",
    colorError: "#b3261e",
    borderRadius: 6,
    controlHeight: 28,
    fontSize: 13,
    fontFamily:
      '"Segoe UI", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif',
    fontFamilyCode:
      '"Cascadia Code", "JetBrains Mono", Consolas, monospace',
  },
  components: {
    Layout: {
      headerBg: "#f5f6f8",
      headerHeight: 48,
      siderBg: "#fafbfc",
      bodyBg: "#f5f6f8",
    },
    Tabs: {
      // G1-02 B4 更新：墨条=AC 蓝选中指示（原暗期鎏金退役——装饰金面
      // 单源=global.css 轴）。页签三态（未选=次档灰 #646a73/悬浮按压=
      // 深文 #1f2329/选中=AC #1677ff）；antd token 为 JS 字面量无法
      // var() 引轴——itemColor/itemHover/Active 与 global.css
      // --wp-text-2/--wp-text 同值双源（A2-N-01 联动清单成员），
      // itemSelectedColor 与 colorPrimary 同值（AC 锚）。渐变下划线/
      // 选中字重=global.css scoped 面（::after 路线，见彼处注记）。
      inkBarColor: "#1677ff",
      horizontalItemPadding: "10px 14px",
      itemColor: "#646a73",
      itemHoverColor: "#1f2329",
      itemActiveColor: "#1f2329",
      itemSelectedColor: "#1677ff",
    },
    Table: {
      // C2 沿革：表头/悬停=BG-3 灰；colorSplit 亮底分割灰（原暗期
      // 深蓝透明派生退役；Table 面该 token 仅消费于 fix 列阴影+
      // 虚拟滚动条[未用]，组件级覆写不泄漏表分割线）
      headerBg: "#f0f2f5",
      rowHoverBg: "#f0f2f5",
      colorSplit: "#e8eaed",
    },
  },
};

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {/* P0-2 顺手收口（F10/教训 24）：两汉字按钮自动插空格根除（「应 用」
          →「应用」——antd Button 默认在中日韩两字符间插半角空格；SSR 测试
          实证：方案表应用钮「应 用」）。antd v6 面=ConfigProvider button
          prop（theme.components.Button.autoInsertSpace 为已弃用旧位）。 */}
      <ConfigProvider theme={themeConfig} button={{ autoInsertSpace: false }}>
        {children}
      </ConfigProvider>
    </QueryClientProvider>
  );
}
