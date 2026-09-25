/**
 * 方案浏览提示组件（批2d 行数预算修——自 solutionsPane 抽取：无解诊断/
 * 漂移横幅/载荷缺失三提示与方案取数错误回显，纯展示零逻辑变更）。
 *
 * 输入:  noSolutions（done+feasible_count=0）/diagnosis（result 载荷弱类型
 *        字段——DiagnosisPanel 自窄化）/driftWarn（applyGates 闸③）/
 *        payloadMissing（done 而 feasible_count 缺失）+方案取数 error 面
 * 输出:  三提示段落（各自条件渲染）+取数错误回显段（409/422 领域码注记）
 *
 * 规格说明（FE6 D8/AUDIT2 FIX2 I-3/P0-2 沿革——逻辑零变更纯抽取）。
 */
import { Typography } from "antd";

import { WaterprintApiError } from "../shared/api/http";
import { DiagnosisPanel } from "../features/solutions/components/DiagnosisPanel";

/** 无解诊断/漂移横幅/载荷缺失三提示（solutionsPane 面内条件渲染面）。 */
export function SolutionsNotices({
  noSolutions,
  diagnosis,
  driftWarn,
  payloadMissing,
}: {
  noSolutions: boolean;
  diagnosis: unknown;
  driftWarn: boolean;
  payloadMissing: boolean;
}) {
  return (
    <>
      {noSolutions ? <DiagnosisPanel diagnosis={diagnosis} /> : null}
      {driftWarn ? (
        <Typography.Paragraph type="warning" style={{ marginBottom: 0, marginTop: 8 }}>
          设计已变更——方案表来自旧版本设计的枚举结果，应用前将再次提示确认。
        </Typography.Paragraph>
      ) : null}
      {payloadMissing ? (
        <Typography.Paragraph type="warning" style={{ marginBottom: 0, marginTop: 8 }}>
          枚举已完成但结果载荷缺失（feasible_count）——请重新提交枚举。
        </Typography.Paragraph>
      ) : null}
    </>
  );
}

/** 方案取数错误回显（409/422 领域码注记仅挂对应码——AUDIT2 FIX2 I-3）。 */
export function SolutionsFetchError({
  error,
  isError,
}: {
  error: unknown;
  isError: boolean;
}) {
  if (!isError) {
    return null;
  }
  return (
    <Typography.Paragraph type="danger">
      方案取数失败：
      {error instanceof Error ? error.message : "未知错误"}
      {error instanceof WaterprintApiError &&
      (error.code === "TaskNotCompleteError" ||
        error.code === "InvalidPageParameterError")
        ? "（未完成任务取方案=409/排序键白名单外=422——详见任务状态）"
        : null}
    </Typography.Paragraph>
  );
}
