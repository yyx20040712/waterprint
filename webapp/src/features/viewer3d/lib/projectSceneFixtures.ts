/**
 * 投影层测试夹具工厂（B3 R6 自 projectScene.test.ts 拆出——三分共用面）：
 * fixture() 场景构造器+FixtureNode 节点类型+VERSION 版本锚串。
 *
 * 输入:  overrides 局部覆盖（Partial<Record<string, unknown>>——展开合入
 *        基准场景）
 * 输出:  fixture() 基准场景 Record（六节点：四 solid+水面+ground+aerator
 *        12 实例——core/layers 两测试件消费）；FixtureNode 类型；VERSION
 *        常量（SCENE_VERSION 门断言锚）。纯工厂零断言（lib/ 内非 .test
 *        不参 vitest 收集）；零 import（自足数据面）
 */

/** 场景版本锚（SCENE_VERSION 门用例断言串——RENDER_SCENE_VERSION 同值）。 */
export const VERSION = "waterprint-scene-5/z-up/m";

/** 夹具节点形态（宽松面——投影层入口本收 unknown）。 */
export type FixtureNode = {
  node_id: string;
  semantic: string;
  primitive: { kind: string; dims: Record<string, number>; semantic: string };
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: [number, number, number];
  instance_count?: number;
};

export function fixture(overrides?: Partial<Record<string, unknown>>): Record<string, unknown> {
  const nodes: FixtureNode[] = [
    {
      node_id: "pool-1",
      semantic: "pool_wall",
      primitive: { kind: "box", dims: { length: 10, width: 4, depth: 3 }, semantic: "pool_wall" },
      position: [0, 0, 0],
    },
    {
      node_id: "pool-2",
      semantic: "pool_wall",
      primitive: { kind: "cylinder", dims: { diameter: 6, depth: 4 }, semantic: "pool_wall" },
      position: [20, 0, 0],
    },
    {
      node_id: "chan-1",
      semantic: "channel",
      primitive: { kind: "extrusion", dims: { length: 8, width: 1, depth: 1.5 }, semantic: "channel" },
      position: [30, 0, 0],
    },
    {
      node_id: "surf-1",
      semantic: "water_surface",
      primitive: { kind: "water_surface", dims: { length: 10, width: 4, depth: 2.5 }, semantic: "water_surface" },
      position: [0, 0.1, 0],
    },
    {
      node_id: "ground-1",
      semantic: "ground",
      primitive: { kind: "plane", dims: { length: 50, width: 30 }, semantic: "ground" },
      position: [0, -0.01, 0],
    },
    {
      node_id: "unit-1::aerator",
      semantic: "aerator",
      primitive: { kind: "box", dims: { length: 0.5, width: 0.5, depth: 0.5 }, semantic: "aerator" },
      position: [2, 0.5, 1],
      instance_count: 12,
    },
  ];
  const scene: Record<string, unknown> = {
    scene_version: VERSION,
    condition_key: "design",
    root: ["pool-1", "pool-2", "chan-1", "surf-1"],
    nodes,
  };
  return { ...scene, ...overrides };
}
