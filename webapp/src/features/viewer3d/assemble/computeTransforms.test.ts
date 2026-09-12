/**
 * 分组变换数学核冻结单测（assemble/spec.md §4 数值算例的机器锚——批3
 * 首件「纯函数单测冻结」件）。
 *
 * 输入:  sceneDimsToTarget/shellScale/groupTransform/transformDeterminant
 *        +projectScene 实跑（轴映射跨面对拍）+spec §4 冻结数值
 * 输出:  轴对应表/统一公式（S1 位置缩放+截面逆缩放抵消）/极端算例
 *        （S2-② H=3/6 栏杆 z 锚定+截面恒定）/equipment 保圆与 S3 数据链
 *        /S6 行列式恒正/instance 越权拒（P7）全组断言
 */

import { describe, expect, it } from "vitest";

import { projectScene } from "../lib/projectScene";
import { VERSION } from "../lib/projectSceneFixtures";

import {
  AssembleSpecError,
  groupTransform,
  sceneDimsToTarget,
  shellScale,
  transformDeterminant,
} from "./computeTransforms";
import {
  DEFAULT_TRIM_STRETCH,
  type TemplateNodeMeta,
  type TemplateSize,
} from "./types";

/** 冻结算例模板（spec §4）：AAO 廊道族典型 60×12×5。 */
const AAO_TYPICAL: TemplateSize = { L0: 60, W0: 12, H0: 5 };
/** 冻结算例模板（spec §4）：辐流二沉池圆柱族典型 Φ40×4。 */
const CLARIFIER_TYPICAL: TemplateSize = { L0: 40, W0: 40, H0: 4 };

/** 冻结算例节点：北缘栏杆段（延伸向 x=长；模板米制 AABB x∈[−30,30]、
 * y∈[5.0,6.2]（立柱 1.2m 高——规范定值立法对象）、z∈[−6,−5.94]）。 */
const NORTH_RAIL: TemplateNodeMeta = {
  name: "aao__trim__north_rail__axx",
  group: "trim",
  stretch: [true, false, false],
  anchor: [-30, 5.0, -6],
};

/** 冻结算例节点：池顶走道板（缺省掩码=水平双向；板厚 0.15m 定值）。 */
const WALKWAY: TemplateNodeMeta = {
  name: "aao__trim__walkway",
  group: "trim",
  stretch: DEFAULT_TRIM_STRETCH,
  anchor: [-30, 5.0, -6],
};

/** 顶点变换（列矢量 M=T(t)·diag(σ)——缩放先作用）。 */
function applyVertex(
  transform: {
    translation: readonly [number, number, number];
    scale: readonly [number, number, number];
  },
  v: readonly [number, number, number],
): [number, number, number] {
  return [
    transform.scale[0] * v[0] + transform.translation[0],
    transform.scale[1] * v[1] + transform.translation[1],
    transform.scale[2] * v[2] + transform.translation[2],
  ];
}

/** 向量逐分量近似断言（IEEE754——除法/乘差出 1e−16 级尾差，冻结数值
 *  断言用 12 位容差；零值分量同样经容差路径）。 */
function expectVec3Close(
  actual: readonly number[],
  expected: readonly number[],
): void {
  expect(actual).toHaveLength(expected.length);
  actual.forEach((value, index) => {
    expect(value).toBeCloseTo(expected[index]!, 12);
  });
}

describe("sceneDimsToTarget 轴对应表（S2-③）", () => {
  it("box 三键归并：length/width/depth→L/W/H", () => {
    expect(sceneDimsToTarget("box", { length: 10, width: 4, depth: 3 }))
      .toEqual({ L: 10, W: 4, H: 3 });
  });

  it("cylinder：diameter→L=W（直径口径）、depth→H", () => {
    expect(sceneDimsToTarget("cylinder", { diameter: 6, depth: 4 }))
      .toEqual({ L: 6, W: 6, H: 4 });
  });

  it("缺键/族域外 kind→null（extrusion/plane 不入 v1 冻结面）", () => {
    expect(sceneDimsToTarget("box", { length: 10, width: 4 })).toBeNull();
    expect(sceneDimsToTarget("extrusion", { length: 8, width: 1, depth: 1.5 })).toBeNull();
    expect(sceneDimsToTarget("plane", { length: 50, width: 30 })).toBeNull();
  });
});

describe("shellScale 轴序与防线", () => {
  it("三值互异证轴序：x=L/L0（长）、y=H/H0（深）、z=W/W0（宽）", () => {
    // target 6×3×2 / typical 3×1×1 → [2, 2, 3]——若轴序错位则出 [2,3,2] 等
    expect(shellScale({ L: 6, W: 3, H: 2 }, { L0: 3, W0: 1, H0: 1 }))
      .toEqual([2, 2, 3]);
  });

  it("恒等：目标=典型尺寸→[1,1,1]", () => {
    expect(shellScale({ L: 60, W: 12, H: 5 }, AAO_TYPICAL)).toEqual([1, 1, 1]);
  });

  it("模板典型尺寸非正=registry 声明病显式拒", () => {
    expect(() => shellScale({ L: 6, W: 3, H: 2 }, { L0: 0, W0: 1, H0: 1 }))
      .toThrow(AssembleSpecError);
  });

  it("目标尺寸非正=deviation 先裁防线（本层 throw=漏裁兜底）", () => {
    expect(() => shellScale({ L: 6, W: 0, H: 2 }, { L0: 3, W0: 1, H0: 1 }))
      .toThrow(AssembleSpecError);
  });
});

describe("轴映射跨面对拍（S2-③——模板系与场景系换轴同构）", () => {
  it("projectScene 实跑位置=模板 Blender→glTF 换轴式：(x,z,−y) 同点同出", () => {
    // 场景 z-up 点（x=3 东、y=4 北、z=5 标高）经 projectScene（L5R 唯一
    // 换轴点）应出 three 世界 (3, 5, −4)；模板 Blender 同语义点（x=长/东、
    // y=宽/北、z=深/上）经 +Y up 导出换轴 (x,z,−y) 出同值——两系在 three
    // 世界同构直配（spec §1 轴对应表的机器锚）。
    const scene = {
      scene_version: VERSION,
      condition_key: "ck",
      root: ["u1::pool_wall"],
      nodes: [
        {
          node_id: "u1::pool_wall",
          semantic: "pool_wall",
          primitive: {
            kind: "box",
            dims: { length: 10, width: 4, depth: 3 },
            semantic: "pool_wall",
          },
          position: [3, 4, 5],
        },
      ],
    };
    const out = projectScene(scene as never);
    const scenePoint = out.solids[0]!.position;
    const blenderPoint: readonly [number, number, number] = [3, 4, 5];
    const gltfPoint: readonly [number, number, number] = [
      blenderPoint[0],
      blenderPoint[2],
      -blenderPoint[1],
    ];
    expect(scenePoint).toEqual([3, 5, -4]);
    expect(gltfPoint).toEqual(scenePoint);
  });
});

describe("groupTransform·shell", () => {
  it("σ=s 精确+translation=[0,0,0]（锚点项恒等抵消——任意锚）", () => {
    const s = shellScale({ L: 48, W: 12, H: 3 }, AAO_TYPICAL);
    const node: TemplateNodeMeta = {
      name: "aao__shell__wall",
      group: "shell",
      stretch: [false, false, false],
      anchor: [5, 7, 9],
    };
    expect(groupTransform(node, s)).toEqual({ translation: [0, 0, 0], scale: s });
  });
});

describe("groupTransform·trim 极端算例（S2-②——spec §4 冻结数值）", () => {
  it("H=3（sH=0.6）：立柱底随壁顶 5.0→3.0、截面高恒 1.2、延伸向全长 48", () => {
    const s = shellScale({ L: 48, W: 12, H: 3 }, AAO_TYPICAL); // [0.8, 0.6, 1]
    const t = groupTransform(NORTH_RAIL, s);
    expect(t).toEqual({ translation: [0, -2, 0], scale: [0.8, 1, 1] });
    // 立柱底（模板 y=5.0=壁顶）→3.0（目标壁顶=H）；柱顶 6.2→4.2（高恒 1.2）
    expect(applyVertex(t, [-30, 5.0, -6])).toEqual([-24, 3.0, -6]);
    expect(applyVertex(t, [30, 6.2, -5.94])).toEqual([24, 4.2, -5.94]);
  });

  it("H=6（sH=1.2）：立柱底 5.0→6.0、柱顶→7.2（截面高恒 1.2 不拉伸）", () => {
    const s = shellScale({ L: 60, W: 12, H: 6 }, AAO_TYPICAL); // [1, 1.2, 1]
    const t = groupTransform(NORTH_RAIL, s);
    expectVec3Close(t.translation, [0, 1, 0]); // 5×(1.2−1)=0.999…98 尾差容差
    expect(t.scale).toEqual([1, 1, 1]);
    expectVec3Close(applyVertex(t, [-30, 5.0, -6]), [-30, 6.0, -6]);
    expectVec3Close(applyVertex(t, [30, 6.2, -5.94]), [30, 7.2, -5.94]);
  });

  it("宽向锚定：W=6（sW=0.5）北缘栏杆缘 −6→−3 随壳缘（定值轴锚点随壳走）", () => {
    const s = shellScale({ L: 60, W: 6, H: 5 }, AAO_TYPICAL); // [1, 1, 0.5]
    const t = groupTransform(NORTH_RAIL, s);
    expect(t.translation).toEqual([0, 0, 3]);
    expect(applyVertex(t, [-30, 5.0, -6])[2]).toBe(-3); // 目标北缘=−W/2
  });

  it("缺省掩码=水平双向：走道板 σ=[sL,1,sW]、板厚 0.15 恒定", () => {
    expect(DEFAULT_TRIM_STRETCH).toEqual([true, false, true]);
    const s = shellScale({ L: 48, W: 12, H: 3 }, AAO_TYPICAL); // [0.8, 0.6, 1]
    const t = groupTransform(WALKWAY, s);
    expect(t.scale).toEqual([0.8, 1, 1]);
    // 板顶/板底（模板 y=5.0/5.15）→3.0/3.15（壁顶随壳、厚 0.15 恒定）
    expect(applyVertex(t, [0, 5.0, 0])[1]).toBe(3.0);
    expect(applyVertex(t, [0, 5.15, 0])[1]).toBeCloseTo(3.15, 12);
  });

  it("trim 竖直轴（y）入延伸集=S1 立法违例显式拒", () => {
    const s = shellScale({ L: 48, W: 12, H: 3 }, AAO_TYPICAL);
    const bad: TemplateNodeMeta = { ...NORTH_RAIL, stretch: [true, true, false] };
    expect(() => groupTransform(bad, s)).toThrow(AssembleSpecError);
  });
});

describe("groupTransform·equipment（S3 数据链+保圆）", () => {
  it("中心筒：u=actual/templateFeature 精确+三轴等模（保圆）+池心锚不动", () => {
    const s = shellScale({ L: 30, W: 30, H: 4 }, CLARIFIER_TYPICAL); // [0.75,1,0.75]
    const node: TemplateNodeMeta = {
      name: "clarifier__equip__center_well",
      group: "equipment",
      stretch: [false, false, false],
      anchor: [0, 0, 0], // pool_center_bottom 语义锚=模板原点
    };
    // S3 数据链：actualFactor=0.12×直径 30→actual=3.6；模板特征=3.0m
    const t = groupTransform(node, s, { templateFeature: 3.0, actual: 3.6 });
    expect(t.scale).toEqual([1.2, 1.2, 1.2]); // 等比保圆
    expect(t.translation).toEqual([0, 0, 0]); // 池心池底不动
    // 筒体 x∈[−1.5,1.5]（Φ3.0）→[−1.8,1.8]（Φ3.6）居中；底 y=0 贴底
    expectVec3Close(applyVertex(t, [-1.5, 0, -1.5]), [-1.8, 0, -1.8]);
    expectVec3Close(applyVertex(t, [1.5, 2.4, 1.5]), [1.8, 2.88, 1.8]);
  });

  it("端部设备 aabb_min 锚：安装锚随壳（模板壁 20→目标壁 15）", () => {
    const s = shellScale({ L: 30, W: 30, H: 4 }, CLARIFIER_TYPICAL); // [0.75,1,0.75]
    const node: TemplateNodeMeta = {
      name: "clarifier__equip__decantor",
      group: "equipment",
      stretch: [false, false, false],
      anchor: [20, 0, 0], // 东壁安装锚（aabb_min 语义）
    };
    const t = groupTransform(node, s, { templateFeature: 2.5, actual: 3.0 });
    expect(t.scale).toEqual([1.2, 1.2, 1.2]);
    expect(t.translation).toEqual([-9, 0, 0]); // 20×(0.75−1.2)
    // 跨壁几何 x∈[19,21]→[13.8,16.2]——锚点 20→15 恰在目标壁（L/2=15）
    expect(applyVertex(t, [20, 0, 0])[0]).toBe(15);
    expect(applyVertex(t, [19, 0, 0])[0]).toBeCloseTo(13.8, 12);
    expect(applyVertex(t, [21, 0, 0])[0]).toBeCloseTo(16.2, 12);
  });

  it("缺特征规格/特征非正=registry 声明病显式拒", () => {
    const s = shellScale({ L: 30, W: 30, H: 4 }, CLARIFIER_TYPICAL);
    const node: TemplateNodeMeta = {
      name: "clarifier__equip__center_well",
      group: "equipment",
      stretch: [false, false, false],
      anchor: [0, 0, 0],
    };
    expect(() => groupTransform(node, s)).toThrow(AssembleSpecError);
    expect(() => groupTransform(node, s, { templateFeature: 0, actual: 3.6 }))
      .toThrow(AssembleSpecError);
  });
});

describe("行列式硬条款（S6——实例矩阵 det>0）", () => {
  it("全组类产出 det>0（shell/trim/equipment——绕序不翻前提）", () => {
    const s = shellScale({ L: 48, W: 9, H: 3 }, AAO_TYPICAL);
    const shellNode: TemplateNodeMeta = {
      name: "aao__shell__wall", group: "shell",
      stretch: [false, false, false], anchor: [0, 0, 0],
    };
    const equipNode: TemplateNodeMeta = {
      name: "aao__equip__mixer", group: "equipment",
      stretch: [false, false, false], anchor: [0, 0, 0],
    };
    expect(transformDeterminant(groupTransform(shellNode, s).scale))
      .toBeGreaterThan(0);
    expect(transformDeterminant(groupTransform(NORTH_RAIL, s).scale))
      .toBeGreaterThan(0);
    expect(
      transformDeterminant(
        groupTransform(equipNode, s, { templateFeature: 1.0, actual: 0.8 }).scale,
      ),
    ).toBeGreaterThan(0);
  });
});

describe("instance 组越权拒（P7 呈裁未决）", () => {
  it("instance 不经 groupTransform（instanceLayout 归批3 主体）", () => {
    const s = shellScale({ L: 48, W: 12, H: 3 }, AAO_TYPICAL);
    const node: TemplateNodeMeta = {
      name: "aao__inst__rail_post",
      group: "instance",
      stretch: [false, false, false],
      anchor: [0, 0, 0],
    };
    expect(() => groupTransform(node, s)).toThrow(AssembleSpecError);
  });
});
