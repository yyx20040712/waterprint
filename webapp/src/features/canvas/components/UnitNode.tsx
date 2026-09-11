/**
 * 构筑物节点卡片：域色象形图标+中文名主标（unit_id 收进 title 悬浮）+
 * 内置 kind 徽标+左域色 bar+选中鎏金描边+方向端口排布。
 *
 * 输入:  NodeProps<UnitFlowNode>（投影层 data：unitId/kind/sourcePorts/
 *        targetPorts——React Flow 受控 selected 标记）
 * 输出:  React Flow 自定义节点渲染件（type="unit" 注册键）
 *
 * 规格说明（FE4 D1/D2+FE5 选中面+M6 中文名；C2-canvas 批 P3 重制——
 *   task-C2-canvas-plan.md §二+glm D 项①⑤ 痛点处置）：
 *   - 重制=视觉稿 A 冻结语言（c2-design/canvas-flow.html 态二）：168 宽
 *     卡片+左 3px 域色 bar（四域色——unitGlyph.domainColorOf）+24×24
 *     象形图标（Unicode 稳定集+域色三色组底/边/前景）+中文名 12.5px
 *     600 主标（#e8eef7——C1 冻结主文字色，glm ⑤对比度痛点收口）
 *     +选中**鎏金**描边+光晕（C1 变量轴注释「鎏金限品牌点缀（选中
 *     描边/收边线）」既定意图——替换 FE5 蓝描边；--wp-gold 同值字面量
 *     双源）；
 *   - 域色数据=单元清单端点（useListUnitsApiUnitsGet——name_zh 同源
 *     同缓存）；查表键=kind ?? unitId（内置节点归 catalog kind 键
 *     「municipal_input 等——business_line=municipal §14.3 裁决」；
 *     未收录回退中性灰不误导）；
 *   - 中文名数据源=M6 制（清单 name_zh 精确等值；未达/未收录回退
 *     unit_id 主标）；P2 生命周期批（2026-09-12 用户裁定「unit_id 对
 *     用户无效」）：常驻等宽副标行退役——unitId 收进主标 title 悬浮
 *     （ParamForm B2 PD8 追溯链同制；C2VD V2 断行工艺随副标退役）；
 *   - D1 端口=方向中性：targetPorts 左侧（入）/sourcePorts 右侧（出）
 *     ——P8 端口描边随域色（挂账④流体色兑现）；
 *   - 多端口垂直均布（工程图例惯例）；卡片底色 --wp-bg-elevated
 *     配 ConfigProvider 深色主题（CanvasFlow colorMode=dark 同谱）；
 *   - 只读批：节点拖动面归 CanvasFlow 裁量（本卡片不消费拖拽态）；
 *   - C2-thumb（2026-09-11 节点 3D 缩略图②）：图标槽双态=44×44 圆角
 *     深底 3D 缩略图（ThumbnailStage 离屏产出——context 注入[app 层
 *     组合穿线]）优先/缺席回退 24×24 象形（未算/无构型——零回归）；
 *     卡片最小高 56→64+端口首距 20→26（V4 布局校准）；设计真源=
 *     briefs/task-C2-thumb-plan.md；C2-visual T3：缩略图槽 hover 悬浮
 *     大图 160px（portal+fixed——task-c2-visual-plan §二 T3）。
 *   - P0-3（画布编辑最小闭环——task-c2-edit-plan）：编辑态（data.editing
 *     由 CanvasFlow 渲染层聚合注入——投影 data 字段零触碰）端口面=
 *     catalog 端口表渲染（红线④：纯 catalog 数据展示可——新节点零边
 *     时边聚合面空,manifest 端口面完整呈现 IN 左/OUT 右）+右上删除钮
 *     （store 薄壳 deleteNodes——级联清在纯函数层）；只读面零回归
 *     （editing 缺省=边聚合端口+无删除钮原样）。
 */
import { useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { Node, NodeProps } from "@xyflow/react";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { domainColorOf, unitGlyph } from "../lib/unitGlyph";
import { useUnitThumbnail } from "../lib/thumbnailContext";
import type { UnitFlowNode, UnitFlowNodeData } from "../lib/projectFlow";
import { useCanvasStore } from "../store/canvasStore";
import { PortHandle } from "./PortHandle";

/** catalog 端口声明（编辑态端口面数据——CanvasFlow 渲染层聚合注入）。 */
export type EditPortDecl = { portId: string; direction: "IN" | "OUT" };

/** 编辑态扩展 data（投影 UnitFlowNodeData 的超集——editing 面非投影产物）。 */
export type UnitNodeData = UnitFlowNodeData & {
  editing?: boolean;
  catalogPorts?: readonly EditPortDecl[];
};

/** 编辑态扩展节点（React Flow 泛型——NODE_TYPES 注册面消费）。 */
export type EditableUnitNode = Node<UnitNodeData, "unit">;

/** 内置节点 kind 徽标文案（D2 四 kind——core graph/nodes.py 内置域）。 */
const KIND_LABELS: Record<string, string> = {
  municipal_input: "市政进水",
  junction: "汇流",
  quality_edit: "水质编辑",
  recycle_junction: "回流汇流",
};

/** 卡片骨架（视觉稿冻结——与 C1 变量轴同值双源：改色红线双处联动）。 */
const CARD_WIDTH = 168;
const CARD_MIN_HEIGHT = 64; // C2-thumb：56→64（44 缩略图槽升档）

/** C2-thumb V3（呈裁① 推荐）：3D 缩略图 44×44 圆角深底（构型在场景底色
 * 上可读）；缩略图缺席=24×24 象形图标原槽（零回归回退态）。 */
const THUMB_SIZE = 44;

/** C2-visual T3：hover 悬浮大图边长（卡片上方预览——192 渲染近原生显）。 */
const POP_SIZE = 160;
const POP_VIEWPORT_MARGIN = 8;

/** 选中态鎏金描边/光晕（--wp-gold #d9a94a 派生——交互状态色非语义色；
 * R-G3 联动清单成员：改鎏金须与 global.css --wp-gold 同步）。 */
const SELECT_BORDER = "rgba(217, 169, 74, 0.75)";
const SELECT_GLOW =
  "0 0 0 1px rgba(217,169,74,.35), 0 4px 18px rgba(217,169,74,.14), 0 3px 12px rgba(3,10,22,.45)";

/** 域色图标三色组（视觉稿态三冻结——底/边框/前景按域派生；同值
 * 联动面=R-G3 清单：改域色以 unitGlyph.domainColorOf 为基准同步）。 */
const DOMAIN_ICON_STYLES: Record<string, { bg: string; border: string; fg: string }> = {
  municipal: { bg: "rgba(77,163,255,.14)", border: "rgba(77,163,255,.3)", fg: "#7ab2ff" },
  sludge: { bg: "rgba(156,107,69,.16)", border: "rgba(156,107,69,.4)", fg: "#d4a273" },
  mine_water: { bg: "rgba(53,201,176,.12)", border: "rgba(53,201,176,.3)", fg: "#52d8c2" },
  conveyance: { bg: "rgba(154,168,184,.14)", border: "rgba(154,168,184,.3)", fg: "#b8c6d6" },
};
const NEUTRAL_ICON = { bg: "rgba(89,89,89,.14)", border: "rgba(89,89,89,.3)", fg: "#8c8c8c" };

/** 端口列垂直排布（首个端口距顶 26px、行距 16px——C2-thumb 卡片升档
 * 同步 +6；多端口均布）。 */
const PORT_TOP = 26;
const PORT_ROW = 16;

export function UnitNode({ data, selected }: NodeProps<EditableUnitNode>) {
  const badge = data.kind === null ? null : KIND_LABELS[data.kind] ?? data.kind;
  // C2-thumb V3：本节点 3D 缩略图（context 注入——缺席=回退象形图标）
  const thumbnail = useUnitThumbnail(data.unitId);
  // C2-visual T3：hover 悬浮大图定位（fixed+portal——React Flow 容器
  // overflow:hidden 会裁剪节点内 absolute 弹层，逃逸到 body；槽位矩形
  // 快照驱动，视口钳位+上方优先下方回退）
  const [popRect, setPopRect] = useState<{
    x: number;
    top: number;
  } | null>(null);
  const thumbSlotRef = useRef<HTMLImageElement | null>(null);
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
        {thumbnail !== null ? (
          // C2-thumb V3：3D 缩略图（44×44 圆角深底——aria-hidden 装饰面，
          // 名称/键仍由文本承载）；构型=该项目该单元实况（Scene 同源）；
          // C2-visual T3：hover 悬浮大图（fixed+portal 逃逸容器裁剪）
          <img
            aria-hidden
            ref={thumbSlotRef}
            src={thumbnail}
            alt=""
            width={THUMB_SIZE}
            height={THUMB_SIZE}
            data-testid={`thumb-slot-${data.unitId}`}
            style={{
              width: THUMB_SIZE,
              height: THUMB_SIZE,
              flex: "none",
              borderRadius: 8,
              background: "var(--wp-bg-page)",
              objectFit: "cover",
              display: "block",
            }}
            onMouseEnter={() => {
              const slot = thumbSlotRef.current;
              if (slot === null) {
                return;
              }
              const rect = slot.getBoundingClientRect();
              const above = rect.top - POP_SIZE - 10 >= POP_VIEWPORT_MARGIN;
              setPopRect({
                x: rect.left + rect.width / 2,
                // GV-04（R 轮）：下翻分支纵向同样钳位（槽位贴底时 160px
                // 大图下缘不溢出视口——与水平向口径对称）
                top: above
                  ? rect.top - POP_SIZE - 10
                  : Math.min(
                      rect.bottom + 10,
                      window.innerHeight - POP_SIZE - POP_VIEWPORT_MARGIN,
                    ),
              });
            }}
            onMouseLeave={() => setPopRect(null)}
          />
        ) : (
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
        )}
        {/* P2 生命周期批：unitId 收进 title 悬浮（用户裁定副标隐藏——
            ParamForm B2 PD8 追溯链同制；nameZh 缺席时主标回退 unitId
            为瞬时未达态非常驻） */}
        <span
          title={data.unitId}
          style={{ fontSize: 12.5, fontWeight: 600, color: "var(--wp-text)" }}
        >
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
      {/* P0-3 编辑态删除钮（右上角——stopPropagation 免选中；store 薄壳
          通道→designWriter.deleteNodes 级联清边/摆放/受检） */}
      {data.editing === true && (
        <button
          type="button"
          title="删除该单元（所连边/摆放一并清除）"
          onClick={(event) => {
            event.stopPropagation();
            useCanvasStore.getState().deleteNodes([data.unitId]);
          }}
          style={{
            position: "absolute",
            top: -9,
            right: -9,
            width: 18,
            height: 18,
            lineHeight: 1,
            fontSize: 11,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "50%",
            cursor: "pointer",
            color: "#ff7875",
            background: "var(--wp-bg-elevated)",
            border: "1px solid rgba(255,77,79,.55)",
          }}
        >
          ✕
        </button>
      )}
      {data.editing === true && data.catalogPorts !== undefined
        ? // P0-3 编辑态端口面=manifest catalog 声明（红线④纯数据展示——
          // 新节点零边聚合面亦完整呈现；规则判断不在渲染层）；IN/OUT
          // 各自独立计数列（左入右出——工程图惯例）
          data.catalogPorts
            .filter((port) => port.direction === "IN")
            .map((port, index) => (
              <div
                key={`t-${port.portId}`}
                style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, left: -5 }}
              >
                <PortHandle
                  portId={port.portId}
                  direction="target"
                  domainColor={domainColor}
                  connectable
                />
              </div>
            ))
        : data.targetPorts.map((portId, index) => (
            <div key={`t-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, left: -5 }}>
              <PortHandle portId={portId} direction="target" domainColor={domainColor} />
            </div>
          ))}
      {data.editing === true && data.catalogPorts !== undefined
        ? data.catalogPorts
            .filter((port) => port.direction === "OUT")
            .map((port, index) => (
              <div
                key={`s-${port.portId}`}
                style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, right: -5 }}
              >
                <PortHandle
                  portId={port.portId}
                  direction="source"
                  domainColor={domainColor}
                  connectable
                />
              </div>
            ))
        : data.sourcePorts.map((portId, index) => (
            <div key={`s-${portId}`} style={{ position: "absolute", top: PORT_TOP + index * PORT_ROW, right: -5 }}>
              <PortHandle portId={portId} direction="source" domainColor={domainColor} />
            </div>
          ))}
      {/* C2-visual T3：hover 悬浮大图（portal 到 body——fixed 定位逃逸
          React Flow overflow:hidden 裁剪；视口水平钳位；pointer-events
          none 纯预览不挡交互；仅 hover 态挂载零常驻开销） */}
      {popRect !== null && thumbnail !== null
        ? createPortal(
            <img
              src={thumbnail}
              alt=""
              data-testid="wp-thumb-pop"
              style={{
                position: "fixed",
                left: Math.min(
                  Math.max(popRect.x - POP_SIZE / 2, POP_VIEWPORT_MARGIN),
                  window.innerWidth - POP_SIZE - POP_VIEWPORT_MARGIN,
                ),
                top: popRect.top,
                width: POP_SIZE,
                height: POP_SIZE,
                boxSizing: "border-box",
                borderRadius: 10,
                border: "1px solid var(--wp-border)",
                boxShadow: "0 8px 32px rgba(3,10,22,.6)",
                background: "var(--wp-bg-page)",
                zIndex: 1000,
                pointerEvents: "none",
              }}
            />,
            document.body,
          )
        : null}
    </div>
  );
}
