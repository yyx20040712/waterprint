/**
 * CheckedUnitsPanel 测试（2A4 回炉轮 1 R7——纯源文断言零渲染，沿
 * domainColorAxis.test 读源先例；渲染面零锚=UF-57 测试债族在案不随批扩）。
 *
 * 输入:  CheckedUnitsPanel.tsx 源文（读源断言——onError toast 码表门控
 *        装配面：domainGate 双码+锁冲突优先接线）
 * 输出:  断言两组：①UF-59 码表锚——两处 domainGate 调用与
 *        ProjectNotFoundError/InvalidProjectPayloadError 码串在场（码表
 *        依据=server projects.py PUT 链路领域码族）；②isLockConflict→
 *        LOCK_HINT 优先接线在场（409 锁冲突既有门零改锚）
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  new URL("./CheckedUnitsPanel.tsx", import.meta.url),
  "utf-8",
);

describe("CheckedUnitsPanel（onError toast 码表门控装配——源文断言）", () => {
  it("码表锚（UF-59）：两处 domainGate 调用+ProjectNotFoundError/InvalidProjectPayloadError 码串在场", () => {
    expect(source.match(/domainGate\(/g) ?? []).toHaveLength(2);
    expect(source).toContain('"ProjectNotFoundError"');
    expect(source).toContain('"InvalidProjectPayloadError"');
    expect(source).toContain("保存失败：项目不存在或已被删除——请刷新页面核对");
    expect(source).toContain("保存失败：项目数据校验未通过——项目可能已被他处修改，请刷新后重试");
  });

  it("锁冲突优先锚：isLockConflict 判定先于码表→LOCK_HINT 接线在场（既有 409 门零改）", () => {
    expect(source).toContain("isLockConflict(error)");
    expect(source).toContain("? LOCK_HINT");
    expect(source).toContain("工况校核保存失败：");
  });
});
