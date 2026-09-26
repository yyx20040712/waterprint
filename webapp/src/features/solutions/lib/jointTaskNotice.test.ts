/**
 * jointTaskNotice node 测试（批6f——批2d 欠账②：终态文案分派）。
 *
 * 输入:  jointTaskNotice（TaskStatus 快照弱形态——state/error/error_type 注入）
 * 输出:  断言：三终态各就位（done null/failed 明细组合/cancelled 独立文案）
 *        +非终态进度口径维持+畸形宽容（非对象态=进度兜底——归一 unknown 态）
 */
import { describe, expect, it } from "vitest";

import { jointTaskNotice } from "./jointTaskNotice";

function status(state: string, extra: Record<string, unknown> = {}) {
  return {
    task_id: "t1",
    kind: "joint_enumerate",
    state,
    progress: 0.5,
    stage: "run",
    condition_key: null,
    stale: false,
    ...extra,
  };
}

describe("jointTaskNotice（批6f 终态文案分派）", () => {
  it("done → null（结果面由调用方挂载，无提示段）", () => {
    expect(jointTaskNotice(status("done"))).toBeNull();
  });

  it("failed → danger 段+error_type 中文前缀+error 明细组合（快照单源）", () => {
    const notice = jointTaskNotice(
      status("failed", {
        error: "InvalidNodeError: 单元 aao_1 缺少必填参数 n_pool",
        error_type: "InvalidNodeError",
      }),
    );
    expect(notice?.kind).toBe("failed");
    expect(notice?.text).toContain("联合枚举任务失败：");
    expect(notice?.text).toContain("单元数据无效（InvalidNodeError）");
    expect(notice?.text).toContain("单元 aao_1 缺少必填参数 n_pool");
    expect(notice?.text).toContain("可重新提交");
  });

  it("failed 无明细字段 → 失败详情缺失占位（非空串——横幅恒有内容）", () => {
    const notice = jointTaskNotice(status("failed"));
    expect(notice?.kind).toBe("failed");
    expect(notice?.text).toContain("失败详情缺失");
  });

  it("failed 明细空白残骸（空串视同缺席——d1-W1/k1-N1 回炉源面）→ 占位不悬空", () => {
    const empty = jointTaskNotice(status("failed", { error: "", error_type: "" }));
    expect(empty?.text).toContain("失败详情缺失");
    expect(empty?.text).not.toContain("失败：：");
    expect(empty?.text).toBe(
      "联合枚举任务失败：失败详情缺失（error/error_type 均空）——可重新提交。",
    );
  });

  it("failed 未登记 error_type → 原样透传不吞键（InterruptedByRestart 重启中断面）", () => {
    const notice = jointTaskNotice(
      status("failed", {
        error: "InterruptedByRestart: 服务重启中断",
        error_type: "InterruptedByRestart",
      }),
    );
    expect(notice?.text).toContain("InterruptedByRestart");
    expect(notice?.text).toContain("服务重启中断");
  });

  it("cancelled → 独立取消文案（非「进行中」幽灵、非「失败」误称）", () => {
    const notice = jointTaskNotice(status("cancelled"));
    expect(notice?.kind).toBe("cancelled");
    expect(notice?.text).toBe("联合枚举任务已取消——可重新提交。");
    expect(notice?.text).not.toContain("进行中");
    expect(notice?.text).not.toContain("失败");
  });

  it("queued/running → 进度口径维持（批2d 存量文案）", () => {
    for (const state of ["queued", "running"]) {
      const notice = jointTaskNotice(status(state));
      expect(notice?.kind).toBe("progress");
      expect(notice?.text).toBe(
        "联合枚举任务进行中——结果将在完成后呈现（进度见上方任务面板）。",
      );
    }
  });

  it("非对象/畸形载荷 → 进度兜底（unknown 态不猜终局）", () => {
    expect(jointTaskNotice(null)?.kind).toBe("progress");
    expect(jointTaskNotice("x")?.kind).toBe("progress");
    expect(jointTaskNotice({})?.kind).toBe("progress");
  });
});
