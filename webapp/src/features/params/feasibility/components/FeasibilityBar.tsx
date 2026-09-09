/**
 * 1D 行内可行域区间条（PD7 呈裁④）：可行段绿/不可行灰/degraded 标注行；
 * 点击可行段回填值、不可行区吸附最近可行段边界（P0-3 终裁交互流）。
 *
 * 输入:  DesignMapResponse 的 1D 投影（axisValues/segments/coverage）+
 *        回填通道 onPick(value)（草稿状态——apply payload 键零漂移）
 * 输出:  行内展开区间条（data-testid=fd-bar/fd-seg-{i}——探针锚点）
 */
import { Typography } from "antd";

import type { DesignMapResponse } from "../../../../shared/api/generated/model";
import {
  formatBackfill,
  isFeasibleValue,
  snapToBoundary,
  valueAtRatio,
} from "../lib/feasibility";

/** 语义色（C 批禁混批——绿=可行/灰=不可行，装饰性配色不做）。 */
const FEASIBLE_GREEN = "#52c41a";
const INFEASIBLE_GRAY = "#d9d9d9";
const BAR_HEIGHT = 18;

export function FeasibilityBar({
  product,
  onPick,
}: {
  product: DesignMapResponse;
  onPick: (value: number) => void;
}) {
  const values = product.axis_values[0] ?? [];
  const segments = product.segments ?? [];
  const low = values[0] ?? 0;
  const high = values[values.length - 1] ?? low + 1;
  const span = high - low || 1;
  const ratio = (value: number) => ((value - low) / span) * 100;

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const position = (event.clientX - rect.left) / rect.width;
    const value = valueAtRatio(position, values);
    if (value === null) {
      return;
    }
    // PD7 终裁：不可行点击=吸附最近可行段边界（引导行为——不静默）
    const picked = isFeasibleValue(value, segments)
      ? value
      : snapToBoundary(value, segments);
    if (picked !== null) {
      onPick(Number(formatBackfill(picked)));
    }
  };

  return (
    <div data-testid="fd-bar" style={{ marginTop: 4 }}>
      {product.constraint_coverage === "degraded" ? (
        <Typography.Text type="secondary" style={{ fontSize: 11 }} data-testid="fd-degraded">
          本单元暂无适用可行性约束——绿色区=计算有效域
        </Typography.Text>
      ) : null}
      <div
        role="presentation"
        onClick={handleClick}
        title="点击可行段（绿）回填参数值；点击不可行区（灰）吸附最近可行边界"
        style={{
          position: "relative",
          height: BAR_HEIGHT,
          background: INFEASIBLE_GRAY,
          borderRadius: 3,
          cursor: "pointer",
          marginTop: 4,
        }}
      >
        {segments.map((segment, index) => (
          <div
            key={`${segment.start}-${segment.end}`}
            data-testid={`fd-seg-${index}`}
            style={{
              position: "absolute",
              left: `${ratio(segment.start)}%`,
              width: `${Math.max(ratio(segment.end) - ratio(segment.start), 0.5)}%`,
              top: 0,
              bottom: 0,
              background: FEASIBLE_GREEN,
            }}
          />
        ))}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", ...({ color: "#8c8c8c", fontSize: 11 } as const) }}>
        <span>{low}</span>
        <span>
          可行 {product.stats.feasible}/{product.stats.total}（
          {(product.stats.feasible_ratio * 100).toFixed(1)}%）
        </span>
        <span>{high}</span>
      </div>
    </div>
  );
}
