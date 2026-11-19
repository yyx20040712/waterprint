/**
 * 客户端模式远程基址存取（联机架构第六批 2026-11-19——用户裁决厚客户端
 * 模型：界面本地加载，数据/计算全走远程服务器）。
 *
 * 输入:  setRemoteServer(baseUrl) 的远程服务器地址（http(s)://host[:port]）
 *        /getRemoteBaseUrl()/clearRemoteServer() 零参同步现读
 * 输出:  getRemoteBaseUrl → string|null（null=本地模式——请求基址恒空
 *        零行为变；非 null=已归一化 origin，http.ts/sseUrl.ts 前拼）；
 *        setRemoteServer/clearRemoteServer → void（写后即时生效）；
 *        normalizeRemoteBaseUrl → string|null（归一化纯函数——非法形态
 *        null 单一空态）
 *
 * 规格说明（联机第六批任务书）：
 *   - key=`waterprint.remote_server`（waterprint.* 命名域——api token/
 *     theme 同款）；v1 单服务器档案（JSON {base_url}——多服务器列表是
 *     稿开放问题 8，缺省单档案不在本批造列表面）；
 *   - 归一化：URL 解析后仅认 scheme://host[:port]（http/https、无
 *     path/query/fragment/credentials、尾斜线剥除）——防把任意串前拼
 *     进 fetch URL；非法形态=null（调用方不写不连）；
 *   - 同步现读（token.ts 同制式）：无全局缓存无订阅——消费方（http.ts
 *     请求面/sseUrl.ts SSE 面/app 连接态）每次现取；设置面保存即时
 *     生效（连接动作经整页 reload 重装配——URL 键/缓存键语义：客户端
 *     模式仍是同一应用仅 API origin 变，reload 后全量查询自然重取）；
 *   - 存储脏值防御：读出后过 normalizeRemoteBaseUrl 再放行（手改
 *     localStorage 的畸形值=视同未配置，不向 fetch 面外泄）；
 *   - node 测试环境守卫：typeof localStorage 守卫（undefined 视同未
 *     配置）；存储异常（隐私模式/配额满）保守视同未配置面。
 */

/** 持久化键（v1 单服务器档案——JSON {base_url}）。 */
export const REMOTE_SERVER_STORAGE_KEY = "waterprint.remote_server";

interface RemoteServerProfile {
  base_url: string;
}

/**
 * 远程基址归一化（纯函数）：仅认 http(s)://host[:port] origin 形态。
 *
 * 尾斜线剥除（"http://h:1/" 与 "http://h:1" 同值）；带 path/query/
 * fragment/credentials 或非 http(s) scheme 或不可解析=null（单一空态）。
 */
export function normalizeRemoteBaseUrl(input: string): string | null {
  const trimmed = input.trim();
  if (trimmed === "") {
    return null;
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return null; // 不可解析（缺 scheme 等）——单一空态
  }
  if (
    (parsed.protocol !== "http:" && parsed.protocol !== "https:") ||
    parsed.pathname !== "/" ||
    parsed.search !== "" ||
    parsed.hash !== "" ||
    parsed.username !== "" ||
    parsed.password !== ""
  ) {
    return null;
  }
  return `${parsed.protocol}//${parsed.host}`;
}

/** 读远程基址（null=本地模式——存储缺席/JSON 畸形/形态非法同归 null）。 */
export function getRemoteBaseUrl(): string | null {
  try {
    if (typeof localStorage === "undefined") {
      return null; // node 测试环境守卫
    }
    const raw = localStorage.getItem(REMOTE_SERVER_STORAGE_KEY);
    if (raw === null) {
      return null;
    }
    const parsed = JSON.parse(raw) as Partial<RemoteServerProfile> | null;
    if (parsed === null || typeof parsed.base_url !== "string") {
      return null; // 畸形档案=视同未配置（不外泄给 fetch 面）
    }
    return normalizeRemoteBaseUrl(parsed.base_url);
  } catch {
    return null; // 隐私模式/JSON 损坏：保守视同未配置
  }
}

/** 写远程档案（归一化后落盘——非法形态不写；环境缺席/写失败静默）。 */
export function setRemoteServer(baseUrl: string): void {
  const normalized = normalizeRemoteBaseUrl(baseUrl);
  if (normalized === null) {
    return; // 非法形态拒写（调用方 UI 已先行校验——本层兜底）
  }
  try {
    if (typeof localStorage === "undefined") {
      return;
    }
    const profile: RemoteServerProfile = { base_url: normalized };
    localStorage.setItem(REMOTE_SERVER_STORAGE_KEY, JSON.stringify(profile));
  } catch {
    // 配额满/隐私模式：静默失败（连接流由调用方 reload 前置判读）
  }
}

/** 清除远程档案（回落本地模式；环境缺席/删失败静默）。 */
export function clearRemoteServer(): void {
  try {
    if (typeof localStorage === "undefined") {
      return;
    }
    localStorage.removeItem(REMOTE_SERVER_STORAGE_KEY);
  } catch {
    // 同上：清除失败保守视同已配置面（下次写/清再收敛）
  }
}
