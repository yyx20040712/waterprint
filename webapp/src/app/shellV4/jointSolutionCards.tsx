/**
 * v4 右栏联合方案卡（B2 结果与方案批 2026-10-09+R1 回炉 R1b 重制——任务书
 * §三.1 数据接真；wireframe-d-v4 屏 3 右栏形）。
 *
 * 输入:  projectId+?task= 任务轨（parseTaskParam+TASK_EVENT 重读）+任务
 *        快照（kind=joint_enumerate&&done 门）+narrowJointResult（载荷
 *        窄化——非法形状错误面）+comboSummaryText（参数摘要单源复用）
 * 输出:  联合方案卡列：J 编号/参数摘要/★首位/截断提示；点卡=逐单元 apply
 *        序列（每单元原子写+触发重算——末任务 ?task= 回写+TASK_EVENT）；
 *        R1b：粘滞 joint 视图（apply 后 ?task= 已变 recalc——卡列不塌空
 *        保持可连点；?task= 深链语义保留给 dock 聚焦）；部分失败=错误面
 *        +重试（全量重发——apply 幂等）；空态=联合枚举后呈现（白名单）
 *
 * 规格说明（B2 任务书 §三.1+§二.②+R1 简报 R1b/d1-W4/W-失败面族）：
 *   - 粘滞视图（R1b 定形）：urlTaskId 仅用于「发现」joint 枚举任务（done
 *     joint→粘滞 id 承载卡面视图——此后 ?task= 变 recalc/任意值卡列不
 *     塌；新 joint 任务出现〔?task= 再指 joint done〕则切换粘滞）；
 *   - 逐单元 apply 序列（现行单单元契约）：每步原子——部分失败=已写
 *     单元保留+错误面呈现+重试钮（重试=全量重发：apply 同参数重写
 *     design_changed=false 无害+新重算任务，无半写风险——幂等处置）；
 *   - 非法载荷（narrowJointResult 拒）=错误面（wp-v4-joint-error——
 *     非伪空态文案）；
 *   - combos 空=无解合法终态→空态引导（枚举同款语义）。
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

/** 空态引导/错误文案（白名单：空态引导/错误提示）。 */
const NO_JOINT_HINT = "联合方案在联合枚举后呈现";
const BAD_PAYLOAD_HINT = "联合枚举结果载荷非法——重新联合枚举生成";
const JOINT_CARD_LIMIT = 8;

/** R2a 粘滞持久键（按项目键——sessionStorage：跨右栏切页卸载/zone 切换/
 *  刷新三径均稳；跨项目键隔离=R2b 半面）。 */
const stickyKeyOf = (projectId: string) => `wp-v4-joint-sticky-${projectId}`;

/** R3 W-B 存储降级内存面（隐私模式/禁存储抛 SecurityError——粘滞为增强
 *  面，存储不可用则内存 Map 降级承载，禁白屏级崩溃）。 */
const stickyMemoryFallback = new Map<string, string>();
const readStickyEntry = (projectId: string | null): string | null => {
  if (projectId === null) {
    return null;
  }
  const key = stickyKeyOf(projectId);
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return stickyMemoryFallback.get(key) ?? null;
  }
};
const writeStickyEntry = (projectId: string, taskId: string) => {
  const key = stickyKeyOf(projectId);
  try {
    window.sessionStorage.setItem(key, taskId);
  } catch {
    stickyMemoryFallback.set(key, taskId);
  }
};
const clearStickyEntry = (projectId: string) => {
  const key = stickyKeyOf(projectId);
  try {
    window.sessionStorage.removeItem(key);
  } catch {
    /* 存储不可用面——内存键同步清 */
  }
  stickyMemoryFallback.delete(key);
};

/** 粘滞态（R3 W-A：携 owner 域——stickyId 派生=owner===projectId 才生效，
 *  原位 prop 变更竞态帧旧粘滞自动失效〔drift-clear 不触发〕，换键读
 *  effect 独立串行）。 */
type StickyState = { owner: string; taskId: string } | null;

export function JointSolutionCards({
  projectId,
  onApplied,
}: {
  projectId: string | null;
  /** 数据流①回填标注上抛（逐单元序列每步上抛——左栏回填区消费；
   *  N3 声明：序列终态=末单元〔对象语义=末写胜出——落批档〕）。 */
  onApplied: (source: { unitId: string; no: string }) => void;
}) {
  // ?task= 任务轨（TASK_EVENT 重读——URL 单一真相；dockBar 同制）
  const [urlTaskId, setUrlTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search),
  );
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseTaskParam(window.location.search);
      setUrlTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  // 粘滞态（R2a 持久+R3 W-A owner 域：派生 stickyId 在换键帧自动失效旧
  // 项目粘滞——drift-clear 不再以旧闭包误删新项目键）
  const [sticky, setStickyState] = useState<StickyState>(() => {
    const taskId = readStickyEntry(projectId);
    return projectId !== null && taskId !== null
      ? { owner: projectId, taskId }
      : null;
  });
  const stickyId =
    sticky !== null && sticky.owner === projectId ? sticky.taskId : null;
  const adoptSticky = (taskId: string | null) => {
    if (projectId === null) {
      return;
    }
    if (taskId === null) {
      setStickyState(null);
      clearStickyEntry(projectId);
    } else {
      setStickyState({ owner: projectId, taskId });
      writeStickyEntry(projectId, taskId);
    }
  };
  // R2b/R3 W-A：projectId prop 变化=换键读（独立 effect 串行——换键帧先
  // 采用新键粘滞，旧项目键不动）
  useEffect(() => {
    const taskId = readStickyEntry(projectId);
    setStickyState(
      projectId !== null && taskId !== null
        ? { owner: projectId, taskId }
        : null,
    );
  }, [projectId]);

  // 发现通道：?task= 指向的 done joint 任务 → 粘滞 id（R1b+R2b：project_id
  // 守卫——他项目任务不收养；?task= 再指另一 done joint 则切换）
  const urlStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(urlTaskId ?? "", {
    query: { enabled: urlTaskId !== null },
  });
  const urlStatus = urlStatusQuery.data ?? null;
  // R2c：?task= 指向的 failed joint 任务=当前错误面（优先于粘滞卡列——
  // 不得以旧结果冒充当前；project_id 守卫同 R2b）
  const urlJointFailed =
    urlStatus !== null &&
    urlStatus.kind === "joint_enumerate" &&
    urlStatus.state === "failed" &&
    projectId !== null &&
    urlStatus.project_id === projectId;
  useEffect(() => {
    if (
      urlStatus !== null &&
      urlStatus.kind === "joint_enumerate" &&
      urlStatus.state === "done" &&
      projectId !== null &&
      urlStatus.project_id === projectId &&
      urlStatus.task_id !== stickyId
    ) {
      adoptSticky(urlStatus.task_id);
    }
  }, [urlStatus, stickyId, projectId]);

  // 视图通道：粘滞 id 优先（缓存共享——与发现通道同键单次取数；R2b：
  // project 守卫统一辖两源〔粘滞/URL 兜底〕——他项目任务拒渲染）
  const viewTaskId = stickyId ?? urlTaskId;
  const viewStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(viewTaskId ?? "", {
    query: { enabled: viewTaskId !== null },
  });
  const viewStatus = viewStatusQuery.data ?? null;
  const viewProjectMismatch =
    viewStatus !== null &&
    (projectId === null || viewStatus.project_id !== projectId);
  useEffect(() => {
    // 粘滞源漂移=清粘滞（他项目键残留/任务重建面）；URL 兜底源不落粘滞
    if (stickyId !== null && viewProjectMismatch) {
      adoptSticky(null);
    }
  }, [stickyId, viewProjectMismatch]);
  const jointDone =
    viewStatus !== null &&
    viewStatus.kind === "joint_enumerate" &&
    viewStatus.state === "done" &&
    !viewProjectMismatch;
  // 窄化门（非法载荷→错误面标记——jointView 单源；memo 内零副作用）
  const { view, badPayload } = useMemo<{
    view: JointResultView | null;
    badPayload: boolean;
  }>(() => {
    if (!jointDone) {
      return { view: null, badPayload: false };
    }
    try {
      return {
        view: narrowJointResult(viewStatus?.result ?? null),
        badPayload: false,
      };
    } catch {
      return { view: null, badPayload: true };
    }
  }, [jointDone, viewStatus?.result]);

  const queryClient = useQueryClient();
  const apply = useApplySolutionApiCalcSolutionsApplyPost<WaterprintApiError>();
  const [busy, setBusy] = useState(false);
  const [seqError, setSeqError] = useState<string | null>(null);
  const [lastPick, setLastPick] = useState<{
    index: number;
    params: Record<string, Record<string, number>>;
  } | null>(null);

  /** 逐单元 apply 序列（R1b：部分失败=错误面+已写保留；重试=全量重发）。 */
  const runSequence = async (
    index: number,
    comboParams: Record<string, Record<string, number>>,
  ) => {
    if (projectId === null || busy) {
      return;
    }
    setBusy(true);
    setSeqError(null);
    setLastPick({ index, params: comboParams });
    let lastTaskId: string | null = null;
    try {
      for (const [unitId, params] of Object.entries(comboParams)) {
        const outcome = await apply.mutateAsync({
          data: { project_id: projectId, unit_id: unitId, params },
        });
        lastTaskId = outcome.recalc_task_id;
        onApplied({
          unitId,
          no: `J${String(index + 1).padStart(2, "0")}`,
        });
      }
    } catch (error) {
      // 部分失败：已写单元保留（每步原子）；错误面+重试（白名单错误提示）
      setSeqError(error instanceof Error ? error.message : "未知错误");
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
  const truncateNote =
    combos.length > JOINT_CARD_LIMIT
      ? `共 ${combos.length} 项 · 显示前 ${JOINT_CARD_LIMIT}`
      : null;
  return (
    <section className="wp-v4-sec" data-testid="wp-v4-joint-cards">
      <h4>
        全厂 · 联合方案
        {combos.length > 0 ? `（联合枚举 ${combos.length}）` : ""}
      </h4>
      {urlJointFailed ? (
        // R2c：failed joint=当前错误面（优先于粘滞卡列——旧结果不冒充当前）
        <div
          data-testid="wp-v4-joint-error"
          style={{ fontSize: 11, color: "var(--wp-error)" }}
        >
          联合枚举任务失败：
          {urlStatus?.error ?? "未知错误"}——重新联合枚举可重提
        </div>
      ) : badPayload ? (
        <div
          data-testid="wp-v4-joint-error"
          style={{ fontSize: 11, color: "var(--wp-error)" }}
        >
          {BAD_PAYLOAD_HINT}
        </div>
      ) : view === null || combos.length === 0 ? (
        <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>{NO_JOINT_HINT}</span>
      ) : (
        <>
          {combos.slice(0, JOINT_CARD_LIMIT).map((combo, index) => {
            const no = `J${String(index + 1).padStart(2, "0")}`;
            return (
              <button
                key={no}
                type="button"
                data-testid={`wp-v4-joint-card-${no}`}
                disabled={busy}
                onClick={() => void runSequence(index, combo.params)}
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
                  // N10：busy=disabled 视觉态（antd 形——禁用降不透明度）
                  opacity: busy ? 0.6 : 1,
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
          {truncateNote !== null ? (
            <div style={{ fontSize: 10, color: "var(--wp-text-2)" }}>{truncateNote}</div>
          ) : null}
          {/* 部分失败错误面+重试（d1-W4——重试=全量重发：apply 幂等） */}
          {seqError !== null ? (
            <div
              data-testid="wp-v4-joint-error"
              style={{
                fontSize: 11,
                color: "var(--wp-error)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span
                style={{
                  minWidth: 0,
                  flex: 1,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                title={seqError}
              >
                联合方案应用失败（已写单元保留）：{seqError}
              </span>
              <button
                type="button"
                data-testid="wp-v4-joint-retry"
                disabled={busy}
                onClick={() => {
                  if (lastPick !== null) {
                    void runSequence(lastPick.index, lastPick.params);
                  }
                }}
                style={{
                  flex: "none",
                  border: "1px solid var(--wp-border)",
                  borderRadius: 4,
                  background: "var(--wp-bg-container, #ffffff)",
                  color: "var(--wpv4-ac)",
                  fontSize: 11,
                  padding: "1px 8px",
                  cursor: busy ? "default" : "pointer",
                }}
              >
                重试
              </button>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
