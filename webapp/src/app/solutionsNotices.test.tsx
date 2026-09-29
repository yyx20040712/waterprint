/**
 * 方案取数错误回显测试（API-1 R2 回炉 k1-N3/d1-W4——判码扩面最小护栏）。
 *
 * 输入:  SolutionsFetchError + WaterprintApiError{code}（三码：kind 拆分
 *        新码 / 未完成旧码 / 排序键旧码——mutator 同款错误归一形态）
 * 输出:  码→追加提示文案断言（renderToString contain——ToolCallCard 先例）
 */
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { WaterprintApiError } from "../shared/api/http";
import { SolutionsFetchError } from "./solutionsNotices";

const KIND_HINT = "该任务不是枚举任务——仅枚举任务产出方案集，请前往任务面板核对该任务类型";
const NOT_COMPLETE_HINT = "未完成任务取方案=409/排序键白名单外=422——详见任务状态";

function renderCode(code: string): string {
  return renderToString(
    <SolutionsFetchError error={new WaterprintApiError(code, "后端拒绝")} isError={true} />,
  );
}

describe("SolutionsFetchError 判码扩面（API-1）", () => {
  it("TaskKindMismatchError → 任务类型提示（用户语言零 HTTP 面词，不叠旧码文案）", () => {
    const html = renderCode("TaskKindMismatchError");
    expect(html).toContain(KIND_HINT);
    expect(html).not.toContain(NOT_COMPLETE_HINT);
  });
  it("TaskNotCompleteError → 旧文案不动", () => {
    expect(renderCode("TaskNotCompleteError")).toContain(NOT_COMPLETE_HINT);
  });
  it("InvalidPageParameterError → 旧文案不动（分支覆盖）", () => {
    expect(renderCode("InvalidPageParameterError")).toContain(NOT_COMPLETE_HINT);
  });
});
