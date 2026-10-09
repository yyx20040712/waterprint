/**
 * v4 方案偏差重排纯函数层（B2 结果与方案批 2026-10-09——任务书 §二.②
 * 数据流②：调左栏参数→方案卡按与当前参数的偏差重排+Δ徽标随动；前端
 * 重算零新 server 端点；零运行期库 import——node 直测同 solutionsView 制）。
 *
 * 输入:  方案行族（SolutionRow）+gridFields（任务 result 载荷窄化）+当前
 *        参数（design.nodeParams[unitId]——apply 后 invalidate 即随动）
 * 输出:  buildSolutionCards → 卡模型族（S 编号/参数摘要/★推荐=服务端排序
 *        首位/偏差字段族+Δ徽标文本/偏差和重排键）
 *
 * 规格说明（B2 任务书 §二.②+wireframe 屏 1 注记）：
 *   - 偏差口径=方案值−当前值（per grid 字段；当前值缺席字段不入偏差面
 *     ——无可比基线不算偏差）；
 *   - Δ徽标文案=键名+差值（形「ΔSRT 2d」——label 用 label_zh 降级 key，
 *     差值整数直出/小数 3 位尾零剥除）；
 *   - 重排=偏差和升序（与当前参数最近者列首；tie=服务端序稳定）；
 *   - ★推荐=服务端排序首位标记（serverRank 1——重排不改归属）；
 *   - S 编号=服务端序（1 基两位补零——S01 形，与重排后位置解耦）。
 */
import { dimUnit } from "../../shared/dimLabels";
import type { GridField } from "../../features/solutions/lib/solutionsFields";
import type { SolutionRow } from "../../features/solutions/lib/solutionsView";

/** 偏差字段（Δ 徽标数据面）。 */
export type DeviationField = {
  key: string;
  label: string;
  /** 方案值−当前值。 */
  diff: number;
};

/** 方案卡模型（渲染层聚合——apply 载荷经 buildApplyPayload 同源投影）。 */
export type SolutionCard = {
  /** S 编号（服务端序 1 基两位补零——S01 形）。 */
  no: string;
  /** 服务端序（1 基——★归属与 S 编号真源）。 */
  serverRank: number;
  /** 参数摘要（grid 字段 label=值 串——wireframe「SRT 12d · V=18,750」形）。 */
  summary: string;
  /** ★推荐=服务端排序首位（重排不改归属）。 */
  recommended: boolean;
  /** 偏差字段族（非零差——Δ 徽标数据面）。 */
  deviations: DeviationField[];
  /** Δ徽标文本族（键名+差值——渲染直出）。 */
  deviationTexts: string[];
  /** 偏差和（重排键——升序）。 */
  deviationSum: number;
  /** 原行（apply 载荷消费面——buildApplyPayload(row, gridFields)）。 */
  row: SolutionRow;
};

/** 差值显示串（整数直出/小数 3 位尾零剥除——"2"/"0.35"/"-1.5"）。 */
function formatDiff(diff: number): string {
  if (Number.isInteger(diff)) {
    return String(diff);
  }
  return String(parseFloat(diff.toFixed(3)));
}

/** 卡模型构建+偏差重排（纯函数——同输入同输出确定性）。 */
export function buildSolutionCards(
  rows: readonly SolutionRow[],
  gridFields: readonly GridField[],
  currentValues: Readonly<Record<string, number>>,
): SolutionCard[] {
  const cards: SolutionCard[] = rows.map((row, index) => {
    const serverRank = index + 1;
    const deviations: DeviationField[] = [];
    const summaryParts: string[] = [];
    let deviationSum = 0;
    for (const field of gridFields) {
      const raw = row[field.key];
      const label = field.label_zh ?? field.key;
      const unit = dimUnit(field.dim);
      if (typeof raw === "number" && Number.isFinite(raw)) {
        summaryParts.push(`${label} ${raw}${unit === "" ? "" : unit}`);
        const current = currentValues[field.key];
        if (
          typeof current === "number" &&
          Number.isFinite(current) &&
          raw !== current
        ) {
          const diff = raw - current;
          deviations.push({ key: field.key, label, diff });
          deviationSum += Math.abs(diff);
        }
      }
    }
    return {
      no: `S${String(serverRank).padStart(2, "0")}`,
      serverRank,
      summary: summaryParts.join(" · "),
      recommended: serverRank === 1,
      deviations,
      deviationTexts: deviations.map(
        (d) => `Δ${d.key} ${formatDiff(d.diff)}`,
      ),
      deviationSum,
      row,
    };
  });
  // 重排：偏差和升序（最近当前参数列首）；tie=服务端序（稳定排序）
  return [...cards].sort((a, b) =>
    a.deviationSum === b.deviationSum
      ? a.serverRank - b.serverRank
      : a.deviationSum - b.deviationSum,
  );
}
