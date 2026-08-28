/**
 * orval 请求实例（mutator）：请求基底 /api、错误归一化到领域错误码。
 *
 * 输入:  fetch 选项（orval 生成代码传入：url/method/params/headers/data/signal）
 * 输出:  Promise<T>（业务数据；错误统一抛 WaterprintApiError）
 *
 * 规格说明（骨架冻结）：
 *   - baseURL 恒为 "/api"（vite 代理/反代同源，禁硬编码主机）；
 *   - 错误归一化：HTTP 状态 + 服务端领域异常字段 → WaterprintApiError
 *     {code, message, detail}（code=服务端 error_type，无则 HTTP_<status>；
 *     message=统一错误体 detail 文本；422 附字段路径清单由 detail 承载）；
 *   - SSE 订阅不走本实例（EventSource 直连 /api/events/*）；
 *   - 本文件是 shared/api 中唯一允许手写的文件；generated/ 禁手改。
 */

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

const BASE_URL = "/api";

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
  return fetch(`${BASE_URL}${path}`, {
    method: config.method,
    headers: {
      ...(isJsonBody ? { "Content-Type": "application/json" } : {}),
      ...config.headers,
    },
    body: isJsonBody ? JSON.stringify(config.data) : undefined,
    signal: config.signal,
  }).then(async (response) => {
    if (!response.ok) {
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
    return (text ? JSON.parse(text) : undefined) as T;
  });
};
