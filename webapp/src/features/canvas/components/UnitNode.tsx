/**
 * 构筑物节点卡片：中文名主标（单元清单 name_zh）+unit_id 等宽副标+
 * 内置 kind 徽标+左右方向端口排布+选中描边。
 *
 * 输入:  NodeProps<UnitFlowNode>（投影层 data：unitId/kind/sourcePorts/
 *        targetPorts——D2 纯 key+kind+React Flow 受控 selected 标记）
 * 输出:  React Flow 自定义节点渲染件（type="unit" 注册键）
 *
 * 规格说明（FE4 批 6b 段一，D1/D2 裁决；FE5 批 6b 段三增选中面；
 * M6 批 2026-09-03 中文名收口 FE4 段二挂账）：
 *   - D2 卡片=纯 unit key+内置 kind 标注：unit_id 等宽字体（同名构筑物
 *     跨线各自渲染的唯一键）；值含 kind=内置节点加徽标（municipal_input/
 *     junction/quality_edit/recycle_junction——投影层透传不设白名单）；
 *   - M6 中文名：工艺单元主标=单元清单 name_zh（useListUnitsApiUnitsGet
 *     生成 hook 直用——与单元库侧栏同一数据源同一缓存；清单未达/未收录
 *     （内置节点/自定义键）回退 unit_id 主标）；unit_id 恒留等宽副标
 *     （唯一键语义不因显示层弱化）；节点结果摘要仍挂账段二；
 *   - D1 端口=方向中性：targetPorts 左侧（入）/sourcePorts 右侧（出）——
 *     端口集合来自投影层边端点方向聚合（端口表不在项目文件）；灰阶中性
 *     色承载（§19.3 语义色之外禁彩色）；
 *   - FE5 选中反馈（D2 受控 selected——CanvasFlow 映射 node.selected）：
 *     选中描边 2px 主题蓝+微光晕（交互状态色非语义色；React Flow 内建
 *     elementsSelectable 高亮之上的明确视觉反馈）；
 *   - 多端口垂直均布（工程图例惯例）；卡片底色深灰配 ConfigProvider
 *     深色主题（CanvasFlow colorMode=dark 同谱）；
 *   - 只读批：节点拖动面归 CanvasFlow 裁量（本卡片不消费拖拽态）。
 */
import { useMemo } from "react";
import type { NodeProps } from "@xyflow/react";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
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

/** 选中态描边/微光晕（AntD 暗色主题蓝——交互状态色非 §19.3 语义色）。 */
const SELECT_BORDER = "#1668dc";
const SELECT_GLOW = "0 0 6px rgba(22, 104, 220, 0.6)";

/** 端口列垂直排布（首个端口距顶 20px、行距 16px——多端口均布）。 */
const PORT_TOP = 20;
const PORT_ROW = 16;

export function UnitNode({ data, selected }: NodeProps<UnitFlowNode>) {
  const badge = data.kind === null ? null : KIND_LABELS[data.kind] ?? data.kind;
  // 中文名数据源=单元清单端点（与单元库侧栏同一 hook 同一缓存——React Query
  // 去重使多卡片订阅零额外请求）。匹配=精确等值（ParamForm index.get(kind??
  // unitId) 同构——工艺单元节点键即类型键；内置节点 kind 徽标已有中文面不
  // 重复取名；未达/未收录回退 unit_id 主标）
  const catalog = useListUnitsApiUnitsGet();
  const nameZh = useMemo(() => {
    const units = catalog.data?.units;
    if (units === undefined || data.kind !== null) {
      return null;
    }
    return units.find((unit) => unit.unit_id === data.unitId)?.name_zh ?? null;
  }, [catalog.data, data.unitId, data.kind]);
  return (
    <div
      style={{
        position: "relative",
        width: CARD_WIDTH,
        minHeight: CARD_MIN_HEIGHT,
        padding: "6px 14px",
        background: CARD_BACKGROUND,
        border: selected
          ? `2px solid ${SELECT_BORDER}`
          : `1px solid ${CARD_BORDER}`,
        boxShadow: selected ? SELECT_GLOW : undefined,
        borderRadius: 6,
        color: "#d9d9d9",
        fontSize: 12,
        lineHeight: 1.6,
      }}
    >
      {nameZh !== null ? (
        <>
          <div style={{ fontWeight: 600 }}>{nameZh}</div>
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#a6a6a6", wordBreak: "break-all" }}>
            {data.unitId}
          </div>
        </>
      ) : (
        <div style={{ fontFamily: "monospace", wordBreak: "break-all" }}>
          {data.unitId}
        </div>
      )}
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
