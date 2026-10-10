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

// RFC 7230 §6.1 hop-by-hop 头全集（固定族）+ Connection 值点名头（动态族）
const HOP_BY_HOP = new Set([
  "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
  "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade",
]);

function stripHopByHop(headers) {
  const { connection, ...rest } = headers;
  const named = new Set(
    String(Array.isArray(connection) ? connection.join(",") : connection ?? "")
      .split(",").map((t) => t.trim().toLowerCase()).filter(Boolean),
  );
  const out = {};
  for (const [k, v] of Object.entries(rest)) {
    if (HOP_BY_HOP.has(k) || named.has(k)) continue; // Node 入站头已小写化
    out[k] = v;
  }
  return out;
}

function streamFile(res, file, status, type) {
  // 先开流后写头：open 前失败（删除竞态/权限/入口缺失）头未发可回 404；
  // open 后中途失败头已发只能断连——两态都不演化为进程退出
  const stream = createReadStream(file);
  stream.on("open", () => {
    if (res.destroyed || res.writableEnded) { stream.destroy(); return; } // open 前客户端已断
    res.writeHead(status, { "content-type": type });
    stream.pipe(res);
  });
  stream.on("error", (err) => {
    console.error(`[serve-dist-inspect] 读流失败 ${err.code ?? err.message}`);
    if (res.destroyed || res.writableEnded || res.headersSent) res.destroy();
    else { res.writeHead(404, { "content-type": "text/plain" }); res.end("Not Found"); }
  });
  res.on("close", () => { if (!res.writableFinished) stream.destroy(); }); // 客户端早断回收读流（不空跑到 EOF）
}

function handle(req, res) {
  const pathOnly = req.url.split("?")[0];
  if (pathOnly === "/api" || pathOnly.startsWith("/api/")) {
    // hop-by-hop 头双向不转述（固定族+Connection 点名动态族）；帧由本端 pipe 重构
    const proxy = httpRequest(
      { ...API_TARGET, path: req.url, method: req.method, headers: { ...stripHopByHop(req.headers), host: "127.0.0.1:8000" } },
      (up) => {
        res.writeHead(up.statusCode, stripHopByHop(up.headers));
        res.flushHeaders(); // SSE：响应头随 flush 下发，不必等首个事件块
        up.pipe(res);
        up.on("error", () => { if (res.headersSent) res.destroy(); });
        // 上游未竟关闭（SSE 中途死等非 error 路径）——close+!complete 判据（aborted 事件已弃用不依赖）
        up.on("close", () => {
          if (!up.complete) {
            console.error("[serve-dist-inspect] 上游提前断流（close 未竟）");
            if (!res.writableEnded) res.destroy();
          }
        });
    });
    proxy.on("error", (e) => {
      console.error(`[serve-dist-inspect] 反代失败 ${e.code ?? e.message}`);
      if (res.destroyed || res.writableEnded || res.headersSent) { res.destroy(); return; } // 已毁/已发头守卫：不得重写状态行
      res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ detail: `backend unreachable: ${e.code ?? "unknown"}` }));
    });
    res.on("close", () => { if (!res.writableFinished) proxy.destroy(); }); // 异常早断才回收（正常完成不误杀——连接可复用）
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

// listen 失败（端口占用等）显式退出，与启动期预检同风格——不带栈崩溃
server.on("error", (e) => {
  console.error(`[FAIL] 监听失败: ${e.code ?? e.message}（端口 ${PORT}）`);
  process.exit(1);
});

server.listen(PORT, "127.0.0.1", () => {
  const { port } = server.address();
  console.log(`[serve-dist-inspect] http://127.0.0.1:${port}  dist=${ROOT}`);
});
