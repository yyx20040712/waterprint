/**
 * v4 左栏计算回填区（B2 结果与方案批 2026-10-09——任务书 §三.2：B1 空态
 * 接真=计算后自动值回填+方案驱动回填标注〔数据流① 落点〕；wireframe 屏 1
 * 「计算回填 · 自动」形）。
 *
 * 输入:  projectId+unitId（?node= 选中）+appliedSource（方案驱动来源——
 *        SolutionCards/JointSolutionCards onApplied 上抛态）+unit_detail
 *        端点（与 AnalysisPane 同键缓存共享——单次取数两面板消费）
 * 输出:  回填区：标题〔计算回填 · 自动｜方案驱动 · S07〕+选中单元计算派生
 *        值行族〔out_dims 满行取值面首 N 行——数据驱动非硬编码〕+空态
 *        （无结果/未选单元/加载中——白名单：空态引导）
 *
 * 规格说明（B2 任务书 §三.2+§二.③）：
 *   - 自动值回填=unit_detail rows 值面（value 非 null 行——首 6 行）；
 *   - 方案驱动标注=appliedSource.unitId 命中选中单元（S/J 编号随行）；
 *     未命中/无来源=「自动」态（计算后回填语义）；
 *   - TASK_EVENT 事件桥失效 unit-detail 前缀键（apply 重算后回填随动）。
 */
import { useEffect, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { formatSolutionValue } from "../../features/solutions/lib/solutionsView";
import { useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet } from "../../shared/api/generated/calc/calc";
import { TASK_EVENT } from "../../shared/events";
import { unitResultsKeyPredicate } from "./analysisView";

/** 回填行上限（首 N 行——面板高度预算；满行面=中区分析表）。 */
const BACKFILL_ROW_LIMIT = 6;

/** 空态引导文案（白名单：空态引导）。 */
const NO_UNIT_HINT = "选择单元后，计算值在此回填";
const NO_RESULT_HINT = "自动值在计算后回填";
/** R1 W-失败面族：查询错误与空态文案区分（白名单：错误提示）。 */
const LOAD_ERROR_PREFIX = "单元结果读取失败";

export function BackfillSection({
  projectId,
  unitId,
  appliedSource,
}: {
  projectId: string | null;
  unitId: string | null;
  /** 方案驱动来源（数据流① 上抛态——null=无方案来源）。 */
  appliedSource: { unitId: string; no: string } | null;
}) {
  const query = useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet(
    projectId ?? "",
    unitId ?? "",
    undefined,
    { query: { enabled: projectId !== null && unitId !== null } },
  );
  const detail = query.data ?? null;

  // TASK_EVENT 事件桥（apply/重算后失效 unit-results 生成键——回填随动；
  // R1a：predicate 域命中 orval 键〔旧前缀字符串键=死键根治〕；与
  // analysisPane 根级监听双挂载幂等）
  const queryClient = useQueryClient();
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          predicate: unitResultsKeyPredicate(projectId),
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  const rowsWithValue = useMemo(
    () => (detail?.rows ?? []).filter((row) => row.value !== null),
    [detail?.rows],
  );
  const sourceTag =
    appliedSource !== null && appliedSource.unitId === unitId
      ? `方案驱动 · ${appliedSource.no}`
      : null;

  return (
    <section
      style={{
        flex: "none",
        borderTop: "1px solid var(--wp-border-2)",
        padding: "6px 10px 8px",
        maxHeight: "40%",
        overflow: "auto",
      }}
      data-testid="wp-v4-backfill"
    >
      <h4
        style={{
          fontSize: 11,
          color: "var(--wp-text-2)",
          letterSpacing: 1,
          margin: "2px 0 4px",
        }}
      >
        计算回填 · {sourceTag ?? "自动"}
      </h4>
      {unitId === null ? (
        <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>{NO_UNIT_HINT}</span>
      ) : query.isError ? (
        // R1 W-失败面族：错误与空态分面（不同 testid——错误=白名单错误提示）
        <span data-testid="wp-v4-backfill-error" style={{ color: "var(--wp-error)", fontSize: 11 }}>
          {LOAD_ERROR_PREFIX}：
          {query.error instanceof Error ? query.error.message : "未知错误"}
        </span>
      ) : rowsWithValue.length === 0 ? (
        <span data-testid="wp-v4-backfill-empty" style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
          {NO_RESULT_HINT}
        </span>
      ) : (
        rowsWithValue.slice(0, BACKFILL_ROW_LIMIT).map((row) => (
          <div
            key={row.field_id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 11,
              lineHeight: 1.8,
            }}
          >
            <span
              title={row.field_id}
              style={{ color: "var(--wp-text-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
            >
              {row.label_zh ?? row.field_id}
            </span>
            <span
              style={{
                fontVariantNumeric: "tabular-nums",
                fontFamily: "var(--wp-font-mono)",
              }}
            >
              {formatSolutionValue(row.value ?? 0)}
              <span style={{ color: "var(--wp-text-2)", marginLeft: 4 }}>{row.dim}</span>
            </span>
          </div>
        ))
      )}
    </section>
  );
}
