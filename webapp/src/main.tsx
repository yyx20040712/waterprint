/**
 * 应用引导：挂载 React 根（骨架期最小接线，非业务代码）。
 *
 * 输入: ./app/App + ./app/global.css（C1 全局样式底座——body 底色/滚动
 *       根除/变量轴，引入一次全树生效）
 * 输出: #root 挂载点
 *
 * 规格说明（骨架冻结；C1 批 2026-09-10 增 global.css 引入——全库首个
 *   CSS 文件，此前纯 inline style）：
 *   - Provider 组合（AntD ConfigProvider 深色 / QueryClient）在
 *     src/app/providers.tsx 组装（M0 接线期创建），main 只做挂载+样式底座；
 *   - StrictMode 保持开启（§11 R14：暴露副作用问题）；
 *   - P1-1（fix-plan 批4 E2E-5 2026-09-25）：根级 ErrorBoundary 兜底——
 *     Header/Sider/StatusBar/ChatPane 在全部面板边界之外，这些区域一次
 *     渲染异常=整树白屏；根边界=最后防线（降级 UI 非吞错，上报通道同
 *     feature 级）。
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import { ErrorBoundary } from "./app/ErrorBoundary";
import "./app/global.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary label="应用根">
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
