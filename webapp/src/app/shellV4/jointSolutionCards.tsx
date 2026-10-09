/**
 * v4 右栏联合方案卡（B2 结果与方案批 2026-10-09——任务书 §三.1：「全厂」
 * 页联合方案卡组壳=数据接真〔?task= 联合枚举任务→combos〕；多单元同步
 * 回填=前端逐单元 apply 序列——apply 现行单单元契约〔solution.py〕，
 * 序列形落批档申报；wireframe-d-v4 屏 3 右栏形）。
 *
 * 输入:  projectId+?task= 任务轨（parseTaskParam+TASK_EVENT 重读）+任务
 *        快照（kind=joint_enumerate&&done 门）+narrowJointResult（载荷
 *        窄化——非法形状错误面）+comboSummaryText（参数摘要单源复用）
 * 输出:  联合方案卡列：J 编号/参数摘要/★首位；点卡=逐单元 apply 序列
 *        （每单元原子写+触发重算——末任务 ?task= 回写+TASK_EVENT）；
 *        空态=「联合方案在联合枚举后呈现」（白名单：空态引导）
 *
 * 规格说明（B2 任务书 §三.1+§二.②）：
 *   - 联合多单元回填=前端逐单元 apply 序列（现行单单元契约——序列内每
 *     步原子，末步后失效 project 键全量刷新；中间重算任务被末步覆盖=
 *     dock 任务条最新语义，代价面落批档申报）；
 *   - combos 空=无解合法终态（枚举同款语义）→空态引导。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { comboSummaryText } from "../../features/solutions/lib/jointCharts";
import { narrowJointResult, type JointResultView } from "../../features/solutions/lib/jointView";
import {
  useApplySolutionApiCalcSolutionsApplyPost,
  useGetTaskStatusApiCalcTasksTaskIdGet,
} from "../../shared/api/generated/calc/calc";
import type { WaterprintApiError } from "../../shared/api/http";
import { TASK_EVENT } from "../../shared/events";
import { parseTaskParam } from "../projectParam";
import { writeTaskParam } from "../solutionsUrlState";

/** 空态引导文案（白名单：空态引导）。 */
const NO_JOINT_HINT = "联合方案在联合枚举后呈现";

export function JointSolutionCards({
  projectId,
  onApplied,
}: {
  projectId: string | null;
  /** 数据流①回填标注上抛（逐单元序列每步上抛——左栏回填区消费）。 */
  onApplied: (source: { unitId: string; no: string }) => void;
}) {
  // ?task= 任务轨（TASK_EVENT 重读——URL 单一真相；dockBar 同制）
  const [jointTaskId, setJointTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search),
  );
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseTaskParam(window.location.search);
      setJointTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(jointTaskId ?? "", {
    query: { enabled: jointTaskId !== null },
  });
  const status = statusQuery.data ?? null;
  const jointDone =
    status !== null && status.kind === "joint_enumerate" && status.state === "done";
  // 窄化门（非法载荷→错误面——jointView 单源）
  const view = useMemo<JointResultView | null>(() => {
    if (!jointDone) {
      return null;
    }
    try {
      return narrowJointResult(status?.result ?? null);
    } catch {
      return null;
    }
  }, [jointDone, status?.result]);

  const queryClient = useQueryClient();
  const apply = useApplySolutionApiCalcSolutionsApplyPost<WaterprintApiError>();
  const [busy, setBusy] = useState(false);

  /** 点卡=逐单元 apply 序列（多单元同步回填——末任务回写+全量失效）。 */
  const pick = async (index: number, comboParams: Record<string, Record<string, number>>) => {
    if (projectId === null || busy) {
      return;
    }
    setBusy(true);
    let lastTaskId: string | null = null;
    try {
      for (const [unitId, params] of Object.entries(comboParams)) {
        const outcome = await apply.mutateAsync({
          data: { project_id: projectId, unit_id: unitId, params },
        });
        lastTaskId = outcome.recalc_task_id;
        onApplied({ unitId, no: `J${String(index + 1).padStart(2, "0")}` });
      }
    } catch {
      // 序列中断：已写单元保留（每步原子）——错误面提示重试（白名单）
    } finally {
      setBusy(false);
      void queryClient.invalidateQueries({
        queryKey: [`/api/projects/${projectId}`],
      });
      if (lastTaskId !== null) {
        writeTaskParam(lastTaskId);
        window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: lastTaskId }));
      }
    }
  };

  const combos = view?.combos ?? [];
  return (
    <section className="wp-v4-sec" data-testid="wp-v4-joint-cards">
      <h4>
        全厂 · 联合方案
        {combos.length > 0 ? `（联合枚举 ${combos.length}）` : ""}
      </h4>
      {view === null || combos.length === 0 ? (
        <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>{NO_JOINT_HINT}</span>
      ) : (
        <>
          {combos.slice(0, 8).map((combo, index) => {
            const no = `J${String(index + 1).padStart(2, "0")}`;
            return (
              <button
                key={no}
                type="button"
                data-testid={`wp-v4-joint-card-${no}`}
                disabled={busy}
                onClick={() => void pick(index, combo.params)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  width: "100%",
                  textAlign: "left",
                  border: "1px solid var(--wp-border-2)",
                  borderRadius: 6,
                  background: "var(--wp-bg-container, #ffffff)",
                  padding: "6px 8px",
                  marginBottom: 6,
                  cursor: busy ? "default" : "pointer",
                  fontSize: 11,
                  color: "var(--wp-text)",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--wp-font-mono)",
                    color: "var(--wp-text-2)",
                    flex: "none",
                  }}
                >
                  {no}
                </span>
                <span
                  title={comboSummaryText(combo)}
                  style={{
                    minWidth: 0,
                    flex: 1,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {comboSummaryText(combo)}
                </span>
                {index === 0 ? (
                  <span
                    style={{
                      flex: "none",
                      fontSize: 10,
                      color: "var(--wpv4-ok)",
                    }}
                  >
                    ★
                  </span>
                ) : null}
              </button>
            );
          })}
          {apply.isError ? (
            <div style={{ fontSize: 11, color: "var(--wp-error)" }}>
              联合方案应用失败：
              {apply.error instanceof Error ? apply.error.message : "未知错误"}
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
