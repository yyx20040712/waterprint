/**
 * 批量导出任务 hook 测试：提交面（fetch stub）+任务面纯函数（node 环境）。
 *
 * 输入:  useExportBatch 导出面（submitExportBatch+四纯函数；hook 壳
 *        EventSource 生命周期=薄壳不测先例〔useTaskFeed 同款〕——node
 *        环境零 DOM 依赖红线）
 * 输出:  句柄 JSON 解析（修复「句柄误当 blob」现状缺陷）/错误归一/
 *        终态判定/事件解析/outcome 投影/进度派生/SSE URL 六面断言
 *        （SVRB D6②；先红后绿：module 未就绪=import 解析红）
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { WaterprintApiError } from "../../../shared/api/http";
import {
  batchStatusText,
  buildTaskStreamUrl,
  deriveBatchProgress,
  isTerminalTaskState,
  parseTaskEventData,
  submitExportBatch,
  toBatchOutcome,
} from "./useExportBatch";

afterEach(() => {
  vi.unstubAllGlobals();
});

/** fetch 替身类型（http.test.ts 同款——calls 索引面宽松形态）。 */
type FetchMock = ReturnType<typeof vi.fn>;

describe("submitExportBatch 提交面（customInstance POST——fetch stub）", () => {
  it("200 句柄 JSON → 取 task_id+单 body 形态（items 逐项 unit/工况）", async () => {
    const mock: FetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            project_id: "p1",
            kind: "dxf",
            condition_key: "design",
            path: "/exports/x.dxf",
            design_digest: "d0",
            stale_labeled: false,
            task_id: "t-batch-1",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", mock);
    const taskId = await submitExportBatch("dxf", {
      projectId: "p1",
      units: ["municipal_cass", "municipal_chenshachi"],
      conditionKey: "design",
    });
    expect(taskId).toBe("t-batch-1"); // 句柄 JSON 消费（非 blob——现状缺陷修复面）
    expect(mock.mock.calls[0]?.[0]).toBe("/api/exports/dxf");
    const init = mock.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual({
      project_id: "p1",
      condition_key: "design",
      options: {
        items: [
          { unit_id: "municipal_cass", condition_key: "design" },
          { unit_id: "municipal_chenshachi", condition_key: "design" },
        ],
      },
    });
  });

  it("非 2xx 统一错误体 → WaterprintApiError（code=error_type——customInstance 归一）", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              detail: "ifc 批量项 unit_id 须全一致（ifc 为模型级产物不分单元）",
              error_type: "InvalidExportRequestError",
            }),
            { status: 422 },
          ),
      ),
    );
    let caught: unknown = null;
    try {
      await submitExportBatch("ifc", {
        projectId: "p1",
        units: ["u1"],
        conditionKey: "design",
      });
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(WaterprintApiError);
    expect((caught as WaterprintApiError).code).toBe("InvalidExportRequestError");
  });
});

describe("任务面纯函数（SSE 消费/终态投影）", () => {
  it("isTerminalTaskState：done/cancelled/failed 真；queued/running 假", () => {
    expect(isTerminalTaskState("done")).toBe(true);
    expect(isTerminalTaskState("cancelled")).toBe(true);
    expect(isTerminalTaskState("failed")).toBe(true);
    expect(isTerminalTaskState("queued")).toBe(false);
    expect(isTerminalTaskState("running")).toBe(false);
  });

  it("parseTaskEventData：state/progress 两形解析+畸形/缺型拒 null", () => {
    expect(
      parseTaskEventData(
        '{"type":"state","task_id":"t","percent":1,"message":"done","condition_key":null}',
      ),
    ).toEqual({ type: "state", message: "done", percent: 1 });
    expect(
      parseTaskEventData(
        '{"type":"progress","task_id":"t","percent":0.5,"message":"export:dxf:u1","condition_key":"design"}',
      ),
    ).toEqual({ type: "progress", message: "export:dxf:u1", percent: 0.5 });
    expect(parseTaskEventData("not json")).toBeNull();
    expect(parseTaskEventData("[1,2]")).toBeNull();
    expect(parseTaskEventData('{"percent":0.5}')).toBeNull(); // 缺 type
  });

  it("toBatchOutcome：result 双清单透传+failed 面 error 承载+result null 兜底", () => {
    const failure = {
      index: 1,
      unit_id: "u2",
      condition_key: "bad",
      error: "ValueError: injected",
    };
    expect(
      toBatchOutcome({
        state: "cancelled",
        error: null,
        result: {
          state: "cancelled",
          files: ["/exports/a.dxf"],
          failures: [failure],
        },
      }),
    ).toEqual({
      state: "cancelled",
      files: ["/exports/a.dxf"],
      failures: [failure],
      error: null,
    });
    expect(
      toBatchOutcome({
        state: "failed",
        error: "RuntimeError: export_batch 全部 2 项失败——首错：boom",
        result: null,
      }),
    ).toEqual({
      state: "failed",
      files: [],
      failures: [],
      error: "RuntimeError: export_batch 全部 2 项失败——首错：boom",
    });
  });

  it("deriveBatchProgress：percent 幂商式还原序数+stage 文本化（unit 段·连接）", () => {
    expect(deriveBatchProgress(3 / 9, 8, "export:dxf:municipal_cass")).toEqual({
      done: 3,
      total: 8,
      stageText: "dxf·municipal_cass",
      percent: 3 / 9,
    });
    expect(deriveBatchProgress(1 / 2, 1, "export:ifc")).toEqual({
      done: 1,
      total: 1,
      stageText: "ifc",
      percent: 1 / 2,
    });
  });

  it("batchStatusText：三态派生（进行中 percent·i/N｜完成 N 项｜失败 kind·unit·原因）+双 null/终态优先", () => {
    expect(batchStatusText("dxf", null, null)).toBeNull(); // 从未提交=零渲染
    expect(
      batchStatusText("dxf", { done: 3, total: 8, stageText: "dxf·u1", percent: 3 / 9 }, null),
    ).toBe("批量出图进行中 33%·3/8");
    expect(
      batchStatusText("dxf", null, { state: "done", files: ["a.dxf", "b.dxf"], failures: [], error: null }),
    ).toBe("批量出图完成：2 项");
    expect(
      batchStatusText("dxf", { done: 3, total: 8, stageText: "dxf·u1", percent: 3 / 9 }, {
        state: "failed",
        files: [],
        failures: [{ index: 1, unit_id: "u2", condition_key: "avg", error: "boom" }],
        error: null,
      }),
    ).toBe("批量出图失败：dxf·u2·boom"); // 终态优先于残留 progress
    expect(
      batchStatusText("dxf", null, { state: "failed", files: [], failures: [], error: "task dead" }),
    ).toBe("批量出图失败：dxf·—·task dead"); // 无逐项 failures 兜底任务级 error
    expect(
      batchStatusText("dxf", null, { state: "cancelled", files: ["a.dxf"], failures: [], error: null }),
    ).toBe("批量导出已取消：已产 1 项");
  });

  it("buildTaskStreamUrl：token 空=零查询参；非空=?token= 编码（SSE 双通道）", () => {
    expect(buildTaskStreamUrl("t1", null)).toBe("/api/events/tasks/t1");
    expect(buildTaskStreamUrl("t 1", "a b")).toBe(
      "/api/events/tasks/t%201?token=a%20b",
    );
  });
});
