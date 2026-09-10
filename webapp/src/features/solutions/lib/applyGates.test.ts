/**
 * applyGates 纯函数测试（P0-2——三闸语义锁）。
 *
 * 输入:  narrowEnumSource/applyGateReason/applyDriftWarn 纯函数
 * 输出:  三源窄化（缺键 null 降级）/闸①②禁用因分支（表未挂载恒 null/
 *        缺 unit_id 历史载荷/下拉错选/单元缺席）/闸③漂移（缺源不警示）
 */
import { describe, expect, it } from "vitest";

import {
  applyDriftWarn,
  applyGateReason,
  narrowEnumSource,
} from "./applyGates";

const UNITS = [{ unitId: "municipal_aao" }, { unitId: "inlet" }];

describe("narrowEnumSource（三源窄化——缺键 null 诚实降级）", () => {
  it("齐源载荷全收（unit_id/design_hash/currentDesignHash）", () => {
    const source = narrowEnumSource(
      { unit_id: "municipal_aao", design_hash: "abc" },
      { metadata: { content_hash: "abc" } },
    );
    expect(source).toEqual({
      resultUnitId: "municipal_aao",
      resultDesignHash: "abc",
      currentDesignHash: "abc",
    });
  });

  it("历史任务载荷缺键/空串=null（P0-2 扩源前任务面）", () => {
    const source = narrowEnumSource(
      { feasible_count: 3 },
      { metadata: { content_hash: "abc" } },
    );
    expect(source.resultUnitId).toBeNull();
    expect(source.resultDesignHash).toBeNull();
    expect(source.currentDesignHash).toBe("abc");
  });

  it("raw 体未就绪=当前哈希 null（不可证漂移面）", () => {
    expect(narrowEnumSource({}, undefined).currentDesignHash).toBeNull();
    expect(narrowEnumSource({ unit_id: "" }, {}).resultUnitId).toBeNull();
  });
});

describe("applyGateReason（闸①②禁用因）", () => {
  it("表未挂载恒 null（无应用面）", () => {
    expect(
      applyGateReason({
        enumeratedUnitId: null,
        unitId: null,
        units: [],
        unitsReady: true,
        tableEnabled: false,
      }),
    ).toBeNull();
  });

  it("闸②前置：历史任务缺 unit_id=述因（F5 修复后残余面）", () => {
    expect(
      applyGateReason({
        enumeratedUnitId: null,
        unitId: "municipal_aao",
        units: UNITS,
        unitsReady: true,
        tableEnabled: true,
      }),
    ).toContain("历史任务载荷缺 unit_id");
  });

  it("闸①：下拉错选≠表源=禁用述因（防 Y 方案发 X 单元）", () => {
    const reason = applyGateReason({
      enumeratedUnitId: "municipal_aao",
      unitId: "inlet",
      units: UNITS,
      unitsReady: true,
      tableEnabled: true,
    });
    expect(reason).toContain("方案表来自 municipal_aao");
    expect(reason).toContain("切回 municipal_aao");
  });

  it("下拉空=未选定不触发闸①（回填前中性态）", () => {
    expect(
      applyGateReason({
        enumeratedUnitId: "municipal_aao",
        unitId: null,
        units: UNITS,
        unitsReady: true,
        tableEnabled: true,
      }),
    ).toBeNull();
  });

  it("闸②：表源单元不在 design 投影=禁用（删除面前置守卫）", () => {
    const reason = applyGateReason({
      enumeratedUnitId: "removed_unit",
      unitId: "removed_unit",
      units: UNITS,
      unitsReady: true,
      tableEnabled: true,
    });
    expect(reason).toContain("已不在当前项目设计");
  });

  it("GD-N-01：units 清单未就绪=跳闸②（空表≠已删除——防误禁窗口）", () => {
    expect(
      applyGateReason({
        enumeratedUnitId: "municipal_aao",
        unitId: "municipal_aao",
        units: [],
        unitsReady: false,
        tableEnabled: true,
      }),
    ).toBeNull();
  });

  it("齐态放行=null", () => {
    expect(
      applyGateReason({
        enumeratedUnitId: "municipal_aao",
        unitId: "municipal_aao",
        units: UNITS,
        unitsReady: true,
        tableEnabled: true,
      }),
    ).toBeNull();
  });
});

describe("applyDriftWarn（闸③——呈裁⑧ 甲案警示后放行）", () => {
  const BASE = narrowEnumSource(
    { unit_id: "u", design_hash: "h1" },
    { metadata: { content_hash: "h1" } },
  );

  it("哈希一致=不警示", () => {
    expect(applyDriftWarn(BASE, true)).toBe(false);
  });

  it("哈希漂移=警示（应用后旧枚举表对新设计）", () => {
    expect(applyDriftWarn({ ...BASE, currentDesignHash: "h2" }, true)).toBe(true);
  });

  it("缺任一源/表未挂载=不可证不警示", () => {
    expect(applyDriftWarn({ ...BASE, currentDesignHash: null }, true)).toBe(false);
    expect(applyDriftWarn({ ...BASE, resultDesignHash: null }, true)).toBe(false);
    expect(applyDriftWarn({ ...BASE, currentDesignHash: "h2" }, false)).toBe(false);
  });
});
