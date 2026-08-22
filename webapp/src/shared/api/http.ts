/**
 * orval 请求实例（mutator）：请求基底 /api、错误归一化到领域错误码。
 *
 * 输入:  fetch 选项（orval 生成代码传入）
 * 输出:  Promise<T>（业务数据；错误统一抛 WaterprintApiError）
 *
 * 规格说明（骨架冻结）：
 *   - baseURL 恒为 "/api"（vite 代理/反代同源，禁硬编码主机）；
 *   - 错误归一化：HTTP 状态 + 服务端领域异常字段 → WaterprintApiError
 *     {code, message, detail}；422 附字段路径清单（core parse 透传）；
 *   - SSE 订阅不走本实例（EventSource 直连 /api/events/*）；
 *   - 本文件是 shared/api 中唯一允许手写的文件；generated/ 禁手改。
 */
export type WaterprintApiError = {
  code: string;
  message: string;
  detail?: unknown;
};

export const customInstance = <T>(
  _config: RequestInit,
): Promise<T> => {
  void _config;
  throw new Error(
    "骨架未接线：customInstance 待 M0 接线期实现（orval 生成前）",
  );
};
