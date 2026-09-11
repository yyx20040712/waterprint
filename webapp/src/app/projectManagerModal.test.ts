/**
 * projectManagerModal 纯函数面测试（P2 生命周期治理 L3）。
 *
 * 输入: formatTimestamp（ISO → 显示短式）
 * 输出: vitest 断言组（常规 ISO/短串直通两分支）
 *
 * 形态说明（app 层纯函数测试沿 projectCreate.test 先例；Modal 渲染/
 * 交互面[重命名/复制/删除点击链]归无头 E2E shoot_p2_lifecycle——antd
 * Modal 走 portal，SSR 渲染为空[零 jsdom 红线]，本件锁显示层变换）。
 */
import { describe, expect, it } from "vitest";

import { formatTimestamp } from "./projectManagerModal";

describe("formatTimestamp（项目表更新时间显示变换）", () => {
  it("常规 ISO：YYYY-MM-DDTHH:mm:… → 「YYYY-MM-DD HH:mm」", () => {
    expect(formatTimestamp("2026-09-12T08:30:00Z")).toBe("2026-09-12 08:30");
  });

  it("短串（≤16 字符）直通不变形", () => {
    expect(formatTimestamp("2026-09-12")).toBe("2026-09-12");
    expect(formatTimestamp("")).toBe("");
  });
});
