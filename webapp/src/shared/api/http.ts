/**
 * orval 请求实例（mutator）：请求基底、错误归一化到领域错误码。
 *
 * 输入:  (url, init)（orval 8 生成代码传入：url=完整路径含查询串；
 *        init=RequestInit 形——method/headers/body/signal）
 * 输出:  Promise<T>（业务数据；错误统一抛 WaterprintApiError）
 *
 * 规格说明（R2 C1 纠偏 2026-08-28：基底恒空——orval 生成 url 已含
 *   /api 前缀（openapi path 锚面），禁二次前拼（曾致全端点 /api/api 404）；
 *   vite 代理/反代按 /api 键原样透传，同源约定不变）：
 *   - GOV5-1（orval 8 迁移）：mutator 签名 (url, RequestInit) 双参——
 *     查询串改由生成侧 getUrl 拼接（原 withQuery 逻辑上收生成器），
 *     JSON body 生成侧已 stringify 且 Content-Type 已拼入 headers；
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
 *   - 本文件是 shared/api 中唯一允许手写的文件；generated/ 禁手改；
 *   - B15 增 409 锁冲突判定面（LOCK_HINT/isLockConflict——自
 *     solutionsFields 上移单源；口径源=UX2 AssumptionsPanel D3）。
 */

import { AUTH_EVENT } from "../events";
import { getApiToken } from "./token";

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

export const customInstance = <T>(url: string, init: RequestInit): Promise<T> => {
  const path = `${BASE_URL}${url}`;
  // R2-A 批2 D3：token 同步现读——非空拼 Bearer（空=零注入零行为变化）；
  // 生成侧 headers 已含 Content-Type 等静态面（plain object 形态直并）
  const apiToken = getApiToken();
  const headers: Record<string, string> = {
    ...((init.headers as Record<string, string> | undefined) ?? {}),
  };
  if (apiToken !== null) {
    headers.Authorization = `Bearer ${apiToken}`; // token 运行期真相（orval 面无显式 Authorization）
  }
  return fetch(path, {
    ...init,
    headers,
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
          : `请求失败：${init.method ?? "GET"} ${path} → ${response.status}`;
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
        `响应解析失败：${init.method ?? "GET"} ${path} → ${response.status}（2xx 非 JSON 体）`,
        error instanceof Error ? error.message : String(error),
      );
    }
  });
};

/** 409 锁冲突保守提示（CP2 D2——照 UX2 AssumptionsPanel 口径不 force 不重试；
 *  B15 自 features/solutions/lib/solutionsFields.ts 上移收敛——原 AssumptionsPanel
 *  本地双实现销账，判定语义单源）。 */
export const LOCK_HINT = "项目已被他处修改，请刷新后重试（并发写锁守门——不自动覆盖）";

/** 409 面=锁文件冲突（server error_type=ProjectLockedError；HTTP_409 兜底）。 */
export function isLockConflict(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "ProjectLockedError" || error.code === "HTTP_409")
  );
}
