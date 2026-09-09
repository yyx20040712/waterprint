/**
 * 2D 可行域热力图（PD7 呈裁④：模态画布——SVG viewBox 自适应，DxfSvg
 * 先例）：可行格绿/不可行格灰；点击可行格回填两参数值、不可行格
 * 吸附最近可行格（欧氏——P0-3 吸附泛化）。
 *
 * 输入:  DesignMapResponse 的 2D 投影（axisValues×2/mask）+双轴元数据+
 *        回填通道 onPick(a, b)（草稿状态——两键同写零漂移）
 * 输出:  SVG 热力图（data-testid=fd-heatmap/fd-cell-{i}-{j}——探针锚点）
 */
import type { DesignMapResponse } from "../../../../shared/api/generated/model";
import { nearestFeasibleCell } from "../lib/feasibility";

/** 语义色（FeasibilityBar 同款——C 批禁混批）。 */
const FEASIBLE_GREEN = "#52c41a";
const INFEASIBLE_GRAY = "#d9d9d9";
const CELL = 24; // viewBox 单位格边（DxfSvg 同精神显示层常量）
const GAP = 1;

export function FeasibilityHeatmap({
  product,
  onPick,
}: {
  product: DesignMapResponse;
  onPick: (valueA: number, valueB: number) => void;
}) {
  const valuesA = product.axis_values[0] ?? [];
  const valuesB = product.axis_values[1] ?? [];
  const mask = product.mask ?? [];
  const width = valuesB.length * (CELL + GAP);
  const height = valuesA.length * (CELL + GAP);

  const handleCell = (i: number, j: number) => {
    const valueA = valuesA[i];
    const valueB = valuesB[j];
    if (valueA === undefined || valueB === undefined) {
      return;
    }
    if (mask[i]?.[j] === 1) {
      onPick(valueA, valueB);
      return;
    }
    // PD7 终裁吸附泛化：不可行格→最近可行格值对（不静默）
    const nearest = nearestFeasibleCell(valueA, valueB, valuesA, valuesB, mask);
    if (nearest !== null) {
      onPick(nearest.a, nearest.b);
    }
  };

  return (
    <div data-testid="fd-heatmap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "100%", display: "block" }}
      >
        {valuesA.map((_, i) =>
          valuesB.map((__, j) => (
            <rect
              key={`${i}-${j}`}
              data-testid={`fd-cell-${i}-${j}`}
              x={j * (CELL + GAP)}
              y={i * (CELL + GAP)}
              width={CELL}
              height={CELL}
              fill={mask[i]?.[j] === 1 ? FEASIBLE_GREEN : INFEASIBLE_GRAY}
              style={{ cursor: "pointer" }}
              onClick={() => handleCell(i, j)}
            >
              <title>
                {product.axes[0]?.field_id}={valuesA[i]} · {product.axes[1]?.field_id}=
                {valuesB[j]}
                {mask[i]?.[j] === 1 ? "（可行）" : "（不可行——点击吸附最近可行格）"}
              </title>
            </rect>
          )),
        )}
      </svg>
    </div>
  );
}
