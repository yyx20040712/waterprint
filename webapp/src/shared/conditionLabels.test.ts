/**
 * conditionLabels 纯函数测试（工况面 UX 反馈批件 1）：GR-20 键族三态
 * 译名——基线词典命中/offline 拆段合成/族外原样诚实呈现。
 *
 * 输入:  conditionLabel(key, unitNames)（shared/conditionLabels——
 *        BASE_CONDITION_LABELS 静态词典+offline 前缀拆段）
 * 输出:  design/avg→工程全称；design_offline_<id>→单元中文名+检修
 *        （缺失退 id 透传）；族外键原样
 */
import { describe, expect, it } from "vitest";

import {
  BASE_CONDITION_LABELS,
  conditionLabel,
} from "./conditionLabels";

/** 索引样例（catalog name_zh 投影形态——unit_id→中文名）。 */
const NAMES: Record<string, string> = {
  aao: "AAO 生物池",
  cass: "CASS 反应池",
  fine_screen_2: "细格栅（2 号）",
};

describe("conditionLabel 工况键中文化（工况面 UX 反馈批件 1）", () => {
  it("design → 最高日最高时（工程全称——用户裁定命名）", () => {
    expect(conditionLabel("design", NAMES)).toBe("最高日最高时");
  });

  it("avg → 平均日", () => {
    expect(conditionLabel("avg", NAMES)).toBe("平均日");
  });

  it("offline 键 → 单元中文名+检修（catalog name_zh 真源合成）", () => {
    expect(conditionLabel("design_offline_aao", NAMES)).toBe(
      "AAO 生物池检修",
    );
    expect(conditionLabel("design_offline_cass", NAMES)).toBe(
      "CASS 反应池检修",
    );
  });

  it("offline 键 unit_id 含下划线 → 前缀 slice 拆段不歧义", () => {
    expect(conditionLabel("design_offline_fine_screen_2", NAMES)).toBe(
      "细格栅（2 号）检修",
    );
  });

  it("offline 键单元中文名缺失 → id 透传+检修（非猜测——catalog 未就绪退路）", () => {
    expect(conditionLabel("design_offline_unknown_unit", NAMES)).toBe(
      "unknown_unit 检修",
    );
    expect(conditionLabel("design_offline_aao", {})).toBe("aao 检修");
  });

  it("族外键 → 原样返回（诚实呈现不猜语义——dimLabels 同口径）", () => {
    expect(conditionLabel("custom_key", NAMES)).toBe("custom_key");
  });

  it("基线词典键集=design/avg 两键（GR-20 冻结面——防漏登记）", () => {
    expect(Object.keys(BASE_CONDITION_LABELS).sort()).toEqual(["avg", "design"]);
  });
});
