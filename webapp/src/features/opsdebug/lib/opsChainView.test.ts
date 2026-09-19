/**
 * 投影层纯函数测试：opsChain 响应窄化门+状态语义色/格式化对照（node 环境）。
 *
 * 输入:  opsChainView 纯函数（node 环境——零 antd import；B4-1 实现批
 *        ——trustView.test 同构先例）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/任务状态语义色/任务类
 *        中文标签/时刻与残差格式化）
 */
import { describe, expect, it } from "vitest";

import {
  OpsChainViewError,
  formatProgress,
  formatSci,
  formatUnix,
  kindLabel,
  narrowOpsChainResponse,
  stateTone,
} from "./opsChainView";

/** 全字段健康样例（数值手选可读——契约面非真源数值）。 */
function healthy(): Record<string, unknown> {
  return {
    project_id: "p1",
    tasks: [
      {
        task_id: "t1",
        kind: "calc",
        state: "done",
        progress: 1.0,
        stage: "serialize",
        condition_key: null,
        stale: false,
        error: null,
        error_type: null,
        error_code: null,
        snapshot_hash: "abc",
        finished_at_unix: 1758249600.5,
        result: { result_file: "calc-t1.json" },
      },
      {
        task_id: "t2",
        kind: "export_batch",
        state: "failed",
        progress: 0.5,
        stage: "export:dxf:u1",
        condition_key: "design",
        stale: true,
        error: "boom",
        error_type: "RuntimeError",
        error_code: null,
        snapshot_hash: null,
        finished_at_unix: null,
        result: null,
      },
    ],
    latest_calc: {
      task_id: "t1",
      stale: false,
      design_hash: "h1",
      engine_version: "e1",
      data_version: "d1",
      diagnostics: {
        diagnostics_available: true,
        convergence_lines: 2,
        max_iterations: 12,
        worst_final_residual: 1e-11,
        mass_balance_lines: 2,
        effluent_lines: 6,
      },
      warning_counts: { ERROR: 1, WARN: 2 },
      trace: {
        total_nodes: 120,
        by_condition: { design: 60, avg: 60 },
        by_unit: { aao: 40, cugeshan: 80 },
        by_formula: { "GM-F12": 120 },
      },
    },
  };
}

describe("narrowOpsChainResponse 窄化门", () => {
  it("健康样例过门（latest_calc 全块）", () => {
    const report = narrowOpsChainResponse(healthy());
    expect(report.project_id).toBe("p1");
    expect(report.tasks).toHaveLength(2);
    expect(report.latest_calc?.trace.total_nodes).toBe(120);
  });

  it("latest_calc=null 空块过门（无 done calc 降级面）", () => {
    const raw = healthy();
    raw.latest_calc = null;
    const report = narrowOpsChainResponse(raw);
    expect(report.latest_calc).toBeNull();
  });

  it("顶层缺键拒（带键定位）", () => {
    const raw = healthy();
    delete raw.tasks;
    expect(() => narrowOpsChainResponse(raw)).toThrow(OpsChainViewError);
    expect(() => narrowOpsChainResponse(raw)).toThrow("tasks");
  });

  it("任务条目缺键拒（带条目定位）", () => {
    const raw = healthy();
    const tasks = raw.tasks as Record<string, unknown>[];
    delete tasks[0]!.finished_at_unix;
    expect(() => narrowOpsChainResponse(raw)).toThrow("tasks[0]");
  });

  it("任务条目键域类型非法拒", () => {
    const raw = healthy();
    (raw.tasks as { progress: unknown }[])[0]!.progress = "fast";
    expect(() => narrowOpsChainResponse(raw)).toThrow(OpsChainViewError);
  });

  it("latest_calc 聚合块缺 diagnostics 子键拒", () => {
    const raw = healthy();
    const latest = raw.latest_calc as { diagnostics: Record<string, unknown> };
    delete latest.diagnostics.worst_final_residual;
    expect(() => narrowOpsChainResponse(raw)).toThrow("worst_final_residual");
  });

  it("latest_calc trace 子块缺桶拒", () => {
    const raw = healthy();
    const latest = raw.latest_calc as { trace: Record<string, unknown> };
    delete latest.trace.by_formula;
    expect(() => narrowOpsChainResponse(raw)).toThrow("by_formula");
  });

  it("非对象顶层拒", () => {
    expect(() => narrowOpsChainResponse("nope")).toThrow(OpsChainViewError);
  });
});

describe("状态语义与格式化", () => {
  it("任务状态语义色（done 绿/failed 红/cancelled 灰/进行态蓝）", () => {
    expect(stateTone("done")).toBe("green");
    expect(stateTone("failed")).toBe("red");
    expect(stateTone("cancelled")).toBe("default");
    expect(stateTone("running")).toBe("processing");
  });

  it("任务类中文标签", () => {
    expect(kindLabel("calc")).toBe("全厂计算");
    expect(kindLabel("enumerate")).toBe("方案枚举");
    expect(kindLabel("export_batch")).toBe("批量导出");
  });

  it("完成时刻格式化（null=占位/数值=本地时刻串）", () => {
    expect(formatUnix(null)).toBe("—");
    expect(formatUnix(1758249600.5)).toContain("2025");
  });

  it("残差科学计数+进度百分比", () => {
    expect(formatSci(1e-11)).toBe("1.000e-11");
    expect(formatProgress(0.4567)).toBe("46%");
  });
});
