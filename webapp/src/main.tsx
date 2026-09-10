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
 *   - StrictMode 保持开启（§11 R14：暴露副作用问题）。
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import "./app/global.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
