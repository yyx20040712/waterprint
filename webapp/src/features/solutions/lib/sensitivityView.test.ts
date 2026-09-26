/**
 * sensitivityView 窄化门 node 测试（批6e——compareView.test 同构：非法
 * 形状逐门拒负例族+合法载荷四键面收口）。
 *
 * 输入:  narrowSensitivityResponse（/api/calc/sensitivity 响应形状）
 * 输出:  断言：合法载荷→视图四键面/工况前缀拒/行条目键域拒/数值域拒
 */
import { describe, expect, it } from "vitest";

import {
  SensitivityViewError,
  narrowSensitivityResponse,
} from "./sensitivityView";

/** 合法载荷基线（server services.sensitivity 形状）。 */
const validPayload = (): Record<string, unknown> => ({
  project_id: "p1",
  task_id: "t1",
  stale: false,
  design_hash: "abc123",
  engine_version: "0.1.0",
  data_version: "coefficients@1.8.0",
  baseline_key: "design",
  condition_keys: ["design_offline_municipal_aao"],
  rows: [
    {
      field_id: "cost_opex_yuan_a",
      design_value: 100.0,
      values: { design_offline_municipal_aao: 100.0 },
      deltas: { design_offline_municipal_aao: 0.0 },
    },
  ],
});

describe("narrowSensitivityResponse（批6e 窄化门）", () => {
  it("合法载荷→视图四键面（消费面裁剪——溯源键不入视图）", () => {
    const view = narrowSensitivityResponse(validPayload());
    expect(view.stale).toBe(false);
    expect(view.design_hash).toBe("abc123");
    expect(view.condition_keys).toEqual(["design_offline_municipal_aao"]);
    expect(view.rows).toEqual([
      {
        field_id: "cost_opex_yuan_a",
        design_value: 100,
        values: { design_offline_municipal_aao: 100 },
        deltas: { design_offline_municipal_aao: 0 },
      },
    ]);
  });

  it("顶层缺键逐门拒（消息含缺失键名——定位反查）", () => {
    for (const key of ["stale", "design_hash", "condition_keys", "rows", "task_id"]) {
      const payload = validPayload();
      delete payload[key];
      expect(() => narrowSensitivityResponse(payload)).toThrow(SensitivityViewError);
      expect(() => narrowSensitivityResponse(payload)).toThrow(
        new RegExp(`顶层缺 ${key}`),
      );
    }
  });

  it("stale 非布尔/工况键非字典前缀拒（GR-20 镜像执法）", () => {
    const notBool = validPayload();
    notBool.stale = "yes";
    expect(() => narrowSensitivityResponse(notBool)).toThrow("stale 非布尔");
    const badPrefix = validPayload();
    badPrefix.condition_keys = ["avg"];
    expect(() => narrowSensitivityResponse(badPrefix)).toThrow(
      "非 design_offline_ 前缀",
    );
  });

  it("行条目键域与数值域逐门拒（缺键/非有限数/映射非数值）", () => {
    const missing = validPayload();
    (missing.rows as Array<Record<string, unknown>>)[0] = { field_id: "x" };
    expect(() => narrowSensitivityResponse(missing)).toThrow("rows[0] 缺");
    const nanValue = validPayload();
    (nanValue.rows as Array<Record<string, unknown>>)[0] = {
      field_id: "x", design_value: Number.NaN, values: {}, deltas: {},
    };
    expect(() => narrowSensitivityResponse(nanValue)).toThrow(
      "rows[0].design_value 非有限数值",
    );
    const badMap = validPayload();
    (badMap.rows as Array<Record<string, unknown>>)[0] = {
      field_id: "x", design_value: 1, values: { k: "str" }, deltas: {},
    };
    expect(() => narrowSensitivityResponse(badMap)).toThrow("非有限数值");
  });

  it("顶层非对象拒（传输破损面 fail-visible）", () => {
    expect(() => narrowSensitivityResponse(null)).toThrow("顶层非对象");
    expect(() => narrowSensitivityResponse("x")).toThrow("顶层非对象");
  });
});
