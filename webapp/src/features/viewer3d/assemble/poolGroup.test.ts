/**
 * 池组排布计划冻结单测（assemble/poolGroup.ts——S11 接线批机器锚）。
 *
 * 输入:  poolGroupPlan 纯函数+冻结算例（三呈裁 2026-09-13 口径：
 *        ①spacing=max(格长,格宽)+gap ②分池排布 ③unit 域格宽=池组宽÷池数）
 * 输出:  池数双源优先级/工况派生/单池平面派生/spacing 组合/在用槽与
 *        缺位槽同构一致性/契约病 null 族断言
 */

import { describe, expect, it } from "vitest";

import { missingSlotPlaceholders } from "./missingSlots";
import {
  buildPoolBadges,
  buildPoolPlans,
  groupExtents,
  nodeParamOverride,
  poolCapSize,
  poolGroupPlan,
  POOL_CAP_EPS,
  type PoolClaim,
  type PoolGroupInputs,
  type PoolGroupPlan,
} from "./poolGroup";
import { registryEntries } from "./registry";

const CASS_GROUP = { countParam: "n_pool", templateScope: "cell", gap: 1 } as const;
const AAO_GROUP = { countParam: "n", templateScope: "unit", gap: 1 } as const;

/** builder 测试 claims（真实 registry 条目——两族声明面同源）。 */
function registryClaims(): Map<string, PoolClaim> {
  const entries = registryEntries();
  const aao = entries["municipal_aao"];
  const cass = entries["municipal_cass"];
  const claims = new Map<string, PoolClaim>();
  if (aao !== undefined && cass !== undefined) {
    claims.set("municipal_aao", {
      entry: aao,
      dimNode: { dims: { length: 95, width: 38, depth: 5.3 } },
    });
    claims.set("municipal_cass", {
      entry: cass,
      dimNode: { dims: { length: 48.5, width: 19.5, depth: 5.5 } },
    });
  }
  return claims;
}

const CATALOG = [
  {
    unit_id: "municipal_aao",
    params: [{ field_id: "n", default: 2 }],
  },
  {
    unit_id: "municipal_cass",
    params: [{ field_id: "n_pool", default: 4 }],
  },
];

function cassInputs(overrides?: Partial<PoolGroupInputs>): PoolGroupInputs {
  return {
    poolGroup: CASS_GROUP,
    unitId: "municipal_cass",
    dims: { length: 48.5, width: 19.5, depth: 5.5 },
    countDefault: 4,
    countOverride: undefined,
    conditionKey: "design",
    ...overrides,
  };
}

describe("poolGroupPlan 池组计划（S11 接线——三呈裁口径）", () => {
  it("正常工况（design）全池：nActive=nPools、缺位空", () => {
    const plan = poolGroupPlan(cassInputs())!;
    expect(plan.nPools).toBe(4);
    expect(plan.nActive).toBe(4);
    expect(plan.missing).toEqual([]);
    // 呈裁①：spacing=max(48.5,19.5)+1
    expect(plan.spacing).toBe(49.5);
    expect(plan.cellL).toBe(48.5);
    expect(plan.cellW).toBe(19.5);
    // 在用槽=4 槽（分池多份渲染位——呈裁②）
    expect(plan.activeSlots).toHaveLength(4);
  });

  it("检修工况（design_offline_<unit_id>）n−1 池：缺位=尾槽", () => {
    const plan = poolGroupPlan(
      cassInputs({ conditionKey: "design_offline_municipal_cass" }),
    )!;
    expect(plan.nActive).toBe(3);
    expect(plan.missing).toEqual([{ index: 3, position: [24.75, 0, 24.75] }]);
    expect(plan.activeSlots).toHaveLength(3);
  });

  it("他单元检修工况（design_offline_其他单元）本单元全池", () => {
    const plan = poolGroupPlan(
      cassInputs({ conditionKey: "design_offline_municipal_aao" }),
    )!;
    expect(plan.nActive).toBe(4);
    expect(plan.missing).toEqual([]);
  });

  it("override 优先于 catalog default（项目改池数）", () => {
    const plan = poolGroupPlan(cassInputs({ countOverride: 6 }))!;
    expect(plan.nPools).toBe(6);
    // cols=ceil(sqrt(6))=3 方阵——6 槽全在用
    expect(plan.activeSlots).toHaveLength(6);
  });

  it("override 病值（负数/NaN/字符串）回退 catalog default", () => {
    for (const bad of [-2, Number.NaN, "4", null]) {
      const plan = poolGroupPlan(cassInputs({ countOverride: bad }))!;
      expect(plan.nPools).toBe(4);
    }
  });

  it("AAO unit 域：格宽=池组宽÷池数（呈裁③——整单元模板 1 份）", () => {
    const plan = poolGroupPlan({
      poolGroup: AAO_GROUP,
      unitId: "municipal_aao",
      dims: { length: 95, width: 38, depth: 5.3 },
      countDefault: 2,
      countOverride: undefined,
      conditionKey: "design",
    })!;
    expect(plan.cellW).toBe(19); // 38/2
    expect(plan.cellL).toBe(95);
    // 呈裁①：spacing=max(95,19)+1=96
    expect(plan.spacing).toBe(96);
    expect(plan.templateScope).toBe("unit");
  });

  it("AAO 检修（n=2→1 用）：缺位 1 槽=格尺寸框位", () => {
    const plan = poolGroupPlan({
      poolGroup: AAO_GROUP,
      unitId: "municipal_aao",
      dims: { length: 95, width: 38, depth: 5.3 },
      countDefault: 2,
      countOverride: undefined,
      conditionKey: "design_offline_municipal_aao",
    })!;
    expect(plan.nActive).toBe(1);
    // cols=2、rows=1；index 1=(0,1)→(+48,0,0)
    expect(plan.missing).toEqual([{ index: 1, position: [48, 0, 0] }]);
    expect(plan.activeSlots).toEqual([[-48, 0, 0]]);
  });

  it("单池全停（nActive=0）：在用槽空、缺位=全槽", () => {
    const plan = poolGroupPlan(
      cassInputs({
        countOverride: 1,
        conditionKey: "design_offline_municipal_cass",
      }),
    )!;
    expect(plan.nActive).toBe(0);
    expect(plan.activeSlots).toEqual([]);
    expect(plan.missing).toEqual([{ index: 0, position: [0, 0, 0] }]);
  });

  it("在用槽与缺位槽同构：activeSlots=冻结函数全槽切片", () => {
    const plan = poolGroupPlan(
      cassInputs({ conditionKey: "design_offline_municipal_cass" }),
    )!;
    const allSlots = missingSlotPlaceholders(4, 0, 49.5);
    expect(plan.activeSlots).toEqual(allSlots.slice(0, 3).map((s) => s.position));
    // 缺位恰=全槽尾段（拼合完备——无槽位缺口/重叠）
    expect([
      ...plan.activeSlots,
      ...plan.missing.map((s) => s.position),
    ]).toEqual(allSlots.map((s) => s.position));
  });

  it("契约病 null 族：无 default/dims 病/gap 病", () => {
    expect(poolGroupPlan(cassInputs({ countDefault: null }))).toBeNull();
    // 双源皆病（override=0 无效+default=null）→null
    expect(
      poolGroupPlan(cassInputs({ countOverride: 0, countDefault: null })),
    ).toBeNull();
    expect(
      poolGroupPlan(cassInputs({ dims: { width: 19.5, depth: 5.5 } })),
    ).toBeNull();
    expect(
      poolGroupPlan(cassInputs({ dims: { length: -1, width: 19.5 } })),
    ).toBeNull();
    expect(
      poolGroupPlan(cassInputs({ dims: { length: 48.5, width: 0 } })),
    ).toBeNull();
    expect(
      poolGroupPlan(
        cassInputs({ poolGroup: { countParam: "n_pool", templateScope: "cell", gap: 0 } }),
      ),
    ).toBeNull();
  });

  it("AAO unit 域池数病除零面：nPools≥1 闸下 width/nPools 恒有限", () => {
    // nPools=1 的 unit 域（单格单元）：格宽=池组宽直等价
    const plan = poolGroupPlan({
      poolGroup: AAO_GROUP,
      unitId: "municipal_aao",
      dims: { length: 95, width: 38 },
      countDefault: 1,
      countOverride: undefined,
      conditionKey: "design",
    })!;
    expect(plan.cellW).toBe(38);
    expect(plan.spacing).toBe(96);
  });

  it("poolCapSize=max(格长,格宽)+ε：恒覆盖本池剖面且不越槽（gap>ε 契约闸）", () => {
    // CASS：max=48.5 → cap=48.55 < spacing 49.5（槽间余量 0.95>0）
    expect(poolCapSize(48.5, 19.5)).toBeCloseTo(48.55, 12);
    expect(poolCapSize(48.5, 19.5)).toBeLessThan(49.5);
    // AAO 格：max=95 → 95.05 < spacing 96
    expect(poolCapSize(95, 19)).toBeLessThan(96);
    expect(POOL_CAP_EPS).toBeGreaterThan(0);
  });

  it("nodeParamOverride 弱类型窄化：正常提取/形状病链 undefined", () => {
    expect(
      nodeParamOverride(
        { design: { nodes: { municipal_cass: { n_pool: 6 } } } },
        "municipal_cass",
        "n_pool",
      ),
    ).toBe(6);
    for (const bad of [null, {}, { design: null }, { design: {} }, { design: { nodes: {} } }, { design: { nodes: { municipal_cass: null } } }]) {
      expect(
        nodeParamOverride(bad, "municipal_cass", "n_pool"),
      ).toBeUndefined();
    }
    // 缺键=undefined（非 null——与 countDefault null 语义区分）
    expect(
      nodeParamOverride(
        { design: { nodes: { municipal_cass: {} } } },
        "municipal_cass",
        "n_pool",
      ),
    ).toBeUndefined();
  });

  it("小数池数 floor（4.9 池=4 池）——builder 全链一致", () => {
    const plan = poolGroupPlan(cassInputs({ countOverride: 4.9 }))!;
    expect(plan.nPools).toBe(4);
    expect(plan.activeSlots).toHaveLength(4);
  });

  it("buildPoolPlans：catalog 双族组装+override 透传+未就绪空表", () => {
    const plans = buildPoolPlans(
      registryClaims(),
      CATALOG,
      { design: { nodes: { municipal_cass: { n_pool: 2 } } } },
      "design",
    );
    expect(plans.get("municipal_aao")?.nPools).toBe(2);
    expect(plans.get("municipal_cass")?.nPools).toBe(2); // override 2>default 4 生效
    expect(plans.get("municipal_cass")?.activeSlots).toHaveLength(2);
    // catalog 未就绪=空表（W-4 登记面——返回形态锚）
    expect(buildPoolPlans(registryClaims(), undefined, {}, "design").size).toBe(0);
    // 数据病（catalog 缺 countParam 键）=该单元缺席（logFallback 归 probe 面）
    const broken = buildPoolPlans(registryClaims(), [], {}, "design");
    expect(broken.size).toBe(0);
  });

  it("buildPoolBadges：×n/检修徽标+数据病零徽标（W-3——不捏造池数）", () => {
    const claims = registryClaims();
    const plans = buildPoolPlans(claims, CATALOG, {}, "design");
    const normal = buildPoolBadges(claims, plans, "design");
    expect(normal["municipal_aao"]).toEqual({ count: 2, active: 2, offline: false });
    expect(normal["municipal_cass"]).toEqual({ count: 4, active: 4, offline: false });
    const offline = buildPoolBadges(
      claims,
      buildPoolPlans(claims, CATALOG, {}, "design_offline_municipal_cass"),
      "design_offline_municipal_cass",
    );
    expect(offline["municipal_cass"]).toEqual({
      count: 4,
      active: 3,
      offline: true,
    });
    // 他单元检修=本单元徽标无 offline 词
    expect(offline["municipal_aao"]?.offline).toBe(false);
    // 数据病（plans 空）+offline 工况=零徽标（不伪造「×1（1/1 检修中）」）
    expect(buildPoolBadges(claims, new Map(), "design_offline_municipal_cass")).toEqual({});
  });
});

describe("groupExtents 池组足迹 AABB（F5 D1——取景并池组）", () => {
  /** cell 域 claim：锚 placements（世界位）+平面旋转。 */
  function cellClaims(
    placements: ReadonlyArray<readonly [number, number, number]> = [[100, 0, 50]],
    rotation: readonly [number, number, number] = [0, 0, 0],
  ): Map<string, PoolClaim> {
    const cass = registryEntries()["municipal_cass"];
    const claims = new Map<string, PoolClaim>();
    if (cass !== undefined) {
      claims.set("municipal_cass", {
        entry: cass,
        dimNode: {
          dims: { length: 48.5, width: 19.5, depth: 5.5 },
          placements,
          rotation,
        },
      });
    }
    return claims;
  }

  function cellPlans(
    nPools: number,
    conditionKey = "design",
  ): Map<string, PoolGroupPlan> {
    const plans = new Map<string, PoolGroupPlan>();
    plans.set(
      "municipal_cass",
      poolGroupPlan(cassInputs({ countOverride: nPools, conditionKey }))!,
    );
    return plans;
  }

  it("双池 plan → AABB 覆盖两池（半尺寸口径同构 footprintOfNode）", () => {
    // n=2→cols=2/rows=1：槽 [−24.75,0,0]/[+24.75,0,0]；cellL=48.5/cellW=19.5
    const extents = groupExtents(cellPlans(2), cellClaims());
    expect(extents).not.toBeNull();
    // x=100±(24.75+24.25)；z=50±9.75；y=槽位标高 0（足迹面零高度贡献）
    expect(extents).toEqual({ min: [51, 0, 40.25], max: [149, 0, 59.75] });
  });

  it("空 plans → null（零池组零漂移——回退 scene.bounds 原值的调用方契约）", () => {
    expect(groupExtents(new Map(), cellClaims())).toBeNull();
  });

  it("回炉 W2：claim placements 空数组 → 回退原点锚（非静默零贡献）", () => {
    // 空 placements 旧实现内层循环零执行=该池组对取景静默失踪（D1 病态
    // 复发面）；修复后回退 [[0,0,0]] 锚——n=2 槽 ±24.75+半幅 24.25 → x=±49
    const extents = groupExtents(cellPlans(2), cellClaims([]));
    expect(extents).not.toBeNull();
    expect(extents).toEqual({ min: [-49, 0, -9.75], max: [49, 0, 9.75] });
  });

  it("回炉 W2：claim placements 含非有限锚点 → 过滤后按有限锚并盒", () => {
    // NaN 锚旧实现对非首轮比较静默吞槽（破坏「取景宁大勿缺」）；修复后
    // 非有限锚剔除、有限锚 [100,0,50] 正常并盒（同双池基准例数值）
    const extents = groupExtents(
      cellPlans(2),
      cellClaims([
        [Number.NaN, 0, Number.NaN],
        [100, 0, 50],
      ]),
    );
    expect(extents).toEqual({ min: [51, 0, 40.25], max: [149, 0, 59.75] });
  });

  it("unit 域 plan 零贡献：单份模板足迹已被 dimNode 盒覆盖（不虚增取景）", () => {
    const aao = registryEntries()["municipal_aao"];
    const claims = new Map<string, PoolClaim>();
    const plans = new Map<string, PoolGroupPlan>();
    if (aao !== undefined) {
      claims.set("municipal_aao", {
        entry: aao,
        dimNode: {
          dims: { length: 192, width: 77, depth: 5.3 },
          placements: [[0, 0, 0]],
          rotation: [0, 0, 0],
        },
      });
      plans.set(
        "municipal_aao",
        poolGroupPlan({
          poolGroup: AAO_GROUP,
          unitId: "municipal_aao",
          dims: { length: 192, width: 77, depth: 5.3 },
          countDefault: 2,
          countOverride: undefined,
          conditionKey: "design",
        })!,
      );
    }
    // unit 域 activeSlots 虽为 ±96，模板单份渲染不落位——AABB=null
    expect(groupExtents(plans, claims)).toBeNull();
  });

  it("检修缺位槽计入（占位框可见——取景不缺尾槽）", () => {
    // nActive=3/4：缺位=slot 3=(+24.75,0,+24.75)——AABB 必须覆盖
    const extents = groupExtents(
      cellPlans(4, "design_offline_municipal_cass"),
      cellClaims(),
    );
    expect(extents).not.toBeNull();
    expect(extents?.max[0]).toBeCloseTo(149, 10);
    expect(extents?.max[2]).toBeCloseTo(84.5, 10); // 50+24.75+cellW/2
  });

  it("锚旋转 rz=π/2：槽偏移随旋（X 槽→世界 Z 向——TemplateUnit 外层 group 同变换）", () => {
    const extents = groupExtents(
      cellPlans(2),
      cellClaims([[0, 0, 0]], [0, Math.PI / 2, 0]),
    );
    expect(extents).not.toBeNull();
    // 槽 (±24.75,0,0) 绕 Y 转 90°→(0,0,∓24.75)；世界半幅 X=|cos|·cellL/2+
    // |sin|·cellW/2=9.75、Z=|sin|·cellL/2+|cos|·cellW/2=24.25（保守并盒；
    // 逐分量 closeTo——cos(π/2) 机器 ε 容差）
    expect(extents?.min[0]).toBeCloseTo(-9.75, 10);
    expect(extents?.max[0]).toBeCloseTo(9.75, 10);
    expect(extents?.min[1]).toBe(0);
    expect(extents?.max[1]).toBe(0);
    expect(extents?.min[2]).toBeCloseTo(-49, 10);
    expect(extents?.max[2]).toBeCloseTo(49, 10);
  });
});
