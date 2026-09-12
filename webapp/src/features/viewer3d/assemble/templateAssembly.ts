/**
 * 装配计划派生（spec.md §3/§5/§6——纯函数，批3 主体）。
 *
 * 输入:  registry 条目+场景图取数节点（kind+dims）+扫描面节点集
 * 输出:  AssemblyPlan——template（壳缩放+逐组变换）或 fallback
 *        （deviation 判定结果——装配器走 FallbackBox+登记）
 *
 * 规格说明（两层分工 §6：本层是决策核——deviation 数据级降级判定+
 *   数学核产出；组件层消费渲染。equipment 数据链 §5：
 *   actual=actualFactor×L（主轴——cylinder 族=diameter）→u=actual/
 *   templateFeature 等比；缺规格/非正=数学核显式拒→本层 catch 转
 *   fallback+登记（数据病防线——check_templates.mjs 语法门兜前置）。
 */

import {
  AssembleSpecError,
  groupTransform,
  sceneDimsToTarget,
  shellScale,
} from "./computeTransforms";
import { deviation } from "./deviation";
import type { FamilyEntry } from "./registry";
import { familyForUnit, isReady } from "./registry";
import type { RenderNode, RenderScene } from "../lib/projectScene";
import type { ScannedNode } from "./groupScan";
import type { DeviationResult, GroupTransform, TargetDims, Vec3 } from "./types";

/** 装配组（扫描节点+统一公式产出）。 */
export type AssemblyGroup = {
  readonly node: ScannedNode;
  readonly transform: GroupTransform;
};

export type AssemblyPlan =
  | {
      readonly kind: "template";
      readonly shell: Vec3;
      readonly target: TargetDims;
      readonly groups: readonly AssemblyGroup[];
    }
  | {
      readonly kind: "fallback";
      readonly reason:
        | DeviationResult
        | { readonly ok: false; readonly reason: "dim_source_mismatch" }
        | { readonly ok: false; readonly reason: "assemble_error"; readonly message: string };
    };

/** 装配计划（数学核异常收编=fallback——数据病不崩渲染，铁律 5）。 */
export function assemblePlan(
  entry: FamilyEntry,
  kind: string,
  dims: Record<string, number>,
  scanned: readonly ScannedNode[],
): AssemblyPlan {
  const target = sceneDimsToTarget(kind, dims);
  if (target === null) {
    return {
      kind: "fallback",
      reason: { ok: false, reason: "dim_source_mismatch" },
    };
  }
  const verdict = deviation(target, entry.ratioDomain);
  if (!verdict.ok) {
    return { kind: "fallback", reason: verdict };
  }
  try {
    const shell = shellScale(target, entry.templateSize);
    const groups: AssemblyGroup[] = [];
    for (const node of scanned) {
      if (node.group === "instance") {
        continue; // inst 组归 instanceLayout（P7——不经 groupTransform）
      }
      const spec =
        node.group === "equipment" ? equipmentSpec(entry, node, target) : undefined;
      groups.push({ node, transform: groupTransform(node, shell, spec) });
    }
    return { kind: "template", shell, target, groups };
  } catch (error) {
    return {
      kind: "fallback",
      reason: {
        ok: false,
        reason: "assemble_error",
        message:
          error instanceof AssembleSpecError
            ? error.message
            : `装配数学核异常：${String(error)}`,
      },
    };
  }
}

/** equipment 特征规格派生（§5：actual=actualFactor×L；缺声明=数学核拒
 * 路径——null 透传由 groupTransform 显式拒）。 */
function equipmentSpec(
  entry: FamilyEntry,
  node: ScannedNode,
  target: TargetDims,
): { templateFeature: number; actual: number } | undefined {
  const spec = entry.equipment[node.part];
  if (spec === undefined) {
    return undefined;
  }
  return { templateFeature: spec.templateFeature, actual: spec.actualFactor * target.L };
}

/** 单元模板声明（Scene 分支消费）：registry ready 条目×场景 solids+
 * internals——取数节点=kind 匹配 dimSource 的首节点（多实例池节点投影层
 * 路由在 internals——S5 前提）；返回 unit_id→{entry, dimNode}（同单元
 * 其余构型件由模板整族承载不重复渲染）。 */
export function claimTemplateUnits(
  scene: RenderScene | null,
): Map<string, { entry: FamilyEntry; dimNode: RenderNode }> {
  const claims = new Map<string, { entry: FamilyEntry; dimNode: RenderNode }>();
  if (scene === null) {
    return claims;
  }
  for (const node of [...scene.solids, ...scene.internals]) {
    const sep = node.id.indexOf("::");
    if (sep <= 0) {
      continue;
    }
    const unitId = node.id.slice(0, sep);
    if (claims.has(unitId)) {
      continue;
    }
    const entry = familyForUnit(unitId);
    if (entry !== null && isReady(entry) && node.kind === entry.dimSource.primitiveKind) {
      claims.set(unitId, { entry, dimNode: node });
    }
  }
  return claims;
}
