/**
 * Vite 配置：React 插件 + API 反向代理（本地开发直连 uvicorn）。
 *
 * 输入: 无（构建配置）
 * 输出: dev server / 构建产物（dist/，不入库）
 */
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // SSE 透传：changeOrigin + ws 关闭（SSE 走 http），缓冲由响应头控制
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  // 3D 视图懒加载 chunk（§12.6：独立路由，与画布互不干扰）
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          three: ["three", "@react-three/fiber"],
        },
      },
    },
  },
});
