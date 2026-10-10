/**
 * 视检会话静态服务（handover-2026-10-08-6 §五前置②——直服 dist 口径）：
 * dist 静态件 + /api 反代 127.0.0.1:8000（含 SSE 透传——响应式 pipe 不落盘
 * 缓冲）。用法：node scripts/serve-dist-inspect.mjs [port=4280]。退出 Ctrl+C。
 */
import { createServer, request as httpRequest } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../webapp/dist/", import.meta.url));
const API_TARGET = { host: "127.0.0.1", port: 8000 };
const PORT = Number(process.argv[2] || 4280);

const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".ico": "image/x-icon", ".woff2": "font/woff2", ".map": "application/json",
};

const server = createServer((req, res) => {
  if (req.url.startsWith("/api/")) {
    const proxy = httpRequest(
      { ...API_TARGET, path: req.url, method: req.method, headers: { ...req.headers, host: "127.0.0.1:8000" } },
      (up) => { res.writeHead(up.statusCode, up.headers); up.pipe(res); },
    );
    proxy.on("error", (e) => {
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ detail: `backend unreachable: ${e.code}` }));
    });
    req.pipe(proxy);
    return;
  }
  let rel = decodeURIComponent(req.url.split("?")[0]);
  if (rel === "/" || rel === "") rel = "/index.html";
  const file = normalize(join(ROOT, rel));
  if (!file.startsWith(normalize(ROOT)) || !existsSync(file) || statSync(file).isDirectory()) {
    // SPA 回退：非资产路径回 index.html（URL 语义刷新恢复面）
    const indexPath = join(ROOT, "index.html");
    res.writeHead(200, { "content-type": MIME[".html"] });
    createReadStream(indexPath).pipe(res);
    return;
  }
  res.writeHead(200, { "content-type": MIME[extname(file)] || "application/octet-stream" });
  createReadStream(file).pipe(res);
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`[serve-dist-inspect] http://127.0.0.1:${PORT}  dist=${ROOT}`);
});
