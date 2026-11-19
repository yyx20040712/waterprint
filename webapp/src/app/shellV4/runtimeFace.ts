/**
 * 运行角色面纯函数层（联机架构第五批 2026-11-19——/api/runtime 消费面
 * 共享件：状态栏标识/工作台运行方式卡/运行方式设置 Modal 三处同源）。
 *
 * 输入:  RuntimeInfo（orval 生成类型——/api/runtime 载荷）+window.location
 *        （配对地址端口派生——同源端口即服务端口）
 * 输出:  RUNTIME_FALLBACK_LABEL/runtimeModeLabel（标识文案单源）+
 *        pairingAddressUrl（配对地址 URL 构造）+runtimePrimaryAddress
 *        （配对卡首选地址）+clientStatusLabel/CLIENT_BADGE_LABELS/
 *        remoteHostLabel（客户端模式标识/徽标/主机名三面——联机第六批）
 *
 * 规格说明（第五批任务书——状态栏真实连接态）：
 *   - 失败降级：runtime 未达（请求失败/加载中/角色未知）=单机标识静态
 *     文案（验收口径「读 /api/runtime，失败降级静态单机标识」——未知
 *     不虚报服务端态）；
 *   - 文案单源：standalone=「单机模式 · 本地引擎」/server=「服务端 ·
 *     局域网可被发现」（稿 connection.html statusbar 段）；
 *   - 客户端态（第六批，稿 workbench-remote.html statusbar/徽标段）：
 *     online=「客户端 · 远程 @ 主机」（主机名=remoteHostLabel 单源）；
 *     offline/token_invalid/version_mismatch 显因文案（颜色与文字同时
 *     表达原因——稿 state-card 段）；connecting=连接中；local 态不消费
 *     本组（走 runtimeModeLabel——客户端组仅 phase!==local 消费）；
 *   - 配对地址：lan_addresses 首选（缺席回落 bind_host）+窗口同源端口
 *     （UI 由本服务供出——客户端用同一端口可达；非浏览器环境无端口段）。
 */
import type { RuntimeInfo } from "../../shared/api/generated/model";
import type { ClientPhase } from "../clientConnectionStore";

/** 降级标识（请求失败/加载中/角色未知——单机静态文案不虚报）。 */
export const RUNTIME_FALLBACK_LABEL = "单机模式 · 本地引擎";

/** 角色标识文案单源（稿 connection.html statusbar 段两态）。 */
export const RUNTIME_MODE_LABELS: Record<RuntimeInfo["role"], string> = {
  standalone: "单机模式 · 本地引擎",
  server: "服务端 · 局域网可被发现",
};

/** 状态栏标识文案（runtime 未达=降级单机文案——失败诚实降级）。 */
export function runtimeModeLabel(runtime: RuntimeInfo | undefined): string {
  if (runtime === undefined) {
    return RUNTIME_FALLBACK_LABEL;
  }
  return RUNTIME_MODE_LABELS[runtime.role] ?? RUNTIME_FALLBACK_LABEL;
}

/** 配对地址 URL（同源端口派生——UI 由本服务供出，客户端同端口可达）。 */
export function pairingAddressUrl(address: string): string {
  if (typeof window === "undefined") {
    return `http://${address}`;
  }
  const port = window.location.port;
  return `http://${address}${port ? `:${port}` : ""}`;
}

/** 配对卡首选地址（lan_addresses 首选；空集=null——消费方诚实降级
 *  「未发现局域网地址」，不展示 bind_host〔0.0.0.0 非客户端可连地址〕）。 */
export function runtimePrimaryAddress(
  runtime: RuntimeInfo,
): string | null {
  if (runtime.role !== "server") {
    return null; // standalone=无监听地址语义（配对面缺席）
  }
  return runtime.lan_addresses[0] ?? null;
}

/** 客户端态状态栏标识文案（稿 workbench-remote.html statusbar 段）。 */
export function clientStatusLabel(phase: ClientPhase, hostLabel: string): string {
  if (phase === "online") {
    return `客户端 · 远程 @ ${hostLabel}`;
  }
  if (phase === "offline") {
    return "客户端 · 远程不可达";
  }
  if (phase === "token_invalid") {
    return "客户端 · token 失效";
  }
  if (phase === "version_mismatch") {
    return "客户端 · 版本不匹配";
  }
  return "客户端 · 连接中";
}

/** 客户端态徽标短文案（项目区/运行方式卡徽标——在线绿/异常红由类名承载）。 */
export const CLIENT_BADGE_LABELS: Record<
  Exclude<ClientPhase, "local">,
  string
> = {
  connecting: "客户端 · 连接中",
  online: "客户端 · 在线",
  offline: "远程不可达",
  token_invalid: "token 失效",
  version_mismatch: "版本不匹配",
};

/** 远程主机展示名（URL 解析 hostname——非 URL 形态原样回显，不抛）。 */
export function remoteHostLabel(baseUrl: string): string {
  try {
    return new URL(baseUrl).hostname;
  } catch {
    return baseUrl;
  }
}
