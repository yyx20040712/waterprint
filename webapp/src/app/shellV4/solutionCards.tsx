/**
 * v4 右栏方案卡（B2 结果与方案批 2026-10-09——任务书 §二.②/§一.3：选中
 * 工艺页方案卡列表，双向数据流①点方案→apply 回填+左栏方案驱动标注〔经
 * onApplied 上抛〕②当前参数变更→卡按偏差重排+Δ徽标随动〔前端重算零新
 * server 端点〕；wireframe-d-v4 屏 1 形）。
 *
 * 输入:  projectId+unitId（?node= 选中真相——shellV4 受控）+?enum= 枚举轨
 *        （parseEnumParam+TASK_EVENT 重读——dockBar 同制）+任务快照
 *        （kind=enumerate&&done 门）+useGetSolutions 分页（首页 50）+
 *        narrowGridFields（grid 投影面）+useProjectDesign（当前参数——
 *        apply 后 invalidate 即随动=数据流②反应面）
 * 输出:  方案卡列：标题「{单元名} · 方案（枚举 N）」+⟳钮+卡族〔S 编号/
 *        参数摘要/★推荐=服务端排序首位/Δ徽标=与当前参数偏差——偏差和
 *        升序重排〕；空态三面（未选单元/选中单元无方案集=引导 ⟳/加载中）
 *
 * 规格说明（B2 任务书 §二.②+§二.⑤）：
 *   - 数据流①：点卡→POST /calc/solutions/apply（grid 投影载荷——
 *     buildApplyPayload 同源投影）→invalidate project 键+?task= 回写+
 *     TASK_EVENT+onApplied({unitId,no})（左栏计算回填区方案驱动标注）；
 *   - 数据流②：当前参数=design.nodeParams[unitId]（数值面）——
 *     buildSolutionCards 偏差重排（solutionDeviation 纯函数单源）；
 *   - 枚举单元≠选中单元（?enum= 任务 unit_id 面）=「选中单元无方案集」
 *     空态引导 ⟳（任务书 §二.⑤ 第三态）；
 *   - 文案白名单：空态引导——零教学性文字。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "antd";

import { useProjectDesign } from "../../features/params/api/useProjectDesign";
import { useUnitCatalog } from "../../features/params/api/useUnitCatalog";
import { narrowGridFields } from "../../features/solutions/lib/solutionsFields";
import {
  buildApplyPayload,
  narrowSolutionPage,
} from "../../features/solutions/lib/solutionsView";
import {
  useApplySolutionApiCalcSolutionsApplyPost,
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet,
  useGetTaskStatusApiCalcTasksTaskIdGet,
} from "../../shared/api/generated/calc/calc";
import type { WaterprintApiError } from "../../shared/api/http";
import { TASK_EVENT } from "../../shared/events";
import { parseEnumParam } from "../projectParam";
import { writeTaskParam } from "../solutionsUrlState";
import { buildSolutionCards, type SolutionCard } from "./solutionDeviation";

/** 空态引导文案（白名单：空态引导）。 */
const NO_UNIT_HINT = "在画布中选择单元后，方案在此呈现";
const NO_SOLUTIONS_HINT = "选中单元暂无枚举方案——⟳ 重新枚举生成方案集";

/** 卡片行（重排后序——数据流②）。 */
function CardRow({
  card,
  onPick,
}: {
  card: SolutionCard;
  onPick: (card: SolutionCard) => void;
}) {
  return (
    <button
      type="button"
      data-testid={`wp-v4-solution-card-${card.no}`}
      onClick={() => onPick(card)}
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
        cursor: "pointer",
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
        {card.no}
      </span>
      <span style={{ minWidth: 0, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {card.summary}
      </span>
      {card.recommended ? (
        <span
          style={{
            flex: "none",
            fontSize: 10,
            borderRadius: 3,
            padding: "0 5px",
            color: "var(--wpv4-ok)",
            background: "var(--wpv4-ok-bg)",
          }}
        >
          ★推荐
        </span>
      ) : null}
      {card.deviationTexts.map((text) => (
        <span
          key={text}
          title="按当前参数偏差重排"
          style={{
            flex: "none",
            fontSize: 10,
            borderRadius: 3,
            padding: "0 5px",
            color: "var(--wpv4-warn)",
            background: "var(--wpv4-warn-bg)",
            fontFamily: "var(--wp-font-mono)",
          }}
        >
          {text}
        </span>
      ))}
    </button>
  );
}

export function SolutionCards({
  projectId,
  unitId,
  onOpenEnumerate,
  onApplied,
}: {
  projectId: string | null;
  /** 选中工艺（?node= 真相——与 ?enum= 任务 unit_id 匹配才出卡）。 */
  unitId: string | null;
  /** ⟳ 重新枚举入口（designZone Modal 开启回调）。 */
  onOpenEnumerate: () => void;
  /** 数据流①回填标注上抛（apply 成功即调——左栏计算回填区消费）。 */
  onApplied: (source: { unitId: string; no: string }) => void;
}) {
  // ?enum= 枚举轨（TASK_EVENT 重读——URL 单一真相；dockBar 同制）
  const [enumTaskId, setEnumTaskId] = useState<string | null>(() =>
    parseEnumParam(window.location.search),
  );
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseEnumParam(window.location.search);
      setEnumTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(enumTaskId ?? "", {
    query: { enabled: enumTaskId !== null },
  });
  const status = statusQuery.data ?? null;
  const statusResult = status?.result ?? null;
  const enumerateDone =
    status !== null && status.kind === "enumerate" && status.state === "done";
  // R1 W-失败面族：枚举 failed 终态=错误面（kind 同门内先行判定）
  const enumFailed =
    status !== null && status.kind === "enumerate" && status.state === "failed";
  const enumUnitId =
    enumerateDone &&
    typeof (statusResult as Record<string, unknown> | null)?.["unit_id"] ===
      "string"
      ? String((statusResult as Record<string, unknown>)["unit_id"])
      : null;

  const solutionsQuery = useGetSolutionsApiCalcTasksTaskIdSolutionsGet(
    enumTaskId ?? "",
    { page: 1, size: 50 },
    { query: { enabled: enumerateDone } },
  );
  // D4 窄化门（solutionsView 单源）——rows 值域四类窄化后进偏差面
  const pageView = useMemo(() => {
    const data = solutionsQuery.data as unknown;
    if (data === null || data === undefined) {
      return null;
    }
    try {
      return narrowSolutionPage(data);
    } catch {
      return null;
    }
  }, [solutionsQuery.data]);
  const gridFields = useMemo(
    () => narrowGridFields(statusResult),
    [statusResult],
  );

  const designQuery = useProjectDesign(projectId ?? "");
  const currentValues = useMemo(() => {
    const values =
      unitId !== null ? designQuery.data?.nodeParams[unitId] : undefined;
    const out: Record<string, number> = {};
    for (const [key, value] of Object.entries(values ?? {})) {
      if (typeof value === "number" && Number.isFinite(value)) {
        out[key] = value;
      }
    }
    return out;
  }, [designQuery.data, unitId]);

  const queryClient = useQueryClient();
  const apply = useApplySolutionApiCalcSolutionsApplyPost<WaterprintApiError>();

  /** 数据流①：点卡→apply（原子写+触发重算）→失效+回写+上抛。 */
  const pick = (card: SolutionCard) => {
    if (projectId === null || unitId === null) {
      return;
    }
    apply.mutate(
      { data: buildApplyPayload(card.row, gridFields, projectId, unitId) },
      {
        onSuccess: (outcome) => {
          void queryClient.invalidateQueries({
            queryKey: [`/api/projects/${projectId}`],
          });
          writeTaskParam(outcome.recalc_task_id);
          window.dispatchEvent(
            new CustomEvent(TASK_EVENT, { detail: outcome.recalc_task_id }),
          );
          if (onApplied !== undefined) {
            onApplied({ unitId, no: card.no });
          }
        },
      },
    );
  };

  // 单元中文名（目录真源——标题 {unit 简名}）
  const catalogQuery = useUnitCatalog();
  const unitName = useMemo(() => {
    if (unitId === null) {
      return null;
    }
    return (
      catalogQuery.data?.units.find((entry) => entry.unit_id === unitId)
        ?.name_zh ?? null
    );
  }, [catalogQuery.data, unitId]);

  const cards = useMemo(
    () =>
      pageView !== null && enumUnitId !== null && enumUnitId === unitId
        ? buildSolutionCards(pageView.rows, gridFields, currentValues)
        : [],
    [pageView, enumUnitId, unitId, gridFields, currentValues],
  );

  const noSolutions =
    unitId === null
      ? NO_UNIT_HINT
      : enumUnitId !== null && enumUnitId !== unitId
        ? NO_SOLUTIONS_HINT
        : null;

  return (
    <section className="wp-v4-sec" data-testid="wp-v4-solution-cards">
      <h4>
        {unitId === null
          ? "选中工艺 · 方案"
          : `${unitName ?? unitId} · 方案${
              pageView !== null && cards.length > 0
                ? `（枚举 ${pageView.total}）`
                : ""
            }`}
      </h4>
      <div style={{ display: "flex", gap: 6, paddingBottom: 4 }}>
        <Button
          size="small"
          onClick={onOpenEnumerate}
          data-testid="wp-v4-reenumerate"
          disabled={unitId === null || projectId === null}
        >
          ⟳ 重新枚举…
        </Button>
      </div>
      {unitId !== null && projectId !== null && enumTaskId === null ? (
        <div
          data-testid="wp-v4-solution-empty"
          style={{
            border: "1px dashed var(--wp-border-2)",
            borderRadius: 6,
            padding: "10px 8px",
            color: "var(--wp-text-2)",
            fontSize: 11,
          }}
        >
          {NO_SOLUTIONS_HINT}
        </div>
      ) : noSolutions !== null ? (
        <div
          data-testid="wp-v4-solution-empty"
          style={{
            border: "1px dashed var(--wp-border-2)",
            borderRadius: 6,
            padding: "10px 8px",
            color: "var(--wp-text-2)",
            fontSize: 11,
          }}
        >
          {noSolutions}
        </div>
      ) : enumFailed ? (
        // R1 W-失败面族：枚举 failed=错误提示+⟳ 引导（非恒「方案加载中…」）
        <div
          data-testid="wp-v4-solution-error"
          style={{
            border: "1px dashed var(--wp-border-2)",
            borderRadius: 6,
            padding: "10px 8px",
            color: "var(--wp-error)",
            fontSize: 11,
          }}
        >
          枚举任务失败：
          {status?.error ?? "未知错误"}——⟳ 重新枚举可重提
        </div>
      ) : solutionsQuery.isError ? (
        // R1 W-失败面族：方案分页取数失败=错误提示（白名单）
        <div data-testid="wp-v4-solution-error" style={{ fontSize: 11, color: "var(--wp-error)" }}>
          方案集读取失败：
          {solutionsQuery.error instanceof Error
            ? solutionsQuery.error.message
            : "未知错误"}
        </div>
      ) : cards.length === 0 ? (
        <div style={{ color: "var(--wp-text-2)", fontSize: 11 }}>方案加载中…</div>
      ) : (
        <>
          {cards.map((card) => (
            <CardRow key={card.no} card={card} onPick={pick} />
          ))}
          {pageView !== null && pageView.total > pageView.rows.length ? (
            // N2 截断提示（R1：首 50 行截断诚实呈现）
            <div style={{ fontSize: 10, color: "var(--wp-text-2)" }}>
              共 {pageView.total} 项 · 显示前 {pageView.rows.length}
            </div>
          ) : null}
        </>
      )}
      {apply.isError ? (
        <div style={{ fontSize: 11, color: "var(--wp-error)" }}>
          方案应用失败：
          {apply.error instanceof Error ? apply.error.message : "未知错误"}
        </div>
      ) : null}
    </section>
  );
}
