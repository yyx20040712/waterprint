/**
 * 观测投影层纯函数测试：validation 响应窄化门+降级态判定+格式化对照
 * （node 环境——零 antd import；2A1 消费批，trustView.test 同构先例）。
 *
 * 输入:  maintenanceView 纯函数（窄化门/降级判定/故障灯/格式化）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/kb_injected null 三态/
 *        降级三态判定/节点故障灯/ratio·fixgeom 文案）
 */
import { describe, expect, it } from "vitest";

import {
  MaintenanceViewError,
  formatFixgeom,
  formatRatio,
  narrowValidationObservation,
  nodeFailed,
  observationDegradation,
  type ValidationObservation,
} from "./maintenanceView";

/** 全字段健康样例（数值手选可读——契约面非真源数值）。 */
function healthy(): Record<string, unknown> {
  return {
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "h1",
    engine_version: "e1",
    data_version: "d1",
    kb_injected: true,
    validation_available: true,
    conditions: ["design", "avg", "design_offline_municipal_aao"],
    nodes: [
      {
        node_id: "municipal_aao",
        faces: [
          {
            condition_key: "design_offline_municipal_aao",
            kb: { "param.n.positive": true, "param.h2.positive": false },
            any_fail: true,
            ratio: { n: 2.0 },
            fixgeom_min: -1.0,
          },
        ],
      },
    ],
    warnings: [
      {
        code: "kb.param.h2.positive",
        param_key: "h2",
        scope: "municipal_aao",
        message: "kb 越门：param.h2.positive——h2=0.0 违反 h2 > 0",
        condition_keys: ["design_offline_municipal_aao"],
        severity: "WARN",
      },
    ],
  };
}

describe("narrowValidationObservation", () => {
  it("健康样例通过（顶层 11 键+条目键域）", () => {
    const observation = narrowValidationObservation(healthy());
    expect(observation.nodes[0]?.faces[0]?.kb).toEqual({
      "param.n.positive": true,
      "param.h2.positive": false,
    });
  });

  it("顶层缺键拒（带键定位）", () => {
    const sample = healthy() as Record<string, unknown>;
    delete sample.validation_available;
    expect(() => narrowValidationObservation(sample)).toThrow(MaintenanceViewError);
    expect(() => narrowValidationObservation(sample)).toThrow(
      "顶层缺 validation_available",
    );
  });

  it("kb_injected null 三态合法（diag 缺席不可知——禁伪造 False）", () => {
    const sample = healthy();
    sample.kb_injected = null;
    expect(narrowValidationObservation(sample).kb_injected).toBeNull();
    sample.kb_injected = "yes";
    expect(() => narrowValidationObservation(sample)).toThrow(
      "kb_injected 非布尔/null",
    );
  });

  it("faces 键域非法拒（fixgeom_min null 合法/kb 值非布尔拒）", () => {
    const sample = healthy();
    (sample.nodes as unknown[])[0] = {
      node_id: "x",
      faces: [
        { condition_key: "c", kb: {}, any_fail: false, ratio: {}, fixgeom_min: null },
      ],
    };
    expect(
      narrowValidationObservation(sample).nodes[0]?.faces[0]?.fixgeom_min,
    ).toBeNull();
    (sample.nodes as unknown[])[0] = {
      node_id: "x",
      faces: [
        { condition_key: "c", kb: { k: 1 }, any_fail: false, ratio: {}, fixgeom_min: 0 },
      ],
    };
    expect(() => narrowValidationObservation(sample)).toThrow(
      "nodes[0].faces[0] 键域非法",
    );
  });

  it("warnings 行键域非法拒（六键+condition_keys 字符串数组）", () => {
    const sample = healthy();
    (sample.warnings as unknown[])[0] = {
      code: "kb.x", param_key: "n", message: "m", severity: "WARN",
      condition_keys: ["c"],
    };
    expect(() => narrowValidationObservation(sample)).toThrow(
      "warnings[0] 键域非法",
    );
    (sample.warnings as unknown[])[0] = {
      code: "kb.x", param_key: "n", scope: "plant", message: "m",
      severity: "WARN", condition_keys: [7],
    };
    expect(() => narrowValidationObservation(sample)).toThrow(
      "warnings[0] 键域非法",
    );
  });

  it("顶层非对象拒", () => {
    expect(() => narrowValidationObservation([])).toThrow("顶层非对象");
  });

  it("条目 null 收编为 MaintenanceViewError（回炉 d1-N5——非原生 TypeError）", () => {
    const nodeNull = healthy();
    (nodeNull.nodes as unknown[])[0] = null;
    expect(() => narrowValidationObservation(nodeNull)).toThrow(
      MaintenanceViewError,
    );
    expect(() => narrowValidationObservation(nodeNull)).toThrow(
      "nodes[0] 非对象",
    );
    const warnNull = healthy();
    (warnNull.warnings as unknown[])[0] = null;
    expect(() => narrowValidationObservation(warnNull)).toThrow(
      "warnings[0] 非对象",
    );
    const faceNull = healthy();
    ((faceNull.nodes as { faces: unknown[] }[])[0]!.faces as unknown[])[0] =
      null;
    expect(() => narrowValidationObservation(faceNull)).toThrow(
      "faces[0] 非对象",
    );
  });
});

describe("observationDegradation", () => {
  it("健康态四降级全 false", () => {
    const state = observationDegradation(
      narrowValidationObservation(healthy()) as ValidationObservation,
    );
    expect(state).toEqual({
      kbMissing: false,
      kbUnknown: false,
      valMissing: false,
      noObservableFaces: false,
    });
  });

  it("kb 未注入/kb 不可知/val 缺席/空观测四态各自成立", () => {
    const kbMissingSample = healthy();
    kbMissingSample.kb_injected = false;
    expect(
      observationDegradation(narrowValidationObservation(kbMissingSample)).kbMissing,
    ).toBe(true);
    const kbUnknownSample = healthy();
    kbUnknownSample.kb_injected = null;
    expect(
      observationDegradation(narrowValidationObservation(kbUnknownSample)).kbUnknown,
    ).toBe(true);
    const valMissingSample = healthy();
    valMissingSample.validation_available = false;
    expect(
      observationDegradation(narrowValidationObservation(valMissingSample)).valMissing,
    ).toBe(true);
    const emptySample = healthy();
    emptySample.nodes = [];
    expect(
      observationDegradation(narrowValidationObservation(emptySample)).noObservableFaces,
    ).toBe(true);
  });
});

describe("nodeFailed", () => {
  it("任一工况 any_fail 即故障灯亮", () => {
    const observation = narrowValidationObservation(healthy());
    expect(observation.nodes[0] && nodeFailed(observation.nodes[0])).toBe(true);
    const calm = healthy();
    (calm.nodes as { faces: { any_fail: boolean }[] }[])[0]!.faces[0]!.any_fail =
      false;
    const calmObservation = narrowValidationObservation(calm);
    expect(
      calmObservation.nodes[0] && nodeFailed(calmObservation.nodes[0]),
    ).toBe(false);
  });
});

describe("格式化", () => {
  it("ratio=×N 三位小数；fixgeom=两位小数（负号 ASCII）", () => {
    expect(formatRatio(2.0)).toBe("×2.000");
    expect(formatRatio(0.3333333)).toBe("×0.333");
    expect(formatFixgeom(-1.0)).toBe("-1.00");
    expect(formatFixgeom(0.125)).toBe("0.13");
  });
});
