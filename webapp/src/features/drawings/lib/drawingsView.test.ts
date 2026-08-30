/**
 * 投影层纯函数测试：导出列表窄化门+图纸目录行模型+工况选项投影+Content-
 * Disposition 文件名解析（node 环境）。
 *
 * 输入:  drawingsView 纯函数（node 环境——零 antd import，先红后绿）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/行序=服务端序/工况索引面/
 *        导出文件名解析 RFC 5987 优先级）
 */
import { describe, expect, it } from "vitest";

import {
  DrawingsViewError,
  buildSheetRows,
  narrowConditionOptions,
  narrowExportsResponse,
  parseDisposition,
  type ExportMetaView,
} from "./drawingsView";

/** 单条产物夹具（ExportMeta 形状——服务端 ExportMeta dataclass asdict 面）。 */
function metaFixture(overrides: Partial<ExportMetaView> = {}): ExportMetaView {
  return {
    project_id: "p-fe9",
    kind: "dxf",
    condition_key: "design",
    file_name: "p-fe9-dxf-design-5b589e4319.dxf",
    design_digest: "5b589e4319153a62d2bfc10324befbd2ebd5a07de2150b8085fd32b48c172b9e",
    engine_version: "waterprint-server 0.1.0",
    data_version: "coefficients@1.1.0+unit_prices@1.0.0",
    stale_labeled: false,
    ...overrides,
  };
}

describe("narrowExportsResponse 窄化门", () => {
  it("合例：多条产物全字段保真窄化（三元组+stale 旗标面）", () => {
    const rows = narrowExportsResponse([
      metaFixture(),
      metaFixture({
        kind: "calcbook",
        file_name: "p-fe9-calcbook-all-5b589e4319.xlsx",
        condition_key: "",
        stale_labeled: true,
      }),
    ]);
    expect(rows).toHaveLength(2);
    expect(rows[0]!.kind).toBe("dxf");
    expect(rows[0]!.design_digest.startsWith("5b589e43")).toBe(true);
    expect(rows[1]!.condition_key).toBe(""); // 服务端缺省工况=空串（文件名 all 分量合同）
    expect(rows[1]!.stale_labeled).toBe(true);
  });

  it("空列表合法（项目尚无产物——面板空态引导面）", () => {
    expect(narrowExportsResponse([])).toEqual([]);
  });

  it("顶层非数组拒（消息带定位）", () => {
    expect(() => narrowExportsResponse(null)).toThrow(DrawingsViewError);
    expect(() => narrowExportsResponse({})).toThrow(/数组/);
    expect(() => narrowExportsResponse("exports")).toThrow(/数组/);
  });

  it("行非对象拒+缺字段拒（kind/file_name/engine_version 逐键定位）", () => {
    expect(() => narrowExportsResponse([42])).toThrow(/对象/);
    for (const key of [
      "project_id",
      "kind",
      "file_name",
      "design_digest",
      "engine_version",
      "data_version",
    ]) {
      const bad: Record<string, unknown> = { ...metaFixture() };
      delete bad[key];
      expect(() => narrowExportsResponse([bad]), key).toThrow(
        DrawingsViewError,
      );
      expect(() => narrowExportsResponse([bad]), key).toThrow(new RegExp(key));
    }
  });

  it("非空字符串域空串拒（kind/project_id/file_name/版本串）", () => {
    for (const key of ["kind", "project_id", "file_name", "engine_version", "data_version"]) {
      const bad: Record<string, unknown> = { ...metaFixture(), [key]: "" };
      expect(() => narrowExportsResponse([bad]), key).toThrow(DrawingsViewError);
    }
  });

  it("stale_labeled 非布尔拒（bool 异形：字符串/数值/NaN）", () => {
    for (const evil of ["yes", 1, Number.NaN, null]) {
      const bad: Record<string, unknown> = { ...metaFixture(), stale_labeled: evil };
      expect(() => narrowExportsResponse([bad]), `stale_labeled=${String(evil)}`).toThrow(
        /stale_labeled/,
      );
    }
  });

  it("design_digest 数值异形拒（NaN 面——三元组摘要必须 hex 串）", () => {
    for (const evil of [Number.NaN, 12345, true]) {
      const bad: Record<string, unknown> = { ...metaFixture(), design_digest: evil };
      expect(() => narrowExportsResponse([bad]), `digest=${String(evil)}`).toThrow(
        /design_digest/,
      );
    }
  });
});

describe("buildSheetRows 图纸目录行模型", () => {
  it("行序=服务端序+key=文件名+digest 摘要前 10 位（显示层口径）", () => {
    const rows = buildSheetRows([
      metaFixture(),
      metaFixture({
        kind: "calcbook",
        file_name: "p-fe9-calcbook-all-5b589e4319.xlsx",
        condition_key: "",
      }),
    ]);
    expect(rows.map((row) => row.key)).toEqual([
      "p-fe9-dxf-design-5b589e4319.dxf",
      "p-fe9-calcbook-all-5b589e4319.xlsx",
    ]);
    expect(rows[0]!.kind).toBe("dxf");
    expect(rows[0]!.conditionKey).toBe("design");
    expect(rows[0]!.designDigest).toBe("5b589e4319");
    expect(rows[0]!.stale).toBe(false);
  });

  it("工况空串→显示层 all 兜底（与文件名分量 fallback 同源口径）", () => {
    const rows = buildSheetRows([
      metaFixture({ condition_key: "", file_name: "p-fe9-dxf-all-5b589e4319.dxf" }),
    ]);
    expect(rows[0]!.conditionKey).toBe("all");
  });

  it("stale 行透传（force 导出旧结果的显式标注面）", () => {
    const rows = buildSheetRows([metaFixture({ stale_labeled: true })]);
    expect(rows[0]!.stale).toBe(true);
  });
});

describe("parseDisposition Content-Disposition 文件名解析（UX1 DS-05 迁测）", () => {
  it("RFC 5987 filename* 优先并解码（百分比编码 → 原文名；与 plain 并存时优先后者不用）", () => {
    const header =
      'attachment; filename="fallback.dxf"; filename*=UTF-8\'\'%E6%B1%A0-a.dxf';
    expect(parseDisposition(header)).toBe("池-a.dxf");
  });

  it("无 filename* 时取 plain filename（带引号与裸值两形态）", () => {
    expect(
      parseDisposition('attachment; filename="p1-dxf-design-5b589e4319.dxf"'),
    ).toBe("p1-dxf-design-5b589e4319.dxf");
    expect(parseDisposition("attachment; filename=plain.dxf")).toBe("plain.dxf");
  });

  it("解码失败原样透传（非 URI 编码形态——服务端 ascii 命名面不丢名）", () => {
    expect(parseDisposition("attachment; filename*=UTF-8''%%bad%%.dxf")).toBe(
      "%%bad%%.dxf",
    );
  });

  it("null 头/空串/无文件名字段 → null（消费面客户端兜底命名）", () => {
    expect(parseDisposition(null)).toBeNull();
    expect(parseDisposition("")).toBeNull();
    expect(parseDisposition("attachment")).toBeNull();
  });
});

describe("narrowConditionOptions 工况选项投影", () => {
  it("合例：conditions 数组投影（cost 同端点响应面）", () => {
    const raw = { conditions: ["avg", "design"], condition_key: "design" };
    expect(narrowConditionOptions(raw)).toEqual(["avg", "design"]);
  });

  it("缺 conditions/非数组/空数组/空串元素拒", () => {
    expect(() => narrowConditionOptions({})).toThrow(/conditions/);
    expect(() => narrowConditionOptions({ conditions: "design" })).toThrow(/conditions/);
    expect(() => narrowConditionOptions({ conditions: [] })).toThrow(/conditions/);
    expect(() => narrowConditionOptions({ conditions: ["design", ""] })).toThrow(
      /conditions/,
    );
  });

  it("非对象顶层拒", () => {
    expect(() => narrowConditionOptions("avg")).toThrow(DrawingsViewError);
  });
});
