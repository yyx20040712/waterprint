/**
 * 构筑物节点卡片：unit_id 等宽字体主标+内置 kind 徽标+左右方向端口排布。
 *
 * 输入:  NodeProps<UnitFlowNode>（投影层 data：unitId/kind/sourcePorts/
 *        targetPorts——D2 纯 key+kind，参数与结果摘要不进本批渲染面）
 * 输出:  React Flow 自定义节点渲染件（type="unit" 注册键）
 *
 * 规格说明（FE4 批 6b 段一，D1/D2 裁决）：
 *   - D2 卡片=纯 unit key+内置 kind 标注：unit_id 等宽字体（同名构筑物
 *     跨线各自渲染的唯一键）；值含 kind=内置节点加徽标（municipal_input/
 *     junction/quality_edit/recycle_junction——投影层透传不设白名单）；
 *     中文名映射/节点结果摘要挂账段二（正路=server 单元清单端点，
 *     与 D1 端口表同源）；
 *   - D1 端口=方向中性：targetPorts 左侧（入）/sourcePorts 右侧（出）——
 *     端口集合来自投影层边端点方向聚合（端口表不在项目文件）；灰阶中性
 *     色承载（§19.3 语义色之外禁彩色）；
 *   - 多端口垂直均布（工程图例惯例）；卡片底色深灰配 ConfigProvider
 *     深色主题（CanvasFlow colorMode=dark 同谱）；
 *   - 只读批：节点拖动面归 CanvasFlow 裁量（本卡片不消费拖拽态）。
 */
import type { NodeProps } from "@xyflow/react";

import type { UnitFlowNode } from "../lib/projectFlow";
import { PortHandle } from "./PortHandle";

/** 内置节点 kind 徽标文案（D2 四 kind——core graph/nodes.py 内置域）。 */
const KIND_LABELS: Record<string, string> = {
  municipal_input: "市政进水",
  junction: "汇流",
  quality_edit: "水质编辑",
  recycle_junction: "回流汇流",
};

/** 卡片底色/描边（灰阶——ConfigProvider 深色主题同谱）。 */
const CARD_BACKGROUND = "#1f1f1f";
const CARD_BORDER = "#434343";
const CARD_WIDTH = 176;
const CARD_MIN_HEIGHT = 56;

/** 端口列垂直排布（首个端口距顶 20px、行距 16px——多端口均布）。 */
const PORT_TOP = 20;
const PORT_ROW = 16;

export function UnitNode({ data }: NodeProps<UnitFlowNode>) {
  const badge = data.kind === null ? null : KIND_LABELS[data.kind] ?? data.kind;
  return (
    <div
      style={{
        position: "relative",
        width: CARD_WIDTH,
        minHeight: CARD_MIN_HEIGHT,
        padding: "6px 14px",
        background: CARD_BACKGROUND,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: 6,
        color: "#d9d9d9",
        fontSize: 12,
        lineHeight: 1.6,
      }}
    >
      <div style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
        {data.unitId}
      </div>
      {badge !== null && (
        <div
          style={{
            display: "inline-block",
            marginTop: 2,
            padding: "0 6px",
            border: `1px solid ${CARD_BORDER}`,
            borderRadius: 4,
            fontSize: 11,
            color: "#a6a6a6",
          }}
          title={data.kind ?? undefined}
        >
          {badge}
        </div>
      )}
      {data.targetPorts.map((portId, index) => (
        <div key={`t-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, left: -5 }}>
          <PortHandle portId={portId} direction="target" />
        </div>
      ))}
      {data.sourcePorts.map((portId, index) => (
        <div key={`s-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, right: -5 }}>
          <PortHandle portId={portId} direction="source" />
        </div>
      ))}
    </div>
  );
}
