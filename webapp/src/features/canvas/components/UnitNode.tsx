/**
 * 构筑物节点卡片：域色象形图标+中文名主标+unit_id 等宽副标+内置 kind
 * 徽标+左域色 bar+选中鎏金描边+方向端口排布。
 *
 * 输入:  NodeProps<UnitFlowNode>（投影层 data：unitId/kind/sourcePorts/
 *        targetPorts——React Flow 受控 selected 标记）
 * 输出:  React Flow 自定义节点渲染件（type="unit" 注册键）
 *
 * 规格说明（FE4 D1/D2+FE5 选中面+M6 中文名；C2-canvas 批 P3 重制——
 * task-C2-canvas-plan.md §二+glm D 项①⑤ 痛点处置）：
 *   - 重制=视觉稿 A 冻结语言（c2-design/canvas-flow.html 态二）：168 宽
 *     卡片+左 3px 域色 bar（四域色——unitGlyph.domainColorOf）+24×24
 *     象形图标（Unicode 稳定集+域色三色组底/边/前景）+中文名 12.5px
 *     600 主标（#e8eef7——C1 冻结主文字色，glm ⑤对比度痛点收口）+
 *     unit_id 等宽 10.5px 副标（tertiary 弱色）+选中**鎏金**描边+光晕
 *     （C1 变量轴注释「鎏金限品牌点缀（选中描边/收边线）」既定意图——
 *     替换 FE5 蓝描边；--wp-gold 同值字面量双源）；
 *   - 域色数据=单元清单端点（useListUnitsApiUnitsGet——name_zh 同源
 *     同缓存）；查表键=kind ?? unitId（内置节点归 catalog kind 键
 *     「municipal_input 等——business_line=municipal §14.3 裁决」；
 *     未收录回退中性灰不误导）；
 *   - 中文名数据源=M6 制（清单 name_zh 精确等值；未达/未收录回退
 *     unit_id 主标）；unit_id 恒留等宽副标（唯一键语义不弱化）；
 *   - D1 端口=方向中性：targetPorts 左侧（入）/sourcePorts 右侧（出）
 *     ——P8 端口描边随域色（挂账④流体色兑现）；
 *   - 多端口垂直均布（工程图例惯例）；卡片底色 --wp-bg-elevated
 *     配 ConfigProvider 深色主题（CanvasFlow colorMode=dark 同谱）；
 *   - 只读批：节点拖动面归 CanvasFlow 裁量（本卡片不消费拖拽态）。
 */
import { useMemo } from "react";
import type { NodeProps } from "@xyflow/react";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { domainColorOf, unitGlyph } from "../lib/unitGlyph";
import type { UnitFlowNode } from "../lib/projectFlow";
import { PortHandle } from "./PortHandle";

/** 内置节点 kind 徽标文案（D2 四 kind——core graph/nodes.py 内置域）。 */
const KIND_LABELS: Record<string, string> = {
  municipal_input: "市政进水",
  junction: "汇流",
  quality_edit: "水质编辑",
  recycle_junction: "回流汇流",
};

/** 卡片骨架（视觉稿冻结——与 C1 变量轴同值双源：改色红线双处联动）。 */
const CARD_WIDTH = 168;
const CARD_MIN_HEIGHT = 56;

/** 选中态鎏金描边/光晕（--wp-gold #d9a94a 派生——交互状态色非语义色）。 */
const SELECT_BORDER = "rgba(217, 169, 74, 0.75)";
const SELECT_GLOW =
  "0 0 0 1px rgba(217,169,74,.35), 0 4px 18px rgba(217,169,74,.14), 0 3px 12px rgba(3,10,22,.45)";

/** 域色图标三色组（视觉稿态三冻结——底/边框/前景按域派生）。 */
const DOMAIN_ICON_STYLES: Record<string, { bg: string; border: string; fg: string }> = {
  municipal: { bg: "rgba(77,163,255,.14)", border: "rgba(77,163,255,.3)", fg: "#7ab2ff" },
  sludge: { bg: "rgba(156,107,69,.16)", border: "rgba(156,107,69,.4)", fg: "#d4a273" },
  mine_water: { bg: "rgba(53,201,176,.12)", border: "rgba(53,201,176,.3)", fg: "#52d8c2" },
  conveyance: { bg: "rgba(154,168,184,.14)", border: "rgba(154,168,184,.3)", fg: "#b8c6d6" },
};
const NEUTRAL_ICON = { bg: "rgba(89,89,89,.14)", border: "rgba(89,89,89,.3)", fg: "#8c8c8c" };

/** 端口列垂直排布（首个端口距顶 20px、行距 16px——多端口均布）。 */
const PORT_TOP = 20;
const PORT_ROW = 16;

export function UnitNode({ data, selected }: NodeProps<UnitFlowNode>) {
  const badge = data.kind === null ? null : KIND_LABELS[data.kind] ?? data.kind;
  // 域色/中文名数据源=单元清单端点（同一 hook 同一缓存——React Query
  // 去重使多卡片订阅零额外请求）。域色查表键=kind ?? unitId（内置节点
  // 归 catalog kind 键；匹配=精确等值 ParamForm 同构）
  const catalog = useListUnitsApiUnitsGet();
  const businessLine = useMemo(() => {
    const units = catalog.data?.units;
    if (units === undefined) {
      return null;
    }
    const key = data.kind ?? data.unitId;
    return units.find((unit) => unit.unit_id === key)?.business_line ?? null;
  }, [catalog.data, data.unitId, data.kind]);
  const domainColor = domainColorOf(businessLine);
  const iconStyle = DOMAIN_ICON_STYLES[businessLine ?? ""] ?? NEUTRAL_ICON;
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
        background: "var(--wp-bg-elevated)",
        border: selected
          ? `1px solid ${SELECT_BORDER}`
          : "1px solid #2c4568",
        boxShadow: selected ? SELECT_GLOW : "0 3px 12px rgba(3,10,22,.45)",
        borderRadius: 8,
        color: "var(--wp-text)",
      }}
    >
      {/* 左域色 bar（视觉稿冻结：3px 圆角条 inset 8px） */}
      <span
        aria-hidden
        style={{
          position: "absolute",
          left: -1,
          top: 8,
          bottom: 8,
          width: 3,
          borderRadius: 2,
          background: domainColor,
        }}
      />
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px 5px 13px" }}>
        <span
          aria-hidden
          style={{
            width: 24,
            height: 24,
            flex: "none",
            borderRadius: 6,
            fontSize: 12,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: iconStyle.bg,
            border: `1px solid ${iconStyle.border}`,
            color: iconStyle.fg,
          }}
        >
          {unitGlyph(data.unitId, data.kind)}
        </span>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--wp-text)" }}>
          {nameZh ?? data.unitId}
        </span>
        {badge !== null && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: 10,
              color: "var(--wp-text-3)",
              border: "1px solid var(--wp-border-2)",
              borderRadius: 4,
              padding: "0 5px",
              flex: "none",
            }}
            title={data.kind ?? undefined}
          >
            {badge}
          </span>
        )}
      </div>
      <div
        style={{
          padding: "0 10px 8px 13px",
          fontFamily: "var(--wp-font-mono)",
          fontSize: 10.5,
          color: "var(--wp-text-3)",
          wordBreak: "break-all",
        }}
      >
        {data.unitId}
      </div>
      {data.targetPorts.map((portId, index) => (
        <div key={`t-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, left: -5 }}>
          <PortHandle portId={portId} direction="target" domainColor={domainColor} />
        </div>
      ))}
      {data.sourcePorts.map((portId, index) => (
        <div key={`s-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, right: -5 }}>
          <PortHandle portId={portId} direction="source" domainColor={domainColor} />
        </div>
      ))}
    </div>
  );
}
