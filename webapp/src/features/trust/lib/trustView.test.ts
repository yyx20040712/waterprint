/**
 * 投影层纯函数测试：trust 响应窄化门+语义色/格式化对照（node 环境）。
 *
 * 输入:  trustView 纯函数（node 环境——零 antd import；P2 次批 ADR-012
 *        ——estimateView.test 同构先例）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/裕度语义色正绿负红/
 *        残差与流量格式化/中文标签词典）
 */
import { describe, expect, it } from "vitest";

import {
  TrustViewError,
  fluidLabel,
  formatFlow,
  formatRel,
  formatSci,
  loopParamLabel,
  marginText,
  marginTone,
  narrowTrustResponse,
  severityTone,
  type TrustReport,
} from "./trustView";

/** 全字段健康样例（数值手选可读——契约面非真源数值）。 */
function healthy(): Record<string, unknown> {
  return {
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "h1",
    engine_version: "e1",
    data_version: "d1",
    diagnostics_available: true,
    loop_params: { "loop.tolerance": 1e-10 },
    convergence: [
      { condition_key: "design", loop_nodes: ["a", "b"], iterations: 5, final_residual: 1e-11 },
    ],
    mass_balance: [
      {
        condition_key: "design",
        lines: [{ fluid: "WATER", q_sources_total: 0.5, q_sinks_total: 0.5, closure_rel: 0 }],
        unit_imbalances: [
          { unit_id: "u1", fluid: "WATER", q_in: 0.5, q_out: 0.5, delta_rel: 0 },
        ],
      },
    ],
    effluent: [
      {
        condition_key: "design",
        standard_id: "gb18918.level_a",
        indicator: "BOD5",
        value: 7,
        limit: 10,
        margin: 0.3,
      },
    ],
    warnings: [
      {
        unit_id: "u1",
        severity: "WARN",
        source: "factor.aao.ns_band",
        message: "超出建议带",
        param_key: "ns",
        condition_key: "design",
        affected_unit_ids: [],
      },
    ],
    warning_counts: { WARN: 1 },
  };
}

describe("narrowTrustResponse", () => {
  it("健康样例透传全字段", () => {
    const report = narrowTrustResponse(healthy()) as TrustReport;
    expect(report.project_id).toBe("p1");
    expect(report.convergence).toHaveLength(1);
    expect(report.effluent[0]?.margin).toBeCloseTo(0.3);
  });

  it("顶层缺键拒（消息含键名）", () => {
    const bad = healthy();
    delete bad["warning_counts"];
    expect(() => narrowTrustResponse(bad)).toThrow(TrustViewError);
    expect(() => narrowTrustResponse(bad)).toThrow("warning_counts");
  });

  it("顶层非对象拒/诊断布尔拒/convergence 非数组拒", () => {
    expect(() => narrowTrustResponse(null)).toThrow(TrustViewError);
    const badFlag = healthy();
    badFlag["diagnostics_available"] = "yes";
    expect(() => narrowTrustResponse(badFlag)).toThrow("diagnostics_available");
    const badConv = healthy();
    badConv["convergence"] = {};
    expect(() => narrowTrustResponse(badConv)).toThrow("convergence");
  });

  it("条目族键域非法拒（effluent 缺 margin/warnings 条目缺 unit_id）", () => {
    const bad = healthy();
    bad["effluent"] = [{ condition_key: "design", standard_id: "s", indicator: "BOD5", value: 1, limit: 10 }];
    expect(() => narrowTrustResponse(bad)).toThrow("effluent[0]");
    const badWarn = healthy();
    badWarn["warnings"] = [{ severity: "WARN", source: "s", message: "m", param_key: null, condition_key: null, affected_unit_ids: [] }];
    expect(() => narrowTrustResponse(badWarn)).toThrow("warnings[0]");
  });
});

describe("语义色与格式化", () => {
  it("marginTone：0/正=ok，负=over（SolutionsTable 同纪律）", () => {
    expect(marginTone(0)).toBe("ok");
    expect(marginTone(0.3)).toBe("ok");
    expect(marginTone(-0.05)).toBe("over");
  });

  it("marginText：达标带正号、超限带负号（两位百分比）", () => {
    expect(marginText(0.3)).toBe("+30.00%");
    expect(marginText(-0.05)).toBe("-5.00%");
  });

  it("severityTone：ERROR/WARN/INFO 三映射（PumpStationsPanel 同款）", () => {
    expect(severityTone("ERROR")).toBe("error");
    expect(severityTone("WARN")).toBe("warning");
    expect(severityTone("INFO")).toBe("info");
  });

  it("formatSci/formatFlow：科学计数三位尾/流量四位小数", () => {
    expect(formatSci(1e-11)).toBe("1.000e-11");
    expect(formatFlow(0.40232)).toBe("0.4023");
  });

  it("formatRel：零=0.00%、微差=<0.01%、常规两位百分比", () => {
    expect(formatRel(0)).toBe("0.00%");
    expect(formatRel(5e-6)).toBe("<0.01%");
    expect(formatRel(0.0123)).toBe("1.23%");
  });

  it("fluidLabel/loopParamLabel：中文标签词典（字段 ID 不进正文）", () => {
    expect(fluidLabel("WATER")).toBe("水线");
    expect(fluidLabel("SLUDGE")).toBe("泥线");
    expect(loopParamLabel("loop.tolerance")).toBe("收敛容差");
    expect(loopParamLabel("loop.max_iterations")).toBe("迭代上限");
    expect(loopParamLabel("loop.damping")).toBe("阻尼系数");
    expect(loopParamLabel("unknown")).toBe("unknown");
  });
});
