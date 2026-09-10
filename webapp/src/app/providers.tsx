/**
 * Provider 组合：AntD ConfigProvider（C1 主题骨架全量 token）+ QueryClient。
 *
 * 输入:  子组件树
 * 输出:  QueryClientProvider+ConfigProvider 包裹的子组件树
 *
 * 规格说明（FE3 批 6b 段一 D2 实装；C1 批 2026-09-10 主题骨架重制——
 *   方向 A「深海工程台」冻结值，呈裁通过[用户裁选 2026-09-10]）：
 *   - 深色主题锁定（用户裁选：一期锁定暗色——多层暗底难映射亮色，
 *     亮色切换维持 UX 批挂账；原「亮色经 zustand UI slice」注记同步
 *     挂账化）：algorithm=darkAlgorithm+全量 seed token 覆盖；
 *   - token 层级：seed 色（colorPrimary 工程蓝 #3d8bfd）+三层底
 *     （Layout #0b1526 页面/Container #12213a 面板/Elevated #1a2d4d
 *     浮层——纵深层级感）+文字三档（#e8eef7/#9db0c9/#5d7290——对比度
 *     达标）+语义三色（成功/警告/错误——语义色纪律 §19：绿合格/橙警告/
 *     红错误）；鎏金/水线/泥线三色无 antd token 槽位→global.css 变量轴
 *     （--wp-gold/--wp-water/--wp-sludge——单一真相源，inline 消费点经
 *     var() 引用）；
 *   - 度量：fontSize 13（工程密度）/controlHeight 28/borderRadius 6/
 *     fontFamily UI 栈+fontFamilyCode 等宽（工程数值对齐——Cascadia
 *     Code 系）；
 *   - cssVar：antd v6 默认已开 CSS 变量模式（显式 true 的类型面为
 *     {prefix/key} 对象——省略即默认开，运行时样式零重编译）；
 *   - components 微调：Layout 头底分离（headerBg 深一档 #0a1220）+
 *     Tabs 墨条=鎏金（选中指示——品牌点缀）+Table 表头/悬停（数据密度
 *     面基线；列宽/格式化=二期方案标签重制）；
 *   - QueryClient 默认项在 ./queryClient（D3 领域错误 retry 口径）；
 *     StrictMode 双挂载安全：模块级单例（组件外创建）。
 */
import { QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, theme } from "antd";
import type { ThemeConfig } from "antd";

import { createQueryClient } from "./queryClient";

// 模块级唯一实例（D2「组件外创建」——StrictMode 双挂载共享同一 client）
const queryClient = createQueryClient();

/** C1 主题骨架配置（方向 A「深海工程台」冻结值——视觉稿 c1-design）。 */
const themeConfig: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#3d8bfd",
    colorInfo: "#3d8bfd",
    colorLink: "#7ab2ff",
    colorBgLayout: "#0b1526",
    colorBgContainer: "#12213a",
    colorBgElevated: "#1a2d4d",
    colorBorder: "#243a5e",
    colorBorderSecondary: "#1b2c49",
    colorText: "#e8eef7",
    colorTextSecondary: "#9db0c9",
    colorTextTertiary: "#5d7290",
    colorSuccess: "#3ddc97",
    colorWarning: "#f5b544",
    colorError: "#ff6b6b",
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
      headerBg: "#0a1220",
      headerHeight: 48,
      siderBg: "#12213a",
      bodyBg: "#0b1526",
    },
    Tabs: {
      inkBarColor: "#d9a94a",
      horizontalItemPadding: "10px 14px",
    },
    Table: {
      headerBg: "#16263f",
      rowHoverBg: "#1c2f52",
    },
  },
};

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={themeConfig}>{children}</ConfigProvider>
    </QueryClientProvider>
  );
}
