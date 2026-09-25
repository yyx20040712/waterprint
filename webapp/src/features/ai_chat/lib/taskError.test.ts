/**
 * 聊天失败轮错误摘要测试（F2 C-5——终态 failed 横幅明细补查）。
 *
 * 输入:  任务状态端点桩（vi.mock generated 单函数注入——TaskStatus 形态）
 * 输出:  error 摘要截断（前 120 字）+横幅文案单源（摘要在场/回落两态）
 *        +补查失败回落（横幅仍在场——非静默吞错）
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const statusStub = vi.hoisted(() => ({ fetchTask: vi.fn() }));
vi.mock("../../../shared/api/generated", () => ({
  getTaskStatusApiCalcTasksTaskIdGet: statusStub.fetchTask,
}));

import {
  FAILED_TURN_FALLBACK_TEXT,
  TASK_ERROR_SUMMARY_MAX,
  failedTurnBannerText,
  fetchTaskErrorSummary,
  truncateTaskErrorSummary,
} from "./taskError";

/** 任务状态快照桩（error 字段可注入——其余字段取终态形）。 */
const statusStubPayload = (error: string | null) => ({
  state: "failed",
  error,
  error_code: null,
  error_type: "InvalidNodeError",
  kind: "calc",
  progress: 100,
  result: {},
  stage: "run",
  stale: false,
  task_id: "task-k",
  condition_key: null,
});

describe("failed 横幅错误摘要（C-5——mock 任务状态含 error）", () => {
  beforeEach(() => {
    statusStub.fetchTask.mockReset();
  });

  it("任务状态含 error 摘要 → 横幅文案含摘要（前 120 字截断）", async () => {
    const long = "E".repeat(TASK_ERROR_SUMMARY_MAX + 30);
    statusStub.fetchTask.mockResolvedValue(statusStubPayload(long));
    const summary = await fetchTaskErrorSummary("task-k");
    expect(summary).toBe("E".repeat(TASK_ERROR_SUMMARY_MAX)); // 截断=前 120 字
    expect(failedTurnBannerText(summary)).toBe(
      `本轮失败（failed）：${"E".repeat(TASK_ERROR_SUMMARY_MAX)}`,
    );
  });

  it("常规 error 文本整段入横幅（invalid 参数场景）", async () => {
    statusStub.fetchTask.mockResolvedValue(
      statusStubPayload("InvalidNodeError: municipal_input 缺必需参数 ['kz','q_avg_daily']"),
    );
    const text = failedTurnBannerText(await fetchTaskErrorSummary("task-k"));
    expect(text).toContain("本轮失败（failed）：InvalidNodeError");
    expect(text).toContain("kz");
  });

  it("无 error 字段（null）→ 回落通用横幅（明确文案态）", async () => {
    statusStub.fetchTask.mockResolvedValue(statusStubPayload(null));
    expect(await fetchTaskErrorSummary("task-k")).toBeNull();
    expect(failedTurnBannerText(null)).toBe(FAILED_TURN_FALLBACK_TEXT);
  });

  it("补查失败（任务状态端点不可达）→ 回落通用横幅（横幅仍在场）", async () => {
    statusStub.fetchTask.mockRejectedValue(new Error("HTTP_502"));
    expect(await fetchTaskErrorSummary("task-k")).toBeNull();
    expect(failedTurnBannerText(null)).toContain("输入已解锁");
  });

  it("截断边界：恰 120 字不截", () => {
    expect(truncateTaskErrorSummary("x".repeat(TASK_ERROR_SUMMARY_MAX))).toHaveLength(
      TASK_ERROR_SUMMARY_MAX,
    );
  });
});
