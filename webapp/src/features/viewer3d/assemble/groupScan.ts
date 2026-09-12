/**
 * 模板扫描层（spec.md §3/§10——glTF 节点树→装配面元数据）。
 *
 * 输入:  glTF scene root（loader 产出——updateMatrixWorld 后）+registry
 *        prefix（家族命名前缀）
 * 输出:  ScannedNode[]（TemplateNodeMeta+对象引用+世界 AABB——锚点
 *        派生与 cap/克隆的运行时载体）
 *
 * 规格说明（spec §3 逐组锚点表/§10 命名规约）：
 *   - 命名解析：``<prefix>__<group>__<part>[__ax<掩码>][__nc]``——组词
 *     equip→equipment/inst→instance 归一；非规约名静默跳过（分组 Empty
 *     等结构节点合法在场）；规约名语法病=AssembleSpecError（资产病）；
 *   - 掩码换轴：命名轴字母=Blender 系（x=长/y=宽/z=上），扫描层换轴
 *     到 glTF 系 [x=长,y=上,z=宽]（y↔z 互换）；缺省=DEFAULT_TRIM_STRETCH
 *     水平双向（§3）；竖直轴（Blender z）入集=语法病显式拒（数学核
 *     二防线）；
 *   - AABB=世界系（模板本地——root 无父级时即 glTF scene 系；量化
 *     重定心由节点 TRS 补偿后世界位不变[tools/blender/README.md 实测
 *     记档]——锚点/inst 基座恒用世界 AABB，勿读节点 translation 裸值）；
 *   - 锚点派生（§3 表）：shell 恒等抵消[0,0,0]；trim=节点 AABB min
 *     （安装面锚）；equipment=registry 语义锚（pool_center_bottom=
 *     模板原点[0,0,0]/aabb_min）；instance 不锚（σ=𝟙 位姿归 instanceLayout）。
 */

import * as THREE from "three";

import { AssembleSpecError } from "./computeTransforms";
import type { FamilyEntry } from "./registry";
import {
  DEFAULT_TRIM_STRETCH,
  type AxisMask,
  type GroupKind,
  type TemplateNodeMeta,
  type Vec3,
} from "./types";

/** 扫描面节点（TemplateNodeMeta+运行时载体；part=命名第三段——
 * equipment 规格键/instance 计数节点 id 的匹配位）。 */
export type ScannedNode = TemplateNodeMeta & {
  readonly part: string;
  readonly object: THREE.Object3D;
  readonly nc: boolean;
  readonly aabb: { readonly min: Vec3; readonly max: Vec3 };
};

const GROUP_ALIASES: Readonly<Record<string, GroupKind>> = {
  shell: "shell",
  trim: "trim",
  equip: "equipment",
  inst: "instance",
};

/** Blender 轴字母→glTF 槽位 [x,y,z]（§3：y↔z 互换——Blender y=宽→
 * glTF z、Blender z=上→glTF y）。 */
export function blenderMaskToGltf(mask: string): AxisMask {
  const seen = { x: false, y: false, z: false };
  for (const ch of mask) {
    if (!(ch in seen)) {
      throw new AssembleSpecError(`掩码轴字母域外：${ch}（合法 xyz）`);
    }
    seen[ch as keyof typeof seen] = true;
  }
  if (seen.z) {
    throw new AssembleSpecError(
      `掩码含 Blender 竖直轴 z：${mask}——S1 立法违例（竖直定值）`,
    );
  }
  return [seen.x, seen.z /* Blender z→glTF y 已拒恒 false */, seen.y];
}

/**
 * 解析规约名（前缀门+组归一+掩码/nc 尾段）。
 * 非本族前缀/段数不足=null（跳过——结构节点合法）；语法病=显式拒。
 */
export function parseConventionName(
  name: string,
  prefix: string,
): { group: GroupKind; part: string; stretch: AxisMask; nc: boolean } | null {
  const segments = name.split("__");
  if (segments.length < 3 || segments[0] !== prefix) {
    return null;
  }
  const group = GROUP_ALIASES[segments[1] ?? ""];
  if (group === undefined) {
    throw new AssembleSpecError(`组词表外：${segments[1]} in ${name}`);
  }
  const part = segments[2];
  if (part === undefined || part === "") {
    throw new AssembleSpecError(`part 空：${name}`);
  }
  let stretch: AxisMask = DEFAULT_TRIM_STRETCH;
  let nc = false;
  for (const tail of segments.slice(3)) {
    if (tail !== undefined && tail.startsWith("ax") && tail.length > 2) {
      stretch = blenderMaskToGltf(tail.slice(2));
    } else if (tail === "nc") {
      nc = true;
    } else {
      throw new AssembleSpecError(`尾段非法：${tail} in ${name}（合法 __ax…/__nc）`);
    }
  }
  return { group, part, stretch, nc };
}

function aabbOf(object: THREE.Object3D): { min: Vec3; max: Vec3 } {
  const box = new THREE.Box3().setFromObject(object);
  if (box.isEmpty()) {
    throw new AssembleSpecError(`节点无几何 AABB：${object.name}`);
  }
  return {
    min: [box.min.x, box.min.y, box.min.z],
    max: [box.max.x, box.max.y, box.max.z],
  };
}

/**
 * 扫描模板节点树（root.updateMatrixWorld 前置由调用方/loader 保证）。
 * equipment 锚=registry 语义锚（§3 表）；掩码仅 trim 消费（shell/equip/
 * instance 槽位保留缺省值——数学核只对 trim 校验掩码）。
 */
export function groupScan(
  root: THREE.Object3D,
  entry: Pick<FamilyEntry, "prefix" | "equipment">,
): ScannedNode[] {
  root.updateMatrixWorld(true);
  const nodes: ScannedNode[] = [];
  root.traverse((object) => {
    const parsed = parseConventionName(object.name, entry.prefix);
    if (parsed === null) {
      return;
    }
    const aabb = aabbOf(object);
    let anchor: Vec3;
    if (parsed.group === "shell") {
      anchor = [0, 0, 0];
    } else if (parsed.group === "trim") {
      anchor = aabb.min;
    } else if (parsed.group === "equipment") {
      const spec = entry.equipment[parsed.part];
      anchor = spec?.anchor === "pool_center_bottom" ? [0, 0, 0] : aabb.min;
    } else {
      anchor = aabb.min; // instance：布局面消费 AABB（基座语义）——锚槽不参与
    }
    nodes.push({
      name: object.name,
      part: parsed.part,
      group: parsed.group,
      stretch: parsed.stretch,
      anchor,
      object,
      nc: parsed.nc,
      aabb,
    });
  });
  if (nodes.length === 0) {
    throw new AssembleSpecError(
      `模板零规约节点（prefix=${entry.prefix}——资产/registry 前缀不匹配）`,
    );
  }
  return nodes;
}
