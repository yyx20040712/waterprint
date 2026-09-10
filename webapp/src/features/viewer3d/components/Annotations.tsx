/**
 * 三维标注：troika SDF 文本（构筑物中文名+亮色描边——按单元分组一条）。
 *
 * 输入:  RenderNode[]（solids 组——按 node.id「unit::semantic」前缀分
 *        组聚合：标注位=单元组最高顶+抬升；catalog name_zh 中文名
 *        （useListUnitsApiUnitsGet 同缓存——M6 中文名制同式，未收录
 *        回退 unit_id）
 * 输出:  SDF 文本组（troika Text 经 primitive 挂载）
 *
 * 规格说明（FE1 实装 v1；R2 C3 清理面 2026-08-28；C2-3d V3 重制——
 *   briefs/task-C2-3d-plan.md §二 V3+呈裁③「中文名+默认开」）：
 *   - v1 痛点（glm B 项④「无对象命名」+实现截图零标签根因）：文本=
 *     node.id 全串（36 条逐图元噪声）+深色字 #1f1f1f 深底不可见；
 *   - 重制=按单元分组（"unit::" 前缀切分——一条/单元；管廊
 *     pipe::* 与非「::」id 整体跳过：管线/图示语义不标注）；中文名
 *     catalog join；亮色 #e8eef7+深描边（troika outlineWidth——深底
 *     可读）；字号随场景对角线自适应（0.6~6m 钳位）；
 *   - 抬升=分组最高顶+1.2 字号位（标注位摆放，非业务推导）；
 *   - troika Text 持 SDF 纹理/字形图集/后台 worker——useEffect 卸载面
 *     dispose（primitive 不托管外部对象生命周期；工况/项目切换不泄漏，
 *     R2 C3）；
 *   - CJK 字体子集构建期生成（§11 R9——v1 默认字体，子集批挂账）。
 */
import { useEffect, useMemo } from "react";
import { Text } from "troika-three-text";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import type { RenderNode } from "../lib/projectScene";

const LABEL_COLOR = "#e8eef7";
const LABEL_OUTLINE_COLOR = "#0a1220";
/** 字号随对角线缩放的下/上钳（m/字高——1080p 可读下限/防巨字）。 */
const FONT_MIN = 0.6;
const FONT_MAX = 6.0;
/** 对角线→字号比例（glm 一轮 0.01→0.018+上钳 6：全厂视距可读——
 * golden ~600m 对角→上钳 6m 字高量级）。 */
const FONT_PER_DIAGONAL = 0.018;
/** 标注抬升=分组最高顶+1.2×字号（贴顶可读间距）。 */
const LIFT_FACTOR = 1.2;
/** 标签错位带数（glm 二轮采纳：串行排布相邻单元同顶标签叠压——
 * 按单元序三高度带错位[0/0.9/1.8 字号]消叠压；碰撞检测归后续批）。 */
const STAGGER_BANDS = 3;

type UnitLabel = {
  unitId: string;
  position: [number, number, number];
};

type AnnotationsProps = {
  nodes: RenderNode[];
  /** 场景对角线（字号自适应——缺省走下钳）。 */
  diagonal?: number;
};

export function Annotations({ nodes, diagonal = 0 }: AnnotationsProps) {
  const catalog = useListUnitsApiUnitsGet();
  const fontSize = useMemo(
    () => Math.min(FONT_MAX, Math.max(FONT_MIN, diagonal * FONT_PER_DIAGONAL)),
    [diagonal],
  );
  // 按单元分组（"unit::semantic" 前缀；管廊 pipe::* 与无分隔符 id 跳过）
  const labels = useMemo<UnitLabel[]>(() => {
    const tops = new Map<string, { x: number; z: number; top: number }>();
    for (const node of nodes) {
      const separator = node.id.indexOf("::");
      if (separator <= 0) {
        continue;
      }
      const unitId = node.id.slice(0, separator);
      if (unitId === "pipe" || unitId === "site") {
        continue;
      }
      // 水平位=单元组首个节点（组内节点水平聚拢——fallback 排布同源
      // 近似）；高度=组内最高顶（A 二审 GD-N-05 口径记档）
      const acc = tops.get(unitId) ?? { x: node.position[0], z: node.position[2], top: 0 };
      acc.top = Math.max(acc.top, node.position[1] + (node.dims["depth"] ?? 0));
      tops.set(unitId, acc);
    }
    return [...tops.entries()].map(([unitId, acc], index) => ({
      unitId,
      position: [
        acc.x,
        acc.top + (LIFT_FACTOR + ((index % STAGGER_BANDS) * 0.9)) * fontSize,
        acc.z,
      ] as [number, number, number],
    }));
  }, [nodes, fontSize]);
  // 中文名（catalog 同缓存 join——未收录/未达回退 unit_id）
  const nameByUnit = useMemo(() => {
    const map = new Map<string, string>();
    for (const unit of catalog.data?.units ?? []) {
      map.set(unit.unit_id, unit.name_zh);
    }
    return map;
  }, [catalog.data]);
  return (
    <group>
      {labels.map((label) => (
        <LabelMesh
          key={label.unitId}
          text={nameByUnit.get(label.unitId) ?? label.unitId}
          position={label.position}
          fontSize={fontSize}
        />
      ))}
    </group>
  );
}

function LabelMesh({
  text,
  position,
  fontSize,
}: {
  text: string;
  position: [number, number, number];
  fontSize: number;
}) {
  const label = useMemo(() => {
    const instance = new Text();
    instance.text = text;
    instance.fontSize = fontSize;
    instance.color = LABEL_COLOR;
    instance.outlineWidth = fontSize * 0.18;
    instance.outlineColor = LABEL_OUTLINE_COLOR;
    instance.anchorX = "center";
    instance.anchorY = "bottom";
    instance.sync();
    return instance;
  }, [text, fontSize]);
  // R2 C3：卸载/换文案即 dispose 旧实例（SDF 纹理/字形图集/worker 释放——
  // primitive 不托管外部对象生命周期，缺此面则工况切换累积泄漏）。
  useEffect(() => () => label.dispose(), [label]);
  return <primitive object={label} position={position} />;
}
