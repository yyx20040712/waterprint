/**
 * 应用引导：挂载 React 根（骨架期最小接线，非业务代码）。
 *
 * 输入: ./app/App
 * 输出: #root 挂载点
 *
 * 规格说明（骨架冻结）：
 *   - Provider 组合（AntD ConfigProvider 深色 / QueryClient）在
 *     src/app/providers.tsx 组装（M0 接线期创建），main 只做挂载；
 *   - StrictMode 保持开启（§11 R14：暴露副作用问题）。
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
