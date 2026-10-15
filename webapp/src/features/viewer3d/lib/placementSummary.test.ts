/**
 * placementSummary 纯函数测试（F9——C2-visual 批：摆放态横幅判据）。
 *
 * 输入:  countPlacedUnits/designNodesCount/placementSummary 纯函数
 * 输出:  在场单元计数（首段去重/pipe 排除）/design.nodes 可布置窄化
 *        （内置 kind 节点排除）/横幅判据（placed<total+不可达 null）
 */
import { describe, expect, it } from "vitest";

import {
  countPlacedUnits,
  designNodesCount,
  placementSummary,
} from "./placementSummary";
import type { RenderNode, RenderScene } from "./projectScene";

function node(
  id: string,
  placements: Array<[number, number, number]> = [[0, 0, 0]],
): RenderNode {
  return {
    id,
    kind: "box",
    semantic: "pool_wall",
    position: placements[0] ?? [0, 0, 0],
    rotation: [0, 0, 0],
    dims: { length: 1, depth: 1, width: 1 },
    instanceCount: placements.length,
    placements,
  };
}

function sceneOf(
  solids: RenderNode[],
  waters: RenderNode[] = [],
): RenderScene {
  return {
    sceneVersion: "6",
    conditionKey: "ck",
    root: [],
    solids,
    waters,
    internals: [],
    boundaries: [],
    routes: [],
    bounds: null,
  };
}

describe("countPlacedUnits（scene 在场单元数——首段去重）", () => {
  it("多构型件合一单元+waters 同单元不重复计", () => {
    const scene = sceneOf(
      [
        node("aao::pool_wall"),
        node("aao::channel"),
        node("uv::pool_wall"),
      ],
      [node("aao::water_surface")],
    );
    expect(countPlacedUnits(scene)).toBe(2);
  });

  it("pipe:: 场景级件排除+裸 id 排除", () => {
    const scene = sceneOf([node("pipe::1"), node("orphan")]);
    expect(countPlacedUnits(scene)).toBe(0);
  });
});

describe("designNodesCount（可布置单元总数——内置 kind 节点排除）", () => {
  it("design.nodes 键数剔除 kind 节点（19 节点含 4 内置=15 可布置）", () => {
    const detail = {
      design: {
        nodes: {
          aao: {},
          uv: { params: { n: 4 } },
          inlet: { kind: "municipal_input" },
          junction: { kind: "junction" },
        },
      },
    };
    expect(designNodesCount(detail)).toBe(2);
  });

  it("弱类型防御：非对象形状链=null（横幅不挂 fail-open）", () => {
    expect(designNodesCount(null)).toBeNull();
    expect(designNodesCount({})).toBeNull();
    expect(designNodesCount({ design: {} })).toBeNull();
    expect(designNodesCount({ design: { nodes: [] } })).toBeNull();
  });
});

describe("placementSummary（横幅判据——structures 非空且 placed<total）", () => {
  const arranging = {
    design: { nodes: { aao: {}, uv: {} }, site: { structures: { aao: { x: 0, y: 0, rotation: 0, ground_elevation: null } } } },
  };
  const fallback = {
    design: { nodes: { aao: {}, uv: {} }, site: { structures: {} } },
  };

  it("摆放进行中+部分在场=判据成立（1/2）", () => {
    const summary = placementSummary(sceneOf([node("aao::pool_wall")]), arranging);
    expect(summary).toEqual({ placed: 1, total: 2 });
  });

  it("摆放全覆盖=判据不成立（2/2 返 null——GV-01 R 轮：判据收进纯函数）", () => {
    const summary = placementSummary(
      sceneOf([node("aao::pool_wall"), node("uv::pool_wall")]),
      arranging,
    );
    expect(summary).toBeNull();
  });

  it("structures 空=兜底满场不挂横幅（E1 勘正面——防无几何单元常态误报）", () => {
    expect(placementSummary(sceneOf([node("aao::pool_wall")]), fallback)).toBeNull();
  });

  it("详情不可达/形状异常=null（横幅不挂）", () => {
    expect(placementSummary(sceneOf([node("aao::pool_wall")]), null)).toBeNull();
    expect(placementSummary(sceneOf([node("aao::pool_wall")]), {})).toBeNull();
  });
});
