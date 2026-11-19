/**
 * LLM 配置面封装：orval 生成 hook 薄封装（F1 批 2026-09-25）。
 *
 * 输入:  enabled（Modal 开态门控——false 禁用 config 查询：挂载期零请求扰动）
 * 输出:  { configQuery, saveMutation }（生成面直通；保存成功后 invalidate
 *        config 查询键——configured 状态行/回填面即时反映服务端真值）
 *
 * 规格说明（F1 批）：
 *   - ai_chat 自有封装（features 互禁 import）；config 查询键恒
 *     ['/api/ai/config']（生成键函数同源——invalidate 复用）；
 *   - mutation onSuccess invalidate：PUT 200 后配置面复查（服务端返回
 *     GET 同构投影——状态行翻绿一致性）；
 *   - enabled 门控：壳常驻挂载态下 Modal 未开不发请求（tokenSettings
 *     「零请求扰动」同款纪律）；
 *   - 迁移注记（2026-11-19）：aiconnect 切片整目录退役时本件属本地
 *     chat LLM 三键配置（消费保留端点 /api/ai/config）被连带误删——
 *     恢复迁入 ai_chat（挂载=dockBar AI 对话窗模型配置入口）。
 */
import { useQueryClient } from "@tanstack/react-query";

import {
  getGetConfigApiAiConfigGetQueryKey,
  useGetConfigApiAiConfigGet,
  useUpdateConfigApiAiConfigPut,
} from "../../../shared/api/generated/ai-config/ai-config";

/** LLM 配置查询+保存 mutation（enabled=Modal 开态门控）。 */
export function useAiConfig(enabled: boolean) {
  const queryClient = useQueryClient();
  const configQuery = useGetConfigApiAiConfigGet({
    query: { enabled },
  });
  const saveMutation = useUpdateConfigApiAiConfigPut({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetConfigApiAiConfigGetQueryKey(),
        });
      },
    },
  });
  return { configQuery, saveMutation };
}
