/**
 * 客户端连接 supervisor hook（联机架构第六批 2026-11-19——单例装配：
 * ShellV4 恒挂载一次，状态机转移的单点驱动面）。
 *
 * 输入:  useClientConnectionStore.remoteBase（localStorage 水合——连接/
 *        断开经整页 reload 重建）+useGetMetaApiMetaGet（远程 /api/meta
 *        握手复核——本地态 disabled 零请求）+queryCache 订阅（401→
 *        token_invalid；曾 401 查询 success→恢复 online）
 * 输出:  useClientConnectionSupervisor(): void（零参零渲染——仅副作用）
 *
 * 规格说明（联机第六批——单机/服务端态零行为变）：
 *   - 本地态（remoteBase null）：meta 查询 disabled+两 effect 早退——
 *     零请求零订阅零状态写入（既有单机/服务端行为面原样）；
 *   - 客户端态驱动三面：
 *     ① meta 查询态→connecting/offline/online/version_mismatch
 *        （compareServerVersions 复核——服务器升级后连接中重检；
 *        token_invalid 粘性豁免：meta 豁免端点无 token 也 200，其
 *        pending/data 到达不清凭据失效态——恢复仅经面三）；
 *     ② queryCache error 且 WaterprintApiError code=AuthError/HTTP_401
 *        →token_invalid（401 面 error_type=AuthError——http.ts 归一化
 *        code；HTTP_401 兜底非统一错误体网关面）；
 *     ③ queryCache success 且现态 token_invalid 且该查询曾 401→复核
 *        serverMeta 回 online（换 token/重试后曾失败面首个成功即恢复
 *        ——粘性不悬挂；豁免端点〔units/meta 等〕无 token 也 200，其
 *        success 不构成凭据修复证据不触发恢复）；
 *   - offline 恢复=手动重试（projectsZone 重试钮 invalidate 全量→
 *     meta/数据面重取，本 hook 随查询态自然转移——不设轮询）。
 */
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useGetMetaApiMetaGet } from "../shared/api/generated/meta/meta";
import { WaterprintApiError } from "../shared/api/http";
import { useClientConnectionStore } from "./clientConnectionStore";
import { compareServerVersions } from "./remoteHandshake";

/** 401 域判（统一错误体 error_type=AuthError；HTTP_401 兜底网关面）。 */
function isAuthFailure(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "AuthError" || error.code === "HTTP_401")
  );
}

export function useClientConnectionSupervisor(): void {
  const queryClient = useQueryClient();
  const remoteBase = useClientConnectionStore((state) => state.remoteBase);
  const metaQuery = useGetMetaApiMetaGet({
    query: { enabled: remoteBase !== null },
  });

  // 面一：meta 握手查询态 → connecting/offline/online/version_mismatch
  useEffect(() => {
    if (remoteBase === null) {
      return;
    }
    const store = useClientConnectionStore.getState();
    if (metaQuery.isPending) {
      if (store.phase !== "token_invalid") {
        store.setPhaseConnecting(); // 后台重取（窗口聚焦等）不清凭据失效态
      }
      return;
    }
    if (metaQuery.isError) {
      store.setOffline();
      return;
    }
    if (metaQuery.data !== undefined) {
      if (store.phase === "token_invalid") {
        return; // 凭据粘性：meta 豁免端点成功不抵消受保面 401（恢复仅经面三）
      }
      const check = compareServerVersions(metaQuery.data);
      if (check.ok) {
        store.setOnline(metaQuery.data);
      } else {
        store.setVersionMismatch(metaQuery.data, check);
      }
    }
  }, [remoteBase, metaQuery.isPending, metaQuery.isError, metaQuery.data]);

  // 面二/三：queryCache 401→token_invalid；success→粘性恢复（仅限曾 401
  // 的同一查询——units/meta/runtime 等豁免端点的 success 不抵消凭据失效）
  useEffect(() => {
    if (remoteBase === null) {
      return;
    }
    // 曾鉴权失败的查询键集（恢复判据=该键后续 success——公共只读端点
    // 〔units/meta/assumptions/constraints〕无 token 也能 200，其 success
    // 不构成「凭据已修复」证据，不得触发恢复）
    const authFailedQueries = new Set<string>();
    return queryClient.getQueryCache().subscribe((event) => {
      if (event.type !== "updated") {
        return;
      }
      const store = useClientConnectionStore.getState();
      if (event.action.type === "error") {
        if (isAuthFailure(event.action.error)) {
          authFailedQueries.add(event.query.queryHash);
          store.setTokenInvalid();
        }
        return;
      }
      if (
        event.action.type === "success" &&
        store.phase === "token_invalid" &&
        authFailedQueries.delete(event.query.queryHash)
      ) {
        const recovered = store.serverMeta;
        if (recovered !== null && compareServerVersions(recovered).ok) {
          store.setOnline(recovered);
        }
      }
    });
  }, [remoteBase, queryClient]);
}
