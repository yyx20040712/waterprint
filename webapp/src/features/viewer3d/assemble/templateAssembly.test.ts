/**
 * templateAssembly 单测（批3 主体——装配计划派生：目标/壳缩放/逐组
 * 变换/fallback 三路）+registry 数据面（schema+资产在场+预算）。
 *
 * 输入:  registry 实条目+合成扫描节点（groupScan.test 同构树）
 * 输出:  契约断言（§4 数值算例同源：Φ40 恒等/Φ30 保圆/出域降级/
 *        equipment 数据链 §5）
 */

import * as THREE from "three";
import { existsSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { groupScan } from "./groupScan";
import { assemblePlan, claimTemplateUnits } from "./templateAssembly";
import { familyForUnit, registryEntries } from "./registry";

const entryOf = registryEntries()["municipal_erchunchi"];
if (entryOf === undefined) {
  throw new Error("registry 缺辐流条目（测试前提——noUncheckedIndexedAccess 收窄位）");
}
const ENTRY = entryOf;
const ASSET_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../../../public/assets/units",
);

function meshNamed(name: string, size: [number, number, number], pos: [number, number, number]): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size));
  mesh.name = name;
  mesh.position.set(pos[0], pos[1], pos[2]);
  return mesh;
}

function scannedOf(): ReturnType<typeof groupScan> {
  const root = new THREE.Group();
  root.add(meshNamed("clarifier__shell__wall", [40, 4, 40], [0, 2, 0]));
  root.add(meshNamed("clarifier__trim__walkway", [43.2, 0.12, 43.2], [0, 4.06, 0]));
  root.add(meshNamed("clarifier__equip__center_well", [4.8, 2.8, 4.8], [0, 1.8, 0]));
  root.add(meshNamed("clarifier__equip__bridge", [21.5, 0.14, 0.9], [10.75, 3.7, 0]));
  root.add(meshNamed("clarifier__inst__rail_post", [0.05, 1.1, 0.05], [21.5, 4.67, 0]));
  return groupScan(root, ENTRY);
}

describe("registry 数据面（§9 schema v1+资产在场+预算门）", () => {
  it("辐流条目字段齐备（templateSize Φ40×4/域 L/H [4,14]/equipment 三件）", () => {
    expect(ENTRY).toBeDefined();
    expect(ENTRY.family).toBe("clarifier_radial");
    expect(ENTRY.templateSize).toEqual({ L0: 40, W0: 40, H0: 4 });
    expect(ENTRY.ratioDomain).toEqual([
      { key: "clarifier_L_over_H", numerator: "L", denominator: "H", min: 4, max: 14 },
    ]);
    expect(Object.keys(ENTRY.equipment).sort()).toEqual(["bridge", "bridge_drive", "center_well"]);
    expect(ENTRY.instanceSpacing["rail_post"]).toBe(1.5);
    expect(ENTRY.status).toBe("ready");
  });
  it("familyForUnit 未登记单元=null", () => {
    expect(familyForUnit("municipal_gaomidu")).toBeNull();
  });
  it("段二双族条目（AAO/CASS——box 取数+恒等锚 templateSize）", () => {
    const aao = familyForUnit("municipal_aao");
    expect(aao).not.toBeNull();
    expect(aao?.family).toBe("aao_corridor");
    expect(aao?.dimSource.primitiveKind).toBe("box");
    expect(aao?.templateSize).toEqual({ L0: 95, W0: 38, H0: 5.3 });
    expect(aao?.instanceModes).toEqual({ aerator: "grid", rail_post: "rect" });
    const cass = familyForUnit("municipal_cass");
    expect(cass?.family).toBe("cass_batch");
    expect(cass?.templateSize).toEqual({ L0: 48.5, W0: 19.5, H0: 5.5 });
    expect(cass?.instanceModes?.["decant"]).toBe("line_z");
    // 资产在场+预算（段二两族同门）
    for (const fam of ["aao_corridor", "cass_batch"]) {
      expect(statSync(join(ASSET_DIR, `${fam}.glb`)).size).toBeLessThanOrEqual(150 * 1024);
      expect(statSync(join(ASSET_DIR, `${fam}.png`)).size).toBeLessThanOrEqual(80 * 1024);
    }
  });
  it("资产在场+预算（glb ≤150KB/PNG ≤80KB——Kimi §1.5）", () => {
    const glb = join(ASSET_DIR, "clarifier_radial.glb");
    const png = join(ASSET_DIR, "clarifier_radial.png");
    expect(existsSync(glb)).toBe(true);
    expect(existsSync(png)).toBe(true);
    expect(statSync(glb).size).toBeLessThanOrEqual(150 * 1024);
    expect(statSync(png).size).toBeLessThanOrEqual(80 * 1024);
  });
});

describe("assemblePlan（§3/§4/§5/§6 契约）", () => {
  it("目标=模板尺寸 Φ40×4：全组恒等（registry actualFactor 与模板同源自检）", () => {
    const plan = assemblePlan(ENTRY, "cylinder", { diameter: 40, depth: 4 }, scannedOf());
    expect(plan.kind).toBe("template");
    if (plan.kind !== "template") {
      return;
    }
    expect(plan.shell).toEqual([1, 1, 1]);
    const byPart = new Map(plan.groups.map((g) => [g.node.part, g.transform]));
    expect(byPart.get("wall")).toEqual({ translation: [0, 0, 0], scale: [1, 1, 1] });
    // S3 数据链自检：center_well u=(0.12×40)/4.8=1；bridge u=(0.5375×40)/21.5=1
    expect(byPart.get("center_well")?.scale).toEqual([1, 1, 1]);
    expect(byPart.get("bridge")?.scale).toEqual([1, 1, 1]);
    // instance 组不入 groups（P7——instanceLayout 域）
    expect(plan.groups.some((g) => g.node.group === "instance")).toBe(false);
  });
  it("目标 Φ30×4：壳 s=[0.75,1,0.75]；中心筒 u=0.75 保圆三轴等模（§4.C 同式）", () => {
    const plan = assemblePlan(ENTRY, "cylinder", { diameter: 30, depth: 4 }, scannedOf());
    if (plan.kind !== "template") {
      throw new Error("expected template");
    }
    expect(plan.shell).toEqual([0.75, 1, 0.75]);
    const well = plan.groups.find((g) => g.node.part === "center_well");
    expect(well?.transform.scale).toEqual([0.75, 0.75, 0.75]);
    // 池心池底锚：t=(0,0,0)（§4.C——池心不动贴底）
    expect(well?.transform.translation).toEqual([0, 0, 0]);
  });
  it("trim 定值轴截面恒定+锚点随壳缘走（§4.B 宽向锚定同式）", () => {
    const plan = assemblePlan(ENTRY, "cylinder", { diameter: 20, depth: 4 }, scannedOf());
    if (plan.kind !== "template") {
      throw new Error("expected template");
    }
    const walk = plan.groups.find((g) => g.node.part === "walkway");
    expect(walk?.transform.scale).toEqual([0.5, 1, 0.5]);
    expect(walk?.transform.translation[1]).toBeCloseTo(0, 10); // y 恒定（s_y=1）
  });
  it("L/H=15 出域（Φ60×4）→fallback 携明细（§6 闭域判定）", () => {
    const plan = assemblePlan(ENTRY, "cylinder", { diameter: 60, depth: 4 }, scannedOf());
    expect(plan.kind).toBe("fallback");
    if (plan.kind === "fallback" && !plan.reason.ok && "ratio" in plan.reason) {
      expect(plan.reason.reason).toBe("ratio_out_of_domain");
      expect(plan.reason.ratio).toBe(15);
      expect(plan.reason.domain).toEqual([4, 14]);
      expect(plan.reason.key).toBe("clarifier_L_over_H");
    }
  });
  it("取数 kind 与声明不符→dim_source_mismatch", () => {
    const plan = assemblePlan(ENTRY, "box", { length: 40, width: 40, depth: 4 }, scannedOf());
    // box dims 键齐备可取数——但 entry.dimSource.primitiveKind 消费面在
    // Scene claims（本函数不门 kind）；此处验缺键路径
    const mismatch = assemblePlan(ENTRY, "extrusion", { depth: 4 }, scannedOf());
    expect(mismatch.kind === "fallback" && !mismatch.reason.ok && "reason" in mismatch.reason
      && mismatch.reason.reason === "dim_source_mismatch").toBe(true);
    expect(plan.kind).toBe("template"); // box 三键齐备=可装配（claims 面负责 kind 声明门）
  });
  it("equipment 节点缺 registry 规格→assemble_error（数学核拒收编）", () => {
    const root = new THREE.Group();
    root.add(meshNamed("clarifier__shell__wall", [40, 4, 40], [0, 2, 0]));
    root.add(meshNamed("clarifier__equip__mystery", [1, 1, 1], [0, 1, 0]));
    const plan = assemblePlan(
      ENTRY,
      "cylinder",
      { diameter: 40, depth: 4 },
      groupScan(root, ENTRY),
    );
    expect(plan.kind).toBe("fallback");
    if (plan.kind === "fallback" && !plan.reason.ok && "message" in plan.reason) {
      expect(plan.reason.reason).toBe("assemble_error");
      expect(plan.reason.message).toContain("mystery");
    }
  });
});

describe("claimTemplateUnits（Scene 分支声明——solids+internals 双扫）", () => {
  const cylinderNode = (id: string, instanceCount = 1) => ({
    id,
    kind: "cylinder",
    semantic: "pool_wall",
    position: [0, 0, 0] as [number, number, number],
    rotation: [0, 0, 0] as [number, number, number],
    dims: { diameter: 41, depth: 4.6 },
    instanceCount,
    placements: [[0, 0, 0]] as [number, number, number][],
  });
  const sceneOf = (nodes: unknown[]) =>
    ({ solids: nodes, waters: [], internals: [], boundaries: [], routes: [], root: [], bounds: null }) as never;

  it("solids 单实例池节点→声明；同单元其余构型件不入（整族承载）", () => {
    const claims = claimTemplateUnits(sceneOf([
      cylinderNode("municipal_erchunchi::pool_cylinder"),
      { ...cylinderNode("municipal_erchunchi::channel"), kind: "extrusion" },
    ]));
    expect(claims.size).toBe(1);
    expect(claims.get("municipal_erchunchi")?.dimNode.id).toBe(
      "municipal_erchunchi::pool_cylinder",
    );
  });
  it("instance_count=2 池节点路由在 internals——仍声明（S5 多实例前提）", () => {
    const claims = claimTemplateUnits(sceneOf([
      cylinderNode("municipal_erchunchi::pool_cylinder", 2),
    ]));
    const scene = {
      solids: [],
      internals: [cylinderNode("municipal_erchunchi::pool_cylinder", 2)],
    };
    const claimsInternals = claimTemplateUnits(scene as never);
    expect(claims.size).toBe(1);
    expect(claimsInternals.size).toBe(1);
  });
  it("未登记单元/空场景零声明", () => {
    expect(claimTemplateUnits(sceneOf([
      cylinderNode("municipal_chuchenchi::pool_cylinder"),
    ])).size).toBe(0);
    expect(claimTemplateUnits(null).size).toBe(0);
  });
});
