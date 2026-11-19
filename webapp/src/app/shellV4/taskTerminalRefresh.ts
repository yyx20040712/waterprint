/**
 * 任务终态分析面刷新 hook（F1 业务缺陷批 2026-11-19——恒挂载层单点）：
 * 任务流终态（done）失效分析面查询域，翻新提交时刻失效拉回的旧轮值。
 *
 * 输入:  URL ?task=/?enum=（任务轨双参——TASK_EVENT 重读，URL 单一真相）
 *        +projectId（失效域限定）+useTaskFeed（SSE 终态回调）
 * 输出:  useTaskTerminalFaceRefresh（无返回值——shellV4 恒挂载层调用，
 *        终态 done→invalidateQueries(analysisFacesPredicate)）
 *
 * 规格说明（f1-triage 定责：提交时刻失效〔TASK_EVENT→BackfillSection
 *   /analysisPane〕立即 refetch 拉回旧轮值后，终态前无人二次点火——
 *   停留参数页不 remount 即恒旧值，remount 即恢复；缺口=失效时机从未
 *   覆盖任务终态）：
 *   - 恒挂载语义：shellV4 顶层调用（任何 tab 均在场——TaskStrip 仅 ai
 *     页挂载，参数页停留场景由本 hook 承接；与 TaskStrip 任务快照键
 *     失效不冲突——本 hook 只失效分析面域）；
 *   - done 门：终态且有新结果面才失效（failed/cancelled 无新结果不空
 *     转 refetch）；
 *   - 失效域=analysisFacesPredicate 单源（unit-results/compare/trust/
 *     validation——本项目域，他项目键不误伤）；
 *   - SSE 生命周期归 useTaskEventSource 内核（taskId 变更重建/终态即
 *     close——与 TaskStrip 双订阅时两连接各自收流，失效幂等无害）；
 *   - taskId 轨迹同 TaskStrip（?task= 优先 ?enum=，TASK_EVENT 重读同值
 *     早退）。
 */
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTaskFeed } from "../../features/solutions/api/useTaskFeed";
import { TASK_EVENT } from "../../shared/events";
import { parseEnumParam, parseTaskParam } from "../projectParam";
import { useProjectId } from "../useProjectId";
import { analysisFacesPredicate } from "./analysisView";

/** 任务终态分析面刷新（shellV4 恒挂载层——零渲染面，纯失效副作用）。 */
export function useTaskTerminalFaceRefresh(): void {
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();
  const [taskId, setTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search) ??
    parseEnumParam(window.location.search),
  );

  // TASK_EVENT 重读（URL 单一真相——同值早退；TaskStrip 同链）
  useEffect(() => {
    const onTaskParam = () => {
      const next =
        parseTaskParam(window.location.search) ??
        parseEnumParam(window.location.search);
      setTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  useTaskFeed(taskId, (state) => {
    if (state === "done" && projectId !== null) {
      void queryClient.invalidateQueries({
        predicate: analysisFacesPredicate(projectId),
      });
    }
  });
}
