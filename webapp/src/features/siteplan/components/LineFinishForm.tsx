/**
 * 折线收笔参数面板子件（B4 笔③行预算拆法——ENG6 SiteplanToolbar/
 * StructureSidebar/LineSidebar 拆出先例第四例：自 SiteplanPane lineForm 块
 * 抽离，宽度/kind 编辑态随本件自持；finishedLine 挂起态归 SiteplanPane）。
 *
 * 输入:  kind（road|corridor——收笔会话线型）+pointsCount（点数显示）+
 *        onConfirm(width, corridorKind)/onDiscard（落笔/丢弃上行——draft
 *        copy-on-write 落位归父层）
 * 输出:  参数面板 JSX（InputNumber 宽度+corridor kind Select+落笔/丢弃
 *        按钮组——纯展示零业务推导）
 *
 * 规格说明（M3 L2b 收笔面沿承——B4 笔③态随迁注记）：
 *   - 宽度/kind=面板会话态：本件自持（父层按 finishedLine 条件渲染——
 *     新收笔会话=重新挂载=缺省重置，先例=原 onCommitLine 内 setLineWidth
 *     逐会话置缺省同语义）；
 *   - 宽度清空回退按 kind 二分（road=4/corridor=1.5——收笔会话线型即
 *     所选工具）；min 0.1 沿先例；
 *   - 落笔=onConfirm 上行；丢弃=onDiscard（父层 setFinishedLine(null)）。
 */
import { useState } from "react";
import { Button, InputNumber, Select, Space, Typography } from "antd";

/** 收笔参数面板缺省值（显示层常量：道路/走廊典型宽）。 */
const DEFAULT_ROAD_WIDTH = 4;
const DEFAULT_CORRIDOR_WIDTH = 1.5;

/** 走廊 kind 缺省（water——SiteCanvas CORRIDOR_COLORS 登记首键）。 */
const DEFAULT_CORRIDOR_KIND = "water";

/** 走廊 kind 选项（SiteCanvas CORRIDOR_COLORS 登记面——展示层映射）。 */
const CORRIDOR_KIND_OPTIONS = [
  { value: "water", label: "water（给水/中水）" }, { value: "power", label: "power（电力）" },
  { value: "gas", label: "gas（燃气/污泥气）" }, { value: "comm", label: "comm（通信）" },
];

export type LineFinishFormProps = {
  kind: "road" | "corridor";
  pointsCount: number;
  onConfirm: (width: number, corridorKind: string) => void;
  onDiscard: () => void;
};

export function LineFinishForm({
  kind, pointsCount, onConfirm, onDiscard,
}: LineFinishFormProps) {
  const [width, setWidth] = useState<number>(
    kind === "road" ? DEFAULT_ROAD_WIDTH : DEFAULT_CORRIDOR_WIDTH,
  );
  const [corridorKind, setCorridorKind] = useState<string>(DEFAULT_CORRIDOR_KIND);
  return (
    <div style={{ display: "grid", rowGap: 6, width: 200 }}>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {kind === "corridor" ? "管线走廊" : "道路"}宽度（m）·{pointsCount} 点
      </Typography.Text>
      <InputNumber
        size="small"
        min={0.1}
        value={width}
        // 清空回退按收笔会话线型二分（road=4/corridor=1.5——会话 kind 即所选工具）
        onChange={(value) =>
          setWidth(value ?? (kind === "corridor" ? DEFAULT_CORRIDOR_WIDTH : DEFAULT_ROAD_WIDTH))
        }
      />
      {kind === "corridor" ? (
        <Select
          size="small"
          value={corridorKind}
          options={CORRIDOR_KIND_OPTIONS}
          onChange={setCorridorKind}
        />
      ) : null}
      <Space size="small">
        <Button
          size="small"
          type="primary"
          disabled={!Number.isFinite(width)}
          onClick={() => onConfirm(width, corridorKind)}
        >
          落笔
        </Button>
        <Button size="small" onClick={onDiscard}>
          丢弃
        </Button>
      </Space>
    </div>
  );
}
