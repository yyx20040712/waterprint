/**
 * v4 工艺画布节点卡（b3 功能面重涂批 2026-11-19——稿 network.html
 * .flow-node 形：标题行〔域色字形+中文名〕+id 行〔mono〕+域线 meta 行+
 * 左右锚点 Handle；泥线业务线=混色描边；自 thumbnailFlow 拆件〔行数预算
 * 500 墙〕）。
 *
 * 输入:  NodeProps（xyflow 受控——data=ThumbData 渲染层聚合注入〔nameZh/
 *        inPort/outPort/line——目录聚合在 thumbnailFlow〕）+selected
 * 输出:  ThumbnailNode（注册键 "unit" 节点件）+ThumbData 类型+LINE_LABELS
 *        （业务线中文标签——unitInspector 同源消费）
 *
 * 规格说明（b3 批准稿 network.html 节点段）：
 *   - id 行恢复（稿 .flow-node-id 在场——V4 P1「id 副标移除」裁决由批准
 *     稿推翻；data-node-id 探针锚保留）；
 *   - 域色=CSS 轴 var(--wp-water/sludge)〔注入轴——随主题换肤零重渲染〕；
 *   - 锚点端口=目录首 IN/OUT 端口（缺省 in/out 泛键——B1 骨架口径承袭）。
 */
import { Handle, Position, type NodeProps } from "@xyflow/react";

import type { UnitFlowNode } from "../../features/canvas/lib/projectFlow";
import { ThumbnailGlyph } from "../../features/canvas/components/thumbnailGlyph";

/** 缩略图节点 data（渲染层聚合注入——投影 data 零触碰，M1 editData 同制）。 */
export type ThumbData = UnitFlowNode["data"] & {
  nameZh?: string;
  inPort?: string;
  outPort?: string;
  line?: string | null;
};

/** 业务线中文标签（节点 meta 行/inspector 徽标——稿 .flow-node-meta；
 *  目录键域内值）。 */
export const LINE_LABELS: Record<string, string> = {
  municipal: "水线",
  sludge: "泥线",
  mine_water: "矿井水线",
  conveyance: "输配水线",
};

/** 缩略图节点（b3 稿形卡：标题〔域色字形+图题〕+id+域线 meta——selected
 *  经 node.selected 驱动描边；sludge 业务线=泥线卡着色）。 */
export function ThumbnailNode({ data, selected }: NodeProps) {
  const thumb = data as ThumbData;
  const title = thumb.unitId;
  const isSludge = thumb.line === "sludge";
  return (
    <div
      className={`wp-v4-node${selected ? " selected" : ""}${isSludge ? " sludge" : ""}`}
      data-node-id={title}
    >
      <Handle
        type="target"
        position={Position.Left}
        id={thumb.inPort ?? "in"}
        style={{ background: "var(--wp-bg-elevated)", borderColor: "var(--wp-border)" }}
      />
      <div className="wp-v4-node-card">
        <span className="wp-v4-node-title">
          <ThumbnailGlyph kind={thumb.kind ?? title} width={40} height={25} />
          <span className="wp-v4-node-name">{thumb.nameZh ?? title}</span>
        </span>
        <span className="wp-v4-node-id">{title}</span>
        {thumb.line !== undefined && thumb.line !== null ? (
          <span className="wp-v4-node-meta">{LINE_LABELS[thumb.line] ?? null}</span>
        ) : null}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id={thumb.outPort ?? "out"}
        style={{ background: "var(--wp-bg-elevated)", borderColor: "var(--wp-border)" }}
      />
    </div>
  );
}
