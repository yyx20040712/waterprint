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
  nodeParamOverride,
  poolCapSize,
  poolGroupPlan,
  POOL_CAP_EPS,
  type PoolClaim,
  type PoolGroupInputs,
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
