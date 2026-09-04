/**
 * 批量出图纯函数测试：buildBatchExportRequests 逐请求构造（node 环境）。
 *
 * 输入:  batchExport 纯函数（node 环境——零 antd/零运行期库 import，
 *        先红后绿：module 未就绪=import 解析红）
 * 输出:  纯数据构造契约断言（空 units→[]/每单元恰一项/顺序保持/
 *        工况空串归一/dedupe 责任归调用方/kind 面 URL 常量）
 */
import { describe, expect, it } from "vitest";

import {
  BATCH_EXPORT_URL,
  buildBatchExportRequests,
} from "./batchExport";

describe("buildBatchExportRequests 批量请求构造", () => {
  it("空 units → 空数组（无选中即无请求——调用面零循环）", () => {
    expect(buildBatchExportRequests([], "design")).toEqual([]);
  });

  it("每单元恰一项：options.unit_id 单发面+condition_key 透传（纯数据逐请求）", () => {
    const requests = buildBatchExportRequests(
      ["municipal_cass", "municipal_chenshachi"],
      "design",
    );
    expect(requests).toHaveLength(2);
    expect(requests[0]).toEqual({
      condition_key: "design",
      options: { unit_id: "municipal_cass" },
    });
    expect(requests[1]).toEqual({
      condition_key: "design",
      options: { unit_id: "municipal_chenshachi" },
    });
  });

  it("顺序保持：units 序=请求序（客户端顺序循环消费面——i/N 逐次依据）", () => {
    const units = ["u3", "u1", "u2"];
    const requests = buildBatchExportRequests(units, "avg");
    expect(requests.map((request) => request.options.unit_id)).toEqual(units);
  });

  it("工况空串归一：空串原样透传（服务端缺省工况合同——永不 undefined）", () => {
    for (const request of buildBatchExportRequests(["u1"], "")) {
      expect(request.condition_key).toBe("");
      expect("condition_key" in request).toBe(true);
    }
  });

  it("重复项原样保持（dedupe 责任归调用方——antd Select multiple 已去重）", () => {
    expect(buildBatchExportRequests(["u1", "u1"], "design")).toHaveLength(2);
  });

  it("kind 面 URL 常量=/api/exports/dxf（单产物端点——批量对偶拒绝外的唯一通道）", () => {
    expect(BATCH_EXPORT_URL).toBe("/api/exports/dxf");
  });
});
