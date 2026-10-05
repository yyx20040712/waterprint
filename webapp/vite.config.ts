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
  // three 依赖独立分块（§12.6 独立路由语义——Scene 懒加载；2A8/UF-58
  // 实证勘正：three 经 canvasPane→ThumbnailStage 静态链首屏实拉，本配置
  // 实际收益=主包减半 1769→778kB+依赖分块缓存粒度，非「首屏免拉」）
  build: {
    rollupOptions: {
      output: {
        // vite 8 类型面收窄：manualChunks 仅函数形（对象形 TS2769）——
        // "three" 子串命中 three/@react-three/troika-three-text 依赖树；收窄
        // 至 node_modules/three 路径实证无效（构建逐字节同——2A8/UF-58）
        manualChunks: (id: string) => (id.includes("three") ? "three" : undefined),
      },
    },
  },
});
