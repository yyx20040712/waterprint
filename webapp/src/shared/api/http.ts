/**
 * orval 请求实例（mutator）：请求基底、错误归一化到领域错误码。
 *
 * 输入:  fetch 选项（orval 生成代码传入：url/method/params/headers/data/signal）
 * 输出:  Promise<T>（业务数据；错误统一抛 WaterprintApiError）
 *
 * 规格说明（R2 C1 纠偏 2026-08-28：基底恒空——orval 生成 url 已含
 *   /api 前缀（openapi path 键面），禁二次前拼（曾致全端点 /api/api 404）；
 *   vite 代理/反代按 /api 键原样透传，同源约定不变）：
 *   - 错误归一化：HTTP 状态 + 服务端领域异常字段 → WaterprintApiError
 *     {code, message, detail}（code=服务端 error_type，无则 HTTP_<status>；
 *     message=统一错误体 detail 文本；成功路径 2xx 非 JSON 体同归一——
 *     M3 对称面；422 附字段路径清单由 detail 承载）；
 *   - R2-A 批2 D3 Bearer 注入：请求面 getApiToken() 同步现读——非空则
 *     拼 Authorization: Bearer <token>（空=零注入零行为变化；token.ts
 *     localStorage 单一真相，设置页保存即时生效）；
 *   - R2-A 批2 D4 401 通知：响应面 status===401 先 window.dispatchEvent
 *     (AUTH_EVENT) 再走既有归一化 throw（错误语义零变化仅加通知面——
 *     App.tsx 监听自动开连接设置 Modal=错 token 自愈回路；node 测试
 *     环境无 window——typeof 守卫零派发）；
 *   - SSE 订阅不走本实例（EventSource 直连 /api/events/*——冻结方向
 *     不变；token 面由 useTaskFeed 以 ？token= 查询参数对齐）；
 *   - 本文件是 shared/api 中唯一允许手写的文件；generated/ 禁手改。
 */

import { AUTH_EVENT } from "../events";
import { getApiToken } from "./token";

/** orval 生成端点调用传入的请求配置（fetch 客户端面——url 相对基地）。 */
export type CustomInstanceConfig = {
  url: string;
  method: string;
  params?: Record<string, unknown> | unknown;
  headers?: Record<string, string>;
  data?: unknown;
  signal?: AbortSignal;
};

/** 领域错误（结构面冻结：code/message/detail——结构化消费，禁散落判断）。 */
export class WaterprintApiError extends Error {
  readonly code: string;
  readonly detail?: unknown;

  constructor(code: string, message: string, detail?: unknown) {
    super(message);
    this.name = "WaterprintApiError";
    this.code = code;
    this.detail = detail;
  }
}

// 请求基底恒空（R2 C1）：orval 生成 url 已含 /api 前缀——禁二次前拼。
const BASE_URL = "";

function withQuery(url: string, params: unknown): string {
  if (!params || typeof params !== "object") {
    return url;
  }
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params as Record<string, unknown>)) {
    if (value === undefined || value === null) {
      continue; // 可选参数缺省不进查询串（condition_key 缺省=服务端排序首键）
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        search.append(key, String(item));
      }
    } else {
      search.append(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

export const customInstance = <T>(config: CustomInstanceConfig): Promise<T> => {
  const path = withQuery(config.url, config.params);
  const isJsonBody = config.data !== undefined && config.data !== null;
  // R2-A 批2 D3：token 同步现读——非空拼 Bearer（空=零注入零行为变化）
  const apiToken = getApiToken();
  const headers: Record<string, string> = {
    ...(isJsonBody ? { "Content-Type": "application/json" } : {}),
    ...config.headers,
  };
  if (apiToken !== null) {
    headers.Authorization = `Bearer ${apiToken}`; // token 运行期真相（orval 面无显式 Authorization）
  }
  return fetch(`${BASE_URL}${path}`, {
    method: config.method,
    headers,
    body: isJsonBody ? JSON.stringify(config.data) : undefined,
    signal: config.signal,
  }).then(async (response) => {
    if (!response.ok) {
      // R2-A 批2 D4：401 先派发 AUTH_EVENT 再走既有归一化 throw
      // （node 测试环境无 window——守卫零派发，错误语义不变；次序由
      // http.test.ts 时序标记断言锁——R 轮 G1-04）
      if (response.status === 401 && typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent(AUTH_EVENT));
      }
      // 错误归一化：服务端统一错误体 {detail, error_type} → WaterprintApiError
      let payload: unknown = null;
      try {
        const text = await response.text();
        payload = text ? JSON.parse(text) : null;
      } catch {
        payload = null; // 非 JSON 错误体（网关页等）——detail 留空
      }
      const body =
        payload && typeof payload === "object"
          ? (payload as Record<string, unknown>)
          : {};
      const code =
        typeof body.error_type === "string" ? body.error_type : `HTTP_${response.status}`;
      const rawDetail = body.detail;
      const message =
        typeof rawDetail === "string" && rawDetail
          ? rawDetail
          : `请求失败：${config.method} ${path} → ${response.status}`;
      throw new WaterprintApiError(code, message, payload ?? undefined);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    const text = await response.text();
    if (!text) {
      return undefined as T;
    }
    // M3 对称面：成功路径 2xx 非 JSON 体同归一（禁裸 SyntaxError 面世）
    try {
      return JSON.parse(text) as T;
    } catch (error) {
      throw new WaterprintApiError(
        `HTTP_${response.status}`,
        `响应解析失败：${config.method} ${path} → ${response.status}（2xx 非 JSON 体）`,
        error instanceof Error ? error.message : String(error),
      );
    }
  });
};
