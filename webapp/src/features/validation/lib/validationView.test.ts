/**
 * 投影层纯函数测试：validation 响应窄化门+三分区/语义色/标签对照
 * （node 环境——T3 前端警告聚合批；trustView.test 同构先例）。
 *
 * 输入:  validationView 纯函数（零 DOM 零 antd import）+聚合行夹具
 *        （∅ 哨兵/双工况/单工况三形态——warning-aggregation.md §3）
 * 输出:  投影契约断言：窄化门逐类拒带键定位/三分区判据（∅→声明级、
 *        ≥2→工况聚合、单工况→直通）/服务端序稳定过滤/语义色三映射/
 *        影响面与工况键文案词典
 */
import { describe, expect, it } from "vitest";

import {
  ValidationViewError,
  conditionKeysText,
  narrowValidationObservation,
  partitionWarnings,
  scopeLabel,
  severityLabel,
  severityTone,
  type AggregatedWarningRow,
  type ValidationObservation,
} from "./validationView";

/** 全字段健康样例（数值手选可读——契约面非真源数值）。 */
function healthy(): Record<string, unknown> {
  return {
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "h1",
    engine_version: "e1",
    data_version: "d1",
    kb_injected: null,
    validation_available: true,
    conditions: ["avg", "design"],
    nodes: [{ node_id: "municipal_aao", faces: [] }],
    warnings: [
      {
        code: "kb.influent.bod_band",
        param_key: "bod",
        scope: "plant",
        message: "进水 BOD 300 超出建议带 [80, 250]",
        condition_keys: [],
        severity: "WARN",
      },
    ],
  };
}

/** 聚合行夹具工厂。 */
function row(
  code: string,
  scope: string,
  condition_keys: string[],
  severity: AggregatedWarningRow["severity"] = "WARN",
): AggregatedWarningRow {
  return {
    code,
    param_key: "ns",
    scope,
    message: `消息 ${code}`,
    condition_keys,
    severity,
  };
}

describe("narrowValidationObservation", () => {
  it("健康样例透传全字段（kb_injected=null 合法）", () => {
    const report = narrowValidationObservation(healthy()) as ValidationObservation;
    expect(report.project_id).toBe("p1");
    expect(report.validation_available).toBe(true);
    expect(report.kb_injected).toBeNull();
    expect(report.warnings).toHaveLength(1);
    expect(report.conditions).toEqual(["avg", "design"]);
  });

  it("顶层缺键拒（消息含键名）", () => {
    const bad = healthy();
    delete bad["validation_available"];
    expect(() => narrowValidationObservation(bad)).toThrow(ValidationViewError);
    expect(() => narrowValidationObservation(bad)).toThrow("validation_available");
  });

  it("顶层非对象拒/溯源字符串拒/布尔键拒/kb_injected 三态外拒", () => {
    expect(() => narrowValidationObservation(null)).toThrow(ValidationViewError);
    const badStr = healthy();
    badStr["engine_version"] = 7;
    expect(() => narrowValidationObservation(badStr)).toThrow("engine_version");
    const badFlag = healthy();
    badFlag["stale"] = "yes";
    expect(() => narrowValidationObservation(badFlag)).toThrow("stale");
    const badKb = healthy();
    badKb["kb_injected"] = "unknown";
    expect(() => narrowValidationObservation(badKb)).toThrow("kb_injected");
    const kbTrue = healthy();
    kbTrue["kb_injected"] = true;
    expect(narrowValidationObservation(kbTrue).kb_injected).toBe(true);
  });

  it("conditions 非字符串数组拒/nodes 非数组拒/warnings 非数组拒", () => {
    const badCond = healthy();
    badCond["conditions"] = ["avg", 3];
    expect(() => narrowValidationObservation(badCond)).toThrow("conditions");
    const badNodes = healthy();
    badNodes["nodes"] = {};
    expect(() => narrowValidationObservation(badNodes)).toThrow("nodes");
    const badWarn = healthy();
    badWarn["warnings"] = null;
    expect(() => narrowValidationObservation(badWarn)).toThrow("warnings");
  });

  it("warnings 行键域非法拒（缺 scope/condition_keys 非数组/severity 域外）", () => {
    const badScope = healthy();
    badScope["warnings"] = [
      { code: "c", param_key: "p", message: "m", condition_keys: [], severity: "WARN" },
    ];
    expect(() => narrowValidationObservation(badScope)).toThrow("warnings[0]");
    const badKeys = healthy();
    badKeys["warnings"] = [
      { code: "c", param_key: "p", scope: "plant", message: "m", condition_keys: "design", severity: "WARN" },
    ];
    expect(() => narrowValidationObservation(badKeys)).toThrow("warnings[0]");
    const badSeverity = healthy();
    badSeverity["warnings"] = [
      { code: "c", param_key: "p", scope: "plant", message: "m", condition_keys: [], severity: "FATAL" },
    ];
    expect(() => narrowValidationObservation(badSeverity)).toThrow("warnings[0]");
    const badMember = healthy();
    badMember["warnings"] = [
      { code: "c", param_key: "p", scope: "plant", message: "m", condition_keys: ["design", 2], severity: "INFO" },
    ];
    expect(() => narrowValidationObservation(badMember)).toThrow("warnings[0]");
  });
});

describe("partitionWarnings 三分区（§3 判据）", () => {
  it("∅ 哨兵→声明级；命中 ≥2→工况聚合；单工况→直通（位次在聚合区后）", () => {
    const zones = partitionWarnings([
      row("kb.a", "plant", []),
      row("kb.b", "municipal_aao", ["avg", "design"]),
      row("kb.c", "municipal_cass", ["design"]),
    ]);
    expect(zones.declaration.map((item) => item.code)).toEqual(["kb.a"]);
    expect(zones.aggregated.map((item) => item.code)).toEqual(["kb.b"]);
    expect(zones.single.map((item) => item.code)).toEqual(["kb.c"]);
  });

  it("区内序=服务端 (scope,code,param_key) 冻结序稳定过滤（零重排）", () => {
    const zones = partitionWarnings([
      row("kb.z", "plant", []),
      row("kb.a", "plant", []),
      row("kb.m", "n2", ["avg", "design", "s1"]),
      row("kb.b", "n1", ["avg", "design"]),
    ]);
    expect(zones.declaration.map((item) => item.code)).toEqual(["kb.z", "kb.a"]);
    expect(zones.aggregated.map((item) => item.code)).toEqual(["kb.m", "kb.b"]);
  });

  it("空 warnings=三分区全空（呈现面区块整体不渲染）", () => {
    const zones = partitionWarnings([]);
    expect(zones).toEqual({ declaration: [], aggregated: [], single: [] });
  });
});

describe("语义色与标签词典", () => {
  it("severityTone：ERROR=--wp-error/WARN=--wpv4-warn/INFO=次级灰", () => {
    expect(severityTone("ERROR").color).toBe("var(--wp-error)");
    expect(severityTone("WARN").color).toBe("var(--wpv4-warn)");
    expect(severityTone("INFO").color).toBe("var(--wp-text-2)");
    expect(severityTone("WARN").background).toContain("wpv4-warn-bg");
  });

  it("severityLabel：错误/警告/提示（域值不进正文）", () => {
    expect(severityLabel("ERROR")).toBe("错误");
    expect(severityLabel("WARN")).toBe("警告");
    expect(severityLabel("INFO")).toBe("提示");
  });

  it("scopeLabel：plant=全厂、节点 ID 原样（影响面轴 §1）", () => {
    expect(scopeLabel("plant")).toBe("全厂");
    expect(scopeLabel("municipal_aao")).toBe("municipal_aao");
  });

  it("conditionKeysText：∅=空串/单键直书/多键=清单+计数", () => {
    expect(conditionKeysText([])).toBe("");
    expect(conditionKeysText(["design"])).toBe("工况 design");
    expect(conditionKeysText(["avg", "design", "s1"])).toBe(
      "工况 avg、design、s1（3）",
    );
  });
});
