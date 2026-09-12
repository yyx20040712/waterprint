/**
 * 模板单元实例（批3 主体——辐流二沉池首族装配渲染器）。
 *
 * 输入:  registry 条目+取数节点（kind=dimSource）+场景（inst 计数源）
 *        +剖切平面组
 * 输出:  逐 placement 模板实例（扫描节点×统一公式组变换+inst 布局+
 *        S5 逐实例剖切帽盖）；降级态=盒体（deviation）/原语（加载/失败）
 *
 * 规格说明（spec §3 单元级合成 World=T(pos)·Ry(rz)·M_group；§7 S4/S5
 *   stencil 条款；§11 P7）：
 *   - 组变换承载：每扫描节点包一层 group（position=translation、
 *     scale=scale——列矢量 M=T(t)·diag(σ) 的组件层分解）；
 *   - 材质：glb 单源（Blender authored）；剖切面/DoubleSide（被剖非
 *     封盖件穿帮防线 §7）经共享材质 effect 落地（同族实例共享——
 *     clippingPlanes 引用=Scene useMemo 产出，稳定引用零重编译抖动）；
 *   - inst 组（P7）：数量唯一真源=场景图 `{unit}::{part}` 节点
 *     instance_count；无值=不渲染+fallbackLog 登记（禁推导）；
 *   - S5 帽盖：shell 未标 __nc 子件双 writer（IncrementWrap 背/
 *     DecrementWrap 正——奇偶计数 NotEqual 0 多封闭体叠加保持）+
 *     逐实例 cap 面（足迹对角×1.1 过幅；邻池距<过幅钳至间距 95%——
 *     共面帽盖零重复绘制[§7 S5 定案]）；renderOrder 色 0/writer 1/cap 2
 *     （C2VD SectionCap 同制）。
 */

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import type { LoadedTemplate } from "../assemble/loader";
import { loadTemplate } from "../assemble/loader";
import { instanceLayout } from "../assemble/instanceLayout";
import { logFallback } from "../assemble/fallbackLog";
import type { FamilyEntry } from "../assemble/registry";
import { assemblePlan } from "../assemble/templateAssembly";
import { sceneDimsToTarget } from "../assemble/computeTransforms";
import { templateCounters, noteInstances } from "../assemble/probe";
import { strippedClone } from "../assemble/strippedClone";
import type { Vec3 } from "../assemble/types";
import type { RenderNode, RenderScene } from "../lib/projectScene";
import { PoolBox } from "./PoolBox";
import { TemplateCap } from "./TemplateCap";

type TemplateUnitProps = {
  readonly entry: FamilyEntry;
  readonly unitId: string;
  readonly dimNode: RenderNode;
  readonly scene: RenderScene;
  readonly clippingPlanes?: THREE.Plane[];
};

/** P7 计数源：场景图 `{unit}::{part}` 节点 instance_count（无值=null）。 */
export function sceneInstanceCount(
  scene: RenderScene,
  unitId: string,
  part: string,
): number | null {
  const id = `${unitId}::${part}`;
  const found = [...scene.solids, ...scene.internals].find((n) => n.id === id);
  return found === undefined ? null : found.instanceCount;
}

export function TemplateUnit(props: TemplateUnitProps) {
  const { entry, unitId, dimNode, scene, clippingPlanes } = props;
  const [tpl, setTpl] = useState<LoadedTemplate | null>(null);
  useEffect(() => {
    let alive = true;
    loadTemplate(entry)
      .then((loaded) => {
        if (alive) {
          setTpl(loaded);
        }
      })
      .catch((error: unknown) => {
        // 失败=原语保持+登记（降级链终点非静默；不缓存——loader 自愈重试）
        logFallback(unitId, "template_load_error", String(error));
      });
    return () => {
      alive = false;
    };
  }, [entry, unitId]);

  const plan = useMemo(
    () => (tpl === null ? null : assemblePlan(entry, dimNode.kind, dimNode.dims, tpl.nodes)),
    [tpl, entry, dimNode.kind, dimNode.dims],
  );

  useEffect(() => {
    if (plan === null || plan.kind !== "fallback") {
      return;
    }
    const reason =
      plan.reason.ok === false && "reason" in plan.reason
        ? plan.reason.reason
        : "deviation";
    const detail =
      plan.reason.ok === false && "ratio" in plan.reason
        ? `ratio=${plan.reason.ratio}`
        : plan.reason.ok === false && "message" in plan.reason
          ? plan.reason.message
          : undefined;
    logFallback(unitId, `deviation:${String(reason)}`, detail);
  }, [plan, unitId]);

  // 共享材质 effect：剖切面挂载+被剖非封盖件 DoubleSide（§7）。
  // 变更面=clippingPlanes 引用（Scene useMemo 产出——toggle 才变）。
  const lastPlanes = useRef<THREE.Plane[] | undefined>(undefined);
  useEffect(() => {
    if (tpl === null) {
      return;
    }
    const planesChanged = lastPlanes.current !== clippingPlanes;
    lastPlanes.current = clippingPlanes;
    for (const node of tpl.nodes) {
      node.object.traverse((object) => {
        const mesh = object as THREE.Mesh;
        if (mesh.material === undefined || mesh.material === null) {
          return;
        }
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        for (const material of materials) {
          material.clippingPlanes = clippingPlanes ?? null;
          material.side = node.group === "shell" ? THREE.FrontSide : THREE.DoubleSide;
          if (planesChanged) {
            material.needsUpdate = true;
          }
        }
      });
    }
  }, [tpl, clippingPlanes]);

  // inst 组布局（P7）——数量源=场景图；无值不渲染+登记（一次性）。
  // 段二：registry instanceModes/instanceSpacing 声明布局模式与点距
  // （缺省 ring=辐流立柱；grid/line/rect=box 族位置推导面——数量不推导）。
  const instGroups = useMemo(() => {
    if (tpl === null || plan === null || plan.kind !== "template") {
      return [];
    }
    const laid = [];
    for (const proto of tpl.nodes) {
      if (proto.group !== "instance") {
        continue;
      }
      const count = sceneInstanceCount(scene, unitId, proto.part);
      const layout = instanceLayout(proto.aabb, count, plan.shell, {
        mode: entry.instanceModes?.[proto.part],
        spacing: entry.instanceSpacing[proto.part] ?? undefined,
        envelope: { L0: entry.templateSize.L0, W0: entry.templateSize.W0 },
      });
      if (layout.kind === "skipped") {
        logFallback(
          unitId,
          layout.reason === "bad_spacing"
            ? "instance_bad_spacing"
            : "instance_no_scene_count",
          layout.reason === "bad_spacing"
            ? `${proto.part}——instanceSpacing 声明病（非 ring 模式须正间距）`
            : `${proto.part}——P7：数量唯一真源=场景图 instance_count`,
        );
        continue;
      }
      laid.push({ proto, positions: layout.positions });
    }
    return laid;
  }, [tpl, plan, scene, unitId, entry]);

  useEffect(() => {
    for (const { proto, positions } of instGroups) {
      noteInstances(proto.part, positions.length);
    }
  }, [instGroups]);

  useEffect(() => {
    if (plan !== null && plan.kind === "template") {
      templateCounters.rendered += dimNode.placements.length;
    } else if (plan !== null) {
      templateCounters.fallbackBoxes += dimNode.placements.length;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps —— 挂载期计数（probe 读数面）
  }, [plan]);

  if (tpl === null || plan === null) {
    // 加载中/失败：原语渲染保持（降级链终点——非静默：失败已登记）
    return <PrimitiveFallback node={dimNode} clippingPlanes={clippingPlanes} />;
  }
  if (plan.kind === "fallback") {
    const target = sceneDimsToTarget(dimNode.kind, dimNode.dims);
    return <FallbackBoxes node={dimNode} target={target} clippingPlanes={clippingPlanes} />;
  }
  const capPlane = clippingPlanes?.[0] ?? null;
  return (
    <>
      {dimNode.placements.map((placement, index) => (
        <group key={index} position={placement} rotation={dimNode.rotation}>
          {plan.groups.map(({ node, transform }) => (
            <group
              key={node.name}
              position={toThree(transform.translation)}
              scale={toThree(transform.scale)}
            >
              <primitive object={node.object.clone()} />
            </group>
          ))}
          {instGroups.map(({ proto, positions }) =>
            positions.map((position, i) => (
              <group key={`${proto.name}:${i}`} position={toThree(position)}>
                {/* 布局位置=绝对模板位（几何中心语义）——clone 清
                    position 保 scale/rotation（量化补偿——门二 P0）；
                    辐流立柱数据面恒 skipped[P7]，本路径段二 CASS 滗水器
                    首次真实消费 */}
                <primitive object={strippedClone(proto.object)} />
              </group>
            )),
          )}
          {capPlane !== null ? (
            <TemplateCap
              plan={plan}
              placement={placement}
              placements={dimNode.placements}
              plane={capPlane}
            />
          ) : null}
        </group>
      ))}
    </>
  );
}

function toThree(v: Vec3): [number, number, number] {
  return [v[0], v[1], v[2]];
}


/** 加载期/失败原语保持（多 placement 同构——placement 外包 group）。 */
function PrimitiveFallback({
  node,
  clippingPlanes,
}: {
  node: RenderNode;
  clippingPlanes?: THREE.Plane[];
}) {
  return (
    <>
      {node.placements.map((placement, index) => (
        <group key={index} position={placement} rotation={node.rotation}>
          <PoolBox
            node={{ ...node, position: [0, 0, 0], rotation: [0, 0, 0], placements: [node.position] }}
            clippingPlanes={clippingPlanes}
            edges
          />
        </group>
      ))}
    </>
  );
}

/** 盒体降级（deviation 出域——spec §6「比例出域→盒体降级+登记」）。 */
function FallbackBoxes({
  node,
  target,
  clippingPlanes,
}: {
  node: RenderNode;
  target: { L: number; W: number; H: number } | null;
  clippingPlanes?: THREE.Plane[];
}) {
  const dims = useMemo(() => {
    if (target !== null) {
      return { length: target.L, width: target.W, depth: target.H };
    }
    const diameter = node.dims["diameter"] ?? 1;
    return { length: node.dims["length"] ?? diameter, width: node.dims["width"] ?? diameter, depth: node.dims["depth"] ?? 1 };
  }, [target, node.dims]);
  return (
    <>
      {node.placements.map((placement, index) => (
        <group key={index} position={placement} rotation={node.rotation}>
          <PoolBox
            node={{ ...node, kind: "box", dims, position: [0, 0, 0], rotation: [0, 0, 0], placements: [node.position] }}
            clippingPlanes={clippingPlanes}
            edges
          />
        </group>
      ))}
    </>
  );
}
