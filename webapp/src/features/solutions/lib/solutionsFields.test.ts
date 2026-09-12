/**
 * 职责：unitOptionLabel 纯函数四分支 node 测试（B2 扩面 R-1——下拉中文
 * 化形态收口；G1-01 回退分支探针未覆盖面在此补直测）。
 *
 * 输入:  内联目录映射夹具（manifest 命中/缺席+builtin 命中/未就绪）
 * 输出:  四分支断言（纯中文名/英文 id 回退/中文名+（node_id）后缀/
 *        旧形态 unitId（kind）防自重复）
 */
import { describe, expect, it } from "vitest";

import {
  enumerateOptions,
  isUnitEnumerable,
  narrowDimFields,
  narrowGridFields,
  unitOptionLabel,
} from "./solutionsFields";

describe("unitOptionLabel（B2 扩面——单元下拉中文化形态）", () => {
  const catalog = new Map([
    ["municipal_aao", "AAO 生物池"],
    ["municipal_input", "市政输入"],
  ]);

  it("manifest 单元目录命中=纯中文名", () => {
    expect(
      unitOptionLabel({ unitId: "municipal_aao", kind: null }, catalog),
    ).toBe("AAO 生物池");
  });

  it("manifest 单元键缺席=英文 id 诚实回退", () => {
    expect(
      unitOptionLabel({ unitId: "municipal_cass", kind: null }, catalog),
    ).toBe("municipal_cass");
  });

  it("builtin 节点目录命中=kind 中文名+（node_id）辨异后缀", () => {
    expect(
      unitOptionLabel({ unitId: "inlet", kind: "municipal_input" }, catalog),
    ).toBe("市政输入（inlet）");
  });

  it("builtin 目录未就绪=旧形态 unitId（kind）防自重复（G1-01）", () => {
    expect(
      unitOptionLabel({ unitId: "inlet", kind: "municipal_input" }, new Map()),
    ).toBe("inlet（municipal_input）");
  });
});

describe("isUnitEnumerable/enumerateOptions（F6——枚举下拉过滤判据）", () => {
  const catalog = new Map([["municipal_aao", "AAO 生物池"]]);
  const entries = [
    {
      unit_id: "municipal_aao",
      params: [{ field_id: "n", grid: [2, 3, 4] }],
    },
    {
      unit_id: "mine_water_chenshachi",
      params: [{ field_id: "q", grid: null, range: { min: 0, max: 9 } }],
    },
    { unit_id: "conveyance_jishuijing", params: [] },
  ];

  it("grid 档位非空=可枚举", () => {
    expect(
      isUnitEnumerable({ unitId: "municipal_aao", kind: null }, entries),
    ).toBe(true);
  });

  it("grid null/空数组/params 空=不可枚举（键在场诚实拒）", () => {
    expect(
      isUnitEnumerable({ unitId: "mine_water_chenshachi", kind: null }, entries),
    ).toBe(false);
    expect(
      isUnitEnumerable({ unitId: "conveyance_jishuijing", kind: null }, entries),
    ).toBe(false);
  });

  it("目录键缺席（该单元无目录条目）=不可枚举", () => {
    expect(
      isUnitEnumerable({ unitId: "municipal_uv", kind: null }, entries),
    ).toBe(false);
  });

  it("目录未就绪（null）=fail-open 全可（数据面故障不阻断提交）", () => {
    expect(isUnitEnumerable({ unitId: "municipal_uv", kind: null }, null)).toBe(
      true,
    );
  });

  it("builtin 节点经 kind 键判（目录 kind 条目命中）", () => {
    expect(
      isUnitEnumerable({ unitId: "inlet", kind: "municipal_input" }, [
        { unit_id: "municipal_input", params: [] },
      ]),
    ).toBe(false);
  });

  it("enumerateOptions：可枚举零后缀零禁用+不可枚举 disabled 附提示", () => {
    const options = enumerateOptions(
      [
        { unitId: "municipal_aao", kind: null },
        { unitId: "mine_water_chenshachi", kind: null },
      ],
      entries,
      catalog,
    );
    expect(options).toEqual([
      { value: "municipal_aao", label: "AAO 生物池", disabled: false },
      {
        value: "mine_water_chenshachi",
        label: "mine_water_chenshachi（无档位参数）",
        disabled: true,
      },
    ]);
  });
});

describe("narrowDimFields（V2 GOV5 批尾——dim_fields 载荷窄化）", () => {
  it("合法载荷透传（manifest.out_dims 声明面——label_zh=null 直传）", () => {
    const result = {
      grid_fields: [{ key: "n", dim: "DIMENSIONLESS", label_zh: "池数（格）" }],
      dim_fields: [
        { key: "v_o", dim: "VOLUME", label_zh: "好氧区容积" },
        { key: "v_unseen", dim: "", label_zh: null },
      ],
    };
    expect(narrowDimFields(result)).toEqual([
      { key: "v_o", dim: "VOLUME", label_zh: "好氧区容积" },
      { key: "v_unseen", dim: "", label_zh: null },
    ]);
    // grid_fields 不受影响（两族独立窄化）
    expect(narrowGridFields(result)).toEqual([
      { key: "n", dim: "DIMENSIONLESS", label_zh: "池数（格）" },
    ]);
  });

  it("载荷缺键/形状非法 → 空（历史任务降级——表挂载仍可）", () => {
    expect(narrowDimFields(null)).toEqual([]);
    expect(narrowDimFields({})).toEqual([]);
    expect(narrowDimFields({ dim_fields: [{ key: 1 }] })).toEqual([]);
  });
});
