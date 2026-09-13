/**
 * AI 接入连接封装：orval 生成 hook 薄封装（AI2 批）。
 *
 * 输入:  enabled（Modal 开态——false 禁用 status 查询：挂载期零启动请求扰动）
 * 输出:  { statusQuery, setupMutation }（orval 生成面直通——响应模型确定性
 *        标量面免窄化；setup 成功后 invalidate status 查询键——写入后
 *        状态翻绿即时反映）
 *
 * 规格说明（AI2 批 2026-09-13；useTrustQuery 薄封装先例）：
 *   - aiconnect 自有封装（features 互禁 import）；status 查询键恒
 *     ['/api/ai/connection']（生成键函数同源——invalidate 复用）；
 *   - mutation onSuccess invalidate：POST setup 200 后状态面复查
 *     （服务端 setup 返回路径清单与 status 同真源——翻绿一致性）；
 *   - enabled 门控：App 常驻挂载态下 Modal 未开不发请求（tokenSettings
 *     「零请求扰动」同款纪律）。
 */
import { useQueryClient } from "@tanstack/react-query";

import {
  getGetConnectionStatusApiAiConnectionGetQueryKey,
  useGetConnectionStatusApiAiConnectionGet,
  useSetupConnectionApiAiConnectionSetupPost,
} from "../../../shared/api/generated/ai-connection/ai-connection";

/** AI 接入状态查询+一键接入 mutation（enabled=Modal 开态门控）。 */
export function useAiConnection(enabled: boolean) {
  const queryClient = useQueryClient();
  const statusQuery = useGetConnectionStatusApiAiConnectionGet({
    query: { enabled },
  });
  const setupMutation = useSetupConnectionApiAiConnectionSetupPost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetConnectionStatusApiAiConnectionGetQueryKey(),
        });
      },
    },
  });
  return { statusQuery, setupMutation };
}
