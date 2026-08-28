/**
 * 三维标注：troika SDF 文本（池体/构筑物 unit_id + 语义标签）。
 *
 * 输入:  RenderNode[]（solids 组——标注位=节点位+池深抬升）
 * 输出:  SDF 文本组（troika Text 经 primitive 挂载）
 *
 * 规格说明（FE1 实装 v1；R2 C3 清理面 2026-08-28）：
 *   - 标注内容=node_id（场景图携带的稳定标识——禁前端拼业务文案）；
 *   - 抬升=dims.depth 直读（标注位摆放，非业务推导）；
 *   - troika Text 持 SDF 纹理/字形图集/后台 worker——useEffect 卸载面
 *     dispose（primitive 不托管外部对象生命周期；工况/项目切换不泄漏，
 *     R2 C3）；
 *   - CJK 字体子集构建期生成（§11 R9——v1 默认字体，子集批挂账）。
 */
import { useEffect, useMemo } from "react";
import { Text } from "troika-three-text";

import type { RenderNode } from "../lib/projectScene";

const LABEL_FONT_SIZE = 0.8;
const LABEL_COLOR = "#1f1f1f";

type AnnotationsProps = {
  nodes: RenderNode[];
};

export function Annotations({ nodes }: AnnotationsProps) {
  const labels = useMemo(
    () =>
      nodes.map((node) => ({
        id: node.id,
        text: node.id,
        position: [
          node.position[0],
          node.position[1] + (node.dims["depth"] ?? 0),
          node.position[2],
        ] as [number, number, number],
      })),
    [nodes],
  );
  return (
    <group>
      {labels.map((label) => (
        <LabelMesh key={label.id} text={label.text} position={label.position} />
      ))}
    </group>
  );
}

function LabelMesh({ text, position }: { text: string; position: [number, number, number] }) {
  const label = useMemo(() => {
    const instance = new Text();
    instance.text = text;
    instance.fontSize = LABEL_FONT_SIZE;
    instance.color = LABEL_COLOR;
    instance.anchorX = "center";
    instance.anchorY = "bottom";
    instance.sync();
    return instance;
  }, [text]);
  // R2 C3：卸载/换文案即 dispose 旧实例（SDF 纹理/字形图集/worker 释放——
  // primitive 不托管外部对象生命周期，缺此面则工况切换累积泄漏）。
  useEffect(() => () => label.dispose(), [label]);
  return <primitive object={label} position={position} />;
}
