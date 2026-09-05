/**
 * SSE 订阅 URL 单源测试（B6 D8：自 useExportBatch 迁入+补强）。
 *
 * 输入:  buildTaskStreamUrl（shared/api/sseUrl——纯函数，node 直测）
 * 输出:  路径段编码/token 空零查询参/非空 ？token= 编码三面断言
 */
import { describe, expect, it } from "vitest";

import { buildTaskStreamUrl } from "./sseUrl";

describe("buildTaskStreamUrl（SSE URL 单源——B6 D8 迁入）", () => {
  it("token 空=零查询参；非空=?token= 编码（双通道）", () => {
    expect(buildTaskStreamUrl("t1", null)).toBe("/api/events/tasks/t1");
    expect(buildTaskStreamUrl("t 1", "a b")).toBe(
      "/api/events/tasks/t%201?token=a%20b",
    );
  });

  it("taskId 路径段编码（用户可控面——分隔符注入收口）", () => {
    expect(buildTaskStreamUrl("a/b", null)).toBe("/api/events/tasks/a%2Fb");
    expect(buildTaskStreamUrl("..", "tok")).toBe("/api/events/tasks/..?token=tok");
  });
});
