/**
 * 批量出图纯函数测试：buildBatchExportBody 单 body 构造（node 环境）。
 *
 * 输入:  batchExport 纯函数（node 环境——零 antd/零运行期库 import，
 *        先红后绿：module 未就绪=import 解析红）
 * 输出:  纯数据构造契约断言（空 units→items 空/每单元恰一项/顺序保持/
 *        工况空串透传/project_id 进 body/批级 unit 不落键——SVRB
 *        服务端批量任务形态 6 用例）
 */
import { describe, expect, it } from "vitest";

import { buildBatchExportBody } from "./batchExport";

describe("buildBatchExportBody 批量任务体构造（SVRB）", () => {
  it("空 units → items 空数组（body 骨架仍构造——N>1 调用面守卫）", () => {
    expect(buildBatchExportBody("p1", [], "design")).toEqual({
      project_id: "p1",
      condition_key: "design",
      options: { items: [] },
    });
  });

  it("每单元恰一项：items[i]={unit_id, condition_key}（逐项透传面）", () => {
    const body = buildBatchExportBody(
      "p1",
      ["municipal_cass", "municipal_chenshachi"],
      "design",
    );
    expect(body.options.items).toEqual([
      { unit_id: "municipal_cass", condition_key: "design" },
      { unit_id: "municipal_chenshachi", condition_key: "design" },
    ]);
  });

  it("顺序保持：units 序=items 序（服务端 items 序=进度/落盘序）", () => {
    const units = ["u3", "u1", "u2"];
    const body = buildBatchExportBody("p1", units, "avg");
    expect(body.options.items.map((item) => item.unit_id)).toEqual(units);
  });

  it("工况空串透传：condition_key 永不 undefined（服务端缺省工况合同）", () => {
    const body = buildBatchExportBody("p1", ["u1"], "");
    expect(body.condition_key).toBe("");
    expect(body.options.items[0]?.condition_key).toBe("");
  });

  it("project_id 进 body 顶层（单 body 形态——服务端 ExportRequest 合同）", () => {
    expect(buildBatchExportBody("proj-42", ["u1"], "design").project_id).toBe(
      "proj-42",
    );
  });

  it("批级 unit_id 不落键（items 逐项自带——item 覆盖批级语义零兜底）", () => {
    const body = buildBatchExportBody("p1", ["u1", "u2"], "design");
    expect("unit_id" in body.options).toBe(false);
  });
});
