/**
 * 批量任务恢复决策纯函数测试：resolveRestore 四分支+stillCurrent 覆盖
 * 核对+isNotFoundApiError 404 分类（SVRB2 D8——决策树从 effect 抽出
 * node 直测；R1/R5 审核必改项的分支面）。
 *
 * 输入:  StoredBatchTask 载荷+RestoreSnapshot 三态（status/notFound/
 *        unreachable）+重读值与错误对象
 * 输出:  fill/resume/drop/keep 四计划断言+覆盖核对布尔+404 分类边界断言
 */
import { describe, expect, it } from "vitest";

import { WaterprintApiError } from "../../../shared/api/http";
import { StoredBatchTask } from "./batchTaskStore";
import { isNotFoundApiError, resolveRestore, stillCurrent } from "./restoreDecision";

const STORED: StoredBatchTask = { taskId: "t-1", total: 3 };

describe("resolveRestore 决策四分支", () => {
  it("status+终态→fill（终态回填——不清恢复订阅）", () => {
    expect(
      resolveRestore(STORED, { kind: "status", terminal: true, status: { state: "done" } }),
    ).toEqual({ plan: "fill" });
  });

  it("status+非终态→resume（taskId/total 透传重订阅面）", () => {
    expect(
      resolveRestore(STORED, { kind: "status", terminal: false, status: { state: "running" } }),
    ).toEqual({
      plan: "resume",
      taskId: "t-1",
      total: 3,
    });
  });

  it("notFound→drop（服务端权威否定——清存储）", () => {
    expect(resolveRestore(STORED, { kind: "notFound" })).toEqual({ plan: "drop" });
  });

  it("unreachable→keep（网络异常非否定——保留存储待下次挂载重试）", () => {
    expect(resolveRestore(STORED, { kind: "unreachable" })).toEqual({ plan: "keep" });
  });
});

describe("stillCurrent 覆盖核对（R5——异步窗口防旧任务污染新提交）", () => {
  it("重读值同 taskId→true（恢复可继续）", () => {
    expect(stillCurrent({ taskId: "t-1", total: 3 }, "t-1")).toBe(true);
  });

  it("重读值异 taskId（已被新提交覆盖）→false（静默放弃恢复）", () => {
    expect(stillCurrent({ taskId: "t-new", total: 5 }, "t-1")).toBe(false);
  });

  it("重读值 null（已被终态清除）→false", () => {
    expect(stillCurrent(null, "t-1")).toBe(false);
  });
});

describe("isNotFoundApiError 404 分类", () => {
  it("UnknownTaskError（服务端 error_type 面）→true", () => {
    expect(isNotFoundApiError(new WaterprintApiError("UnknownTaskError", "任务不存在"))).toBe(true);
  });

  it("HTTP_404（无 error_type 兜底面）→true", () => {
    expect(isNotFoundApiError(new WaterprintApiError("HTTP_404", "not found"))).toBe(true);
  });

  it("其余 API 错误码（HTTP_500 等）→false", () => {
    expect(isNotFoundApiError(new WaterprintApiError("HTTP_500", "server error"))).toBe(false);
  });

  it("非 WaterprintApiError（普通 Error/字符串）→false", () => {
    expect(isNotFoundApiError(new Error("network down"))).toBe(false);
    expect(isNotFoundApiError("HTTP_404")).toBe(false);
  });
});
