/**
 * QueryClient 工厂与 retry 策略（app 层地基纯函数面——从 providers 拆出，
 * node 测试不拖 antd import 链）。
 *
 * 输入:  无参工厂（D2 冻结默认项常量+领域错误判别 WaterprintApiError）
 * 输出:  retryPolicy（TanStack retry 同签名策略函数）+ createQueryClient()
 *
 * 规格说明（FE3 批 6b 段一，D2/D3 实装）：
 *   - D3 retry 领域错误口径：WaterprintApiError=服务端已组织错误体（4xx
 *     主集合，含 404 无结果集指引/422 校验）重试无益且 404 指引语义要求
 *     立即呈现，一律不重试；非领域错误（TypeError 网络族）最多重试 1 次
 *     （count<1）。providers 规格头原措辞「retry 1（4xx 不重试）」按此
 *     领域错误口径实现——差异记档于此；
 *   - D2 冻结默认项全落地：staleTime 0（工程工具不展示陈旧快照）、
 *     refetchOnWindowFocus false（切窗不闪数据）；
 *   - 「QueryClient 在组件外创建」遵行：providers 以模块级单例消费本工厂
 *     （工厂保持每次新实例——测试互不污染缓存）。
 */
import { QueryClient } from "@tanstack/react-query";

import { WaterprintApiError } from "../shared/api/http";

/** retry 策略（D3 领域错误口径）：领域错误一律不重试；非领域错误最多 1 次。 */
export const retryPolicy = (
  failureCount: number,
  error: unknown,
): boolean => !(error instanceof WaterprintApiError) && failureCount < 1;

/** QueryClient 工厂：D2 冻结默认项（staleTime 0/refetchOnWindowFocus false）。 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 0,
        retry: retryPolicy,
        refetchOnWindowFocus: false,
      },
    },
  });
}
