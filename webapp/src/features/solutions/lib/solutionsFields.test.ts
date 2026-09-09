/**
 * 职责：unitOptionLabel 纯函数四分支 node 测试（B2 扩面 R-1——下拉中文
 * 化形态收口；G1-01 回退分支探针未覆盖面在此补直测）。
 *
 * 输入:  内联目录映射夹具（manifest 命中/缺席+builtin 命中/未就绪）
 * 输出:  四分支断言（纯中文名/英文 id 回退/中文名+（node_id）后缀/
 *        旧形态 unitId（kind）防自重复）
 */
import { describe, expect, it } from "vitest";

import { unitOptionLabel } from "./solutionsFields";

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
