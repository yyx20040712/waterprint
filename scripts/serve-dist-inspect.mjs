/**
 * 视检会话静态服务（handover-2026-10-08-6 §五前置②——直服 dist 口径）：
 * dist 静态件 + /api 反代 127.0.0.1:8000（含 SSE 透传——响应式 pipe 不落盘
 * 缓冲）。用法：node scripts/serve-dist-inspect.mjs [port=4280]。退出 Ctrl+C。
 */
import { createServer, request as httpRequest } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../webapp/dist/", import.meta.url));
// 前缀比对恒带尾分隔符：裸 startsWith(ROOT) 会放行 dist-evil 一类同前缀兄弟目录
const ROOT_PREFIX = normalize(ROOT + sep);
const API_TARGET = { host: "127.0.0.1", port: 8000 };
const PORT = Number(process.argv[2] || 4280);
if (!Number.isInteger(PORT) || PORT < 0 || PORT > 65535) {
  console.error(`[FAIL] 端口参数非法: ${process.argv[2]}（0~65535 整数）`);
  process.exit(2);
}
const indexPath = join(ROOT, "index.html");
if (!existsSync(indexPath)) {
  console.error(`[FAIL] dist 入口缺失: ${indexPath}——先 npm run build 再启动`);
  process.exit(2);
}

const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".ico": "image/x-icon", ".woff2": "font/woff2", ".map": "application/json",
};

function streamFile(res, file, status, type) {
  res.writeHead(status, { "content-type": type });
  // 读流错误（删除竞态/权限）不得演化为进程退出：头已发则断连，头未发则 404
  createReadStream(file).on("error", () => {
    if (res.headersSent) res.destroy();
    else { res.writeHead(404, { "content-type": "text/plain" }); res.end("Not Found"); }
  }).pipe(res);
}

function handle(req, res) {
  if (req.url === "/api" || req.url.startsWith("/api/")) {
    const proxy = httpRequest(
      { ...API_TARGET, path: req.url, method: req.method, headers: { ...req.headers, host: "127.0.0.1:8000" } },
      (up) => {
        // hop-by-hop 头不由代理转述（Connection 族由本端连接自理）
        const { connection, "keep-alive": keepAlive, "transfer-encoding": te, ...headers } = up.headers;
        res.writeHead(up.statusCode, headers);
        res.flushHeaders(); // SSE：响应头随 flush 下发，不必等首个事件块
        up.pipe(res);
        up.on("error", () => { if (res.headersSent) res.destroy(); });
      },
    );
    proxy.on("error", (e) => {
      if (res.headersSent) { res.destroy(); return; } // 中途断流守卫：不得对已发头响应重写 502
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ detail: `backend unreachable: ${e.code ?? "unknown"}` }));
    });
    res.on("close", () => proxy.destroy()); // 客户端断开（关 SSE 页签）即时回收上游连接
    req.pipe(proxy);
    return;
  }
  let rel;
  try { rel = decodeURIComponent(req.url.split("?")[0]); }
  catch { res.writeHead(400, { "content-type": "text/plain" }); res.end("Bad Request"); return; }
  if (rel === "/" || rel === "") rel = "/index.html";
  const file = normalize(join(ROOT, rel));
  const outside = !file.startsWith(ROOT_PREFIX);
  if (outside || !existsSync(file) || statSync(file).isDirectory()) {
    // 带扩展名的资产形态路径 404（缺失资产不静默转 200 HTML——保视检诊断力）；
    // 无扩展名路径=前端路由形态，SPA 回退 index.html（URL 语义刷新恢复面）
    const ext = extname(rel);
    if (ext && ext !== ".html") { res.writeHead(404, { "content-type": "text/plain" }); res.end("Not Found"); return; }
    streamFile(res, indexPath, 200, MIME[".html"]);
    return;
  }
  streamFile(res, file, 200, MIME[extname(file)] || "application/octet-stream");
}

// handler 内任何未预见异常兜底：进程不退出，单请求 500/断连
const server = createServer((req, res) => {
  try { handle(req, res); }
  catch {
    if (res.headersSent) res.destroy();
    else { res.writeHead(500, { "content-type": "application/json" }); res.end(JSON.stringify({ detail: "internal error" })); }
  }
});

server.listen(PORT, "127.0.0.1", () => {
  const { port } = server.address();
  console.log(`[serve-dist-inspect] http://127.0.0.1:${port}  dist=${ROOT}`);
});
