/**
 * assumptionLabels 测试（C2-ALIGN A5r）：22 键全覆盖+fail-open 回退。
 *
 * 输入: 无（字典自证）
 * 输出: vitest 断言组（registry 键面镜像——core 增键未入字典即红）
 */
import { describe, expect, it } from "vitest";

import { ASSUMPTION_KEYS, assumptionLabel } from "./assumptionLabels";

/** registry 22 键全集镜像（core/registry DEFAULT_ASSUMPTIONS 键面）。 */
const REGISTRY_KEYS = [
  "safety.superheight",
  "loop.tolerance",
  "loop.max_iterations",
  "loop.damping",
  "solution.grid.base_per_dim",
  "elevation.wall_thickness",
  "elevation.bury_depth.max",
  "elevation.drop_threshold",
  "elevation.losses.friction_lambda",
  "elevation.losses.gravity",
  "elevation.losses.weir_coefficient",
  "elevation.losses.orifice_coefficient",
  "elevation.pump.pipe_length",
  "elevation.pump.pipe_diameter",
  "geometry.pool.spacing",
  "network.solve.tolerance",
  "network.solve.max_iterations",
  "network.solve.depth_min",
  "network.solve.depth_max",
  "network.excel.max_rows",
  "network.excel.max_file_bytes",
  "solution.design_map.max_points",
] as const;

describe("assumptionLabel（假设中文物理意义标签）", () => {
  it("registry 22 键全覆盖（镜像——core 增键未入字典即红）", () => {
    expect([...ASSUMPTION_KEYS].sort()).toEqual([...REGISTRY_KEYS].sort());
    for (const key of REGISTRY_KEYS) {
      // 词条=非空中文且不等于 key 原文（防占位假词条）
      const label = assumptionLabel(key);
      expect(label, key).not.toBe(key);
      expect(label.length, key).toBeGreaterThan(1);
    }
  });

  it("未知键 fail-open 回退 key 原文（可见性保底）", () => {
    expect(assumptionLabel("future.unknown")).toBe("future.unknown");
    expect(assumptionLabel("")).toBe("");
  });
});
