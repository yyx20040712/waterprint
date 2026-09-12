/**
 * groupScan 单测（批3 主体——命名解析/掩码换轴/锚点派生/显式拒）。
 *
 * 输入:  合成 THREE 节点树（规约命名+几何 AABB——零资产依赖）
 * 输出:  契约断言（§3 逐组锚点表/§10 命名语法/前缀门/组归一）
 */

import * as THREE from "three";
import { describe, expect, it } from "vitest";

import { AssembleSpecError } from "./computeTransforms";
import { blenderMaskToGltf, groupScan, parseConventionName } from "./groupScan";
import { registryEntries } from "./registry";
import { DEFAULT_TRIM_STRETCH } from "./types";

const entryOf = registryEntries()["municipal_erchunchi"];
if (entryOf === undefined) {
  throw new Error("registry 缺辐流条目（测试前提——noUncheckedIndexedAccess 收窄位）");
}
const ENTRY = entryOf;
const PREFIX = "clarifier";

function meshNamed(name: string, size: [number, number, number], pos: [number, number, number]): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size));
  mesh.name = name;
  mesh.position.set(pos[0], pos[1], pos[2]);
  return mesh;
}

function buildTree(): THREE.Group {
  const root = new THREE.Group();
  root.add(meshNamed("clarifier__shell__wall", [40, 4, 40], [0, 2, 0]));
  // 走道（缺省掩码）：AABB y∈[4,4.12]——安装面锚=AABB min
  root.add(meshNamed("clarifier__trim__walkway", [43.2, 0.12, 43.2], [0, 4.06, 0]));
  // 单向件：Blender 掩码 x（长向）→glTF [true,false,false]
  root.add(meshNamed("clarifier__trim__rail_seg__axx", [10, 0.05, 0.05], [5, 4.3, -6]));
  // 水平双向显式（Blender x+y → glTF [x,z]）
  root.add(meshNamed("clarifier__trim__ring__axxy", [2, 0.05, 2], [0, 4.4, 0]));
  // equipment：registry 锚 pool_center_bottom（center_well）与 aabb_min（bridge）
  root.add(meshNamed("clarifier__equip__center_well", [4.8, 2.8, 4.8], [0, 1.8, 0]));
  root.add(meshNamed("clarifier__equip__bridge", [21.5, 0.14, 0.9], [10.75, 3.7, 0]));
  // instance 原型：几何本地（0..1.1）+节点平移——AABB 世界位=基座
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.1, 0.05));
  post.name = "clarifier__inst__rail_post";
  post.position.set(21.5, 4.12, 0);
  root.add(post);
  // 结构节点（分组 Empty 名）：非规约名静默跳过
  const structural = new THREE.Group();
  structural.name = "shell";
  root.add(structural);
  // nc 件：装饰不入封盖集
  root.add(meshNamed("clarifier__shell__decor__nc", [1, 0.1, 1], [0, 4.05, 10]));
  return root;
}

describe("blenderMaskToGltf（§3 y↔z 换轴）", () => {
  it("Blender x（长）→glTF x 槽", () => {
    expect(blenderMaskToGltf("x")).toEqual([true, false, false]);
  });
  it("Blender x+y（水平双向）→glTF x+z 槽（y↔z 互换）", () => {
    expect(blenderMaskToGltf("xy")).toEqual([true, false, true]);
  });
  it("Blender z（竖直）入集=S1 违例显式拒", () => {
    expect(() => blenderMaskToGltf("xz")).toThrow(AssembleSpecError);
    expect(() => blenderMaskToGltf("z")).toThrow(AssembleSpecError);
  });
  it("域外字母拒", () => {
    expect(() => blenderMaskToGltf("w")).toThrow(AssembleSpecError);
  });
});

describe("parseConventionName（§10 语法）", () => {
  it("组词表 equip/inst 归一 equipment/instance", () => {
    expect(parseConventionName("f__equip__w", "f")?.group).toBe("equipment");
    expect(parseConventionName("f__inst__p", "f")?.group).toBe("instance");
  });
  it("前缀不符=null（他族/结构名跳过）", () => {
    expect(parseConventionName("aao__shell__wall", PREFIX)).toBeNull();
    expect(parseConventionName("shell", PREFIX)).toBeNull();
  });
  it("尾段非法显式拒", () => {
    expect(() => parseConventionName("f__shell__w__bogus", "f")).toThrow(AssembleSpecError);
  });
  it("__nc 旗标解析", () => {
    expect(parseConventionName("f__shell__d__nc", "f")?.nc).toBe(true);
  });
});

describe("groupScan（§3 逐组锚点派生）", () => {
  it("全组扫描：结构名跳过+组归一+掩码落位", () => {
    const nodes = groupScan(buildTree(), ENTRY);
    const byName = new Map(nodes.map((n) => [n.name, n]));
    expect(nodes).toHaveLength(8);
    const walkway = byName.get("clarifier__trim__walkway");
    expect(walkway?.group).toBe("trim");
    expect(walkway?.stretch).toEqual(DEFAULT_TRIM_STRETCH);
    expect(walkway?.nc).toBe(false);
    expect(byName.get("clarifier__shell__decor__nc")?.nc).toBe(true);
    expect(byName.get("clarifier__trim__rail_seg__axx")?.stretch).toEqual([true, false, false]);
    expect(byName.get("clarifier__trim__ring__axxy")?.stretch).toEqual([true, false, true]);
    expect(byName.get("clarifier__equip__center_well")?.group).toBe("equipment");
    expect(byName.get("clarifier__inst__rail_post")?.part).toBe("rail_post");
  });
  it("trim 锚=AABB min（安装面锚——含对象平移；float32 几何按分量 5 位）", () => {
    const walkway = groupScan(buildTree(), ENTRY).find((n) => n.name.endsWith("walkway"));
    const [ax, ay, az] = walkway?.anchor ?? [NaN, NaN, NaN];
    expect(ax).toBeCloseTo(-21.6, 5);
    expect(ay).toBeCloseTo(4, 5);
    expect(az).toBeCloseTo(-21.6, 5);
  });
  it("equipment registry 锚 pool_center_bottom=[0,0,0]；缺省 aabb_min", () => {
    const nodes = groupScan(buildTree(), ENTRY);
    const well = nodes.find((n) => n.part === "center_well");
    expect(well?.anchor).toEqual([0, 0, 0]);
    const bridge = nodes.find((n) => n.part === "bridge");
    expect(bridge?.anchor[0]).toBeCloseTo(0, 5); // AABB min x=0（桥自池心起）
    expect(bridge?.anchor[1]).toBeCloseTo(3.63, 5);
  });
  it("instance 原型 AABB=世界基座位（节点平移计入；Box 居中于 position——y 半幅 0.55）", () => {
    const post = groupScan(buildTree(), ENTRY).find((n) => n.part === "rail_post");
    for (const [got, want] of [
      [post?.aabb.min[0], 21.475],
      [post?.aabb.min[1], 3.57],
      [post?.aabb.min[2], -0.025],
      [post?.aabb.max[0], 21.525],
      [post?.aabb.max[1], 4.67],
      [post?.aabb.max[2], 0.025],
    ] as const) {
      expect(got).toBeCloseTo(want, 5);
    }
  });
  it("前缀不匹配全树=零规约节点显式拒（资产/registry 病）", () => {
    const root = new THREE.Group();
    root.add(meshNamed("aao__shell__wall", [1, 1, 1], [0, 0, 0]));
    expect(() => groupScan(root, ENTRY)).toThrow(AssembleSpecError);
  });
});
