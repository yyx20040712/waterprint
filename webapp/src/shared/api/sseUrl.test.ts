/**
 * SSE 订阅 URL 单源测试（B6 D8：自 useExportBatch 迁入+补强；联机第六批
 * 2026-11-19 增客户端模式远程 origin 前拼面）。
 *
 * 输入:  buildTaskStreamUrl（shared/api/sseUrl——纯函数，node 直测；远程
 *        档案经 vi.stubGlobal localStorage 受控）
 * 输出:  路径段编码/token 空零查询参/非空 ？token= 编码/客户端模式远程
 *        origin 前拼四组断言
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { buildTaskStreamUrl } from "./sseUrl";

afterEach(() => {
  vi.unstubAllGlobals();
});

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

  it("客户端模式：远程档案在场 → SSE URL 前拼远程 origin（联机第六批）", () => {
    vi.stubGlobal("localStorage", {
      getItem: (key: string) =>
        key === "waterprint.remote_server"
          ? JSON.stringify({ base_url: "http://127.0.0.1:8100" })
          : null,
      setItem: () => {},
      removeItem: () => {},
    });
    expect(buildTaskStreamUrl("t1", "tok")).toBe(
      "http://127.0.0.1:8100/api/events/tasks/t1?token=tok",
    );
  });

  it("本地模式：档案缺席 → 同源 URL 零前拼（零行为变回归锚）", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
    });
    expect(buildTaskStreamUrl("t1", null)).toBe("/api/events/tasks/t1");
  });
});
