/**
 * inst 布局资产级端到端测试（门二 P0 复审要求——真实量化 glb 驱动）。
 *
 * 输入:  webapp/public/assets/units/cass_batch.glb（meshopt 量化资产）
 * 输出:  契约断言——量化补偿 scale 在渲染克隆上保留（尺寸不坍缩）+
 *        decant line_z 两实例位姿（cx 安装线/y 几何中心/±3.75 均布）
 *
 * 规格（门二实证教训）：meshopt 把几何归一化到单位盒、节点 TRS scale
 *   承载尺寸恢复——剥离 scale 的克隆渲染 AABB 坍缩（7m 桁架→2m 盒，
 *   P0 实录）。本测=真实资产上锁死该回归面（合成 AABB 测试无此证据力）。
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "meshoptimizer";

import { groupScan } from "./groupScan";
import { instanceLayout } from "./instanceLayout";
import { assemblePlan } from "./templateAssembly";
import { familyForUnit } from "./registry";
import { strippedClone as strippedCloneRef } from "./strippedClone";

const ASSET = join(__dirname, "../../../../public/assets/units/cass_batch.glb");

async function loadCass(): Promise<THREE.Object3D> {
  const buffer = readFileSync(ASSET);
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  const gltf = await loader.parseAsync(
    buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength),
    "",
  );
  const root = gltf.scene;
  root.updateMatrixWorld(true);
  return root;
}

it("真实量化资产：decant 克隆保留补偿 scale（渲染 AABB≈建模尺寸）", async () => {
  const root = await loadCass();
  const entry = familyForUnit("municipal_cass");
  expect(entry).not.toBeNull();
  if (entry === null) {
    return;
  }
  const scanned = groupScan(root, entry);
  const decant = scanned.find((s) => s.part === "decant");
  expect(decant).toBeDefined();
  if (decant === undefined) {
    return;
  }

  // 量化补偿在节点 TRS 上（scale≠1——本测前提自证）
  expect(Math.abs(decant.object.scale.x - 1)).toBeGreaterThan(0.01);

  // 装配+布局（golden 恒等 dims——shell=𝟙）
  const plan = assemblePlan(entry, "box", { length: 48.5, width: 19.5, depth: 5.5 }, scanned);
  expect(plan.kind).toBe("template");
  if (plan.kind !== "template") {
    return;
  }
  const layout = instanceLayout(decant.aabb, 2, plan.shell, {
    mode: "line_z",
    spacing: 7.5,
  });
  expect(layout.kind).toBe("laid");
  if (layout.kind !== "laid") {
    return;
  }
  expect(layout.positions).toHaveLength(2);

  // 渲染克隆（清 position 保 scale）：世界 AABB 尺寸≈建模（7.0×1.1×4.1
  // 档——量化容差内）；P0 回归面=尺寸坍缩到 2×0.3×1.2 档即红
  for (const position of layout.positions) {
    const clone = strippedCloneRef(decant.object);
    clone.position.set(position[0], position[1], position[2]);
    const box = new THREE.Box3().setFromObject(clone);
    const size = box.getSize(new THREE.Vector3());
    expect(size.x).toBeGreaterThan(5);   // 悬臂 7m 档（坍缩≈2）
    expect(size.z).toBeGreaterThan(3.5); // 堰槽 4m 档（坍缩≈1.2）
  }

  // 位姿断言：cx=安装线≈18.7（DECANT_X−2.9——量化损失 ~0.02m 档容差
  // [门二 P2 记档：inst 件无量化误差门]）、y=几何中心档、z=±3.75
  const [p0, p1] = layout.positions;
  expect(p0?.[0]).toBeCloseTo((15.23 + 22.17) / 2, 1);
  expect(p1?.[2]).toBeCloseTo(3.75, 9);
  expect(p0?.[2]).toBeCloseTo(-3.75, 9);
  for (const p of layout.positions) {
    expect(p[1]).toBeGreaterThan(3.5);   // boom_z 中心档 4.8±（坍缩位≈0）
    expect(p[1]).toBeLessThan(6.0);
  }
}, 30000);
