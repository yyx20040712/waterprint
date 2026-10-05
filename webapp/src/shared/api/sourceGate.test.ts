/**
 * 领域码门控测试（2A4 批 2026-10-05 UF-59——TDD 先红后绿：node 直测）。
 *
 * 输入:  domainGate（shared/api/sourceGate）+WaterprintApiError（code 归一
 *        面——http.ts 服务端 error_type 透传）
 * 输出:  断言五组：①领域码命中={domain:true,text:fixedText}（raw 服务端
 *        消息不透出）；②他码 WaterprintApiError={domain:false,text:raw
 *        message}（网络错保 raw=I-3 口径）；③普通 Error={domain:false,
 *        text:message}（窄化中文 Error 透出）；④非 Error={domain:false,
 *        text:未知错误}（兜底）；⑤code 大小写敏感实证（=== 全等比较）
 */
import { describe, expect, it } from "vitest";

import { domainGate } from "./sourceGate";
import { WaterprintApiError } from "./http";

describe("domainGate（领域码门控——R3 F1''/R3b I-3 分级口径单源收口）", () => {
  it("象限一：领域码命中={domain:true, text:fixedText}——raw 服务端消息不透出", () => {
    const error = new WaterprintApiError(
      "SceneSourceNotFoundError",
      "项目 'abc123' 无最近完成结果集（先 POST /api/calc/run）",
    );
    const gate = domainGate(error, "SceneSourceNotFoundError", "项目暂无完成的计算结果。");
    expect(gate).toEqual({ domain: true, text: "项目暂无完成的计算结果。" });
  });

  it("象限二：他码 WaterprintApiError={domain:false, text:raw message}（网络错保 raw=I-3 口径）", () => {
    const error = new WaterprintApiError("HTTP_503", "请求失败：GET /api/scene/abc → 503");
    const gate = domainGate(error, "SceneSourceNotFoundError", "项目暂无完成的计算结果。");
    expect(gate).toEqual({ domain: false, text: "请求失败：GET /api/scene/abc → 503" });
  });

  it("象限三：普通 Error={domain:false, text:message}（窄化中文 Error 透出）", () => {
    const gate = domainGate(
      new Error("工况窄化失败：未知节点形态"),
      "CostSourceNotFoundError",
      "项目暂无完成的计算结果。",
    );
    expect(gate).toEqual({ domain: false, text: "工况窄化失败：未知节点形态" });
  });

  it("象限四：非 Error={domain:false, text:未知错误}（兜底——不改语义只收形）", () => {
    const gate = domainGate("网关页 502", "CostSourceNotFoundError", "项目暂无完成的计算结果。");
    expect(gate).toEqual({ domain: false, text: "未知错误" });
  });

  it("code 大小写敏感实证：小写串不命中（error.code 归一后原样全等比较）", () => {
    const error = new WaterprintApiError("scenesourcenotfounderror", "lower-case-code");
    const gate = domainGate(error, "SceneSourceNotFoundError", "项目暂无完成的计算结果。");
    expect(gate.domain).toBe(false);
    expect(gate.text).toBe("lower-case-code");
  });
});
