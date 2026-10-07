/**
 * exportErrorSurface 纯函数测试（M4 批 D1——导出错误呈现调度件：ExportButton
 * 与 Ribbon 导出快访两消费面共享错误链；deps 全注入纯逻辑——零 antd mock 面）。
 *
 * 输入:  surfaceExportError(error, kind, deps)（本件 lib——三分支调度：
 *        网络错/未知面→notifyError「导出失败：…」；StaleExportError→confirm
 *        二选一；ExportSourceNotFoundError→固定摘要+NO_CALC_HINTS[kind] 尾词；
 *        其余 code→notifyError(error.message)）+spy deps（confirm/notifyError/
 *        retry——vi.fn 注入，断言分支面互不串扰）
 * 输出:  断言组：①非 WaterprintApiError→notifyError 前缀串②StaleExportError
 *        →confirm 四字段逐字（title/content=error.message/okText/cancelText）
 *        +onOk 触发 retry③ExportSourceNotFoundError→notifyError 固定摘要
 *        +kind 化尾词（dxf/ifc 两键各一）④其余 code→notifyError(error.message)
 */
import { describe, expect, it, vi } from "vitest";

import { surfaceExportError } from "./exportErrorSurface";
import { WaterprintApiError } from "../../../shared/api/http";

/** spy deps 集（每断言一份——confirm 捕获 onOk 后手动触发验 retry 面）。 */
function makeDeps() {
  return {
    confirm: vi.fn(),
    notifyError: vi.fn(),
    retry: vi.fn(),
  };
}

describe("surfaceExportError 三分支调度（M4 D1——两消费面共享错误链）", () => {
  it("非 WaterprintApiError → notifyError「导出失败：${message}」（网络错不挂误导引导——I-3 分级口径）", () => {
    const deps = makeDeps();
    surfaceExportError(new Error("network down"), "dxf", deps);
    expect(deps.notifyError).toHaveBeenCalledWith("导出失败：network down");
    expect(deps.confirm).not.toHaveBeenCalled();
    expect(deps.retry).not.toHaveBeenCalled();
  });

  it("StaleExportError → confirm 二选一四字段逐字（title/content=error.message/okText/cancelText）+onOk 触发 retry", () => {
    const deps = makeDeps();
    surfaceExportError(
      new WaterprintApiError("StaleExportError", "结果集落后当前设计 2 版"),
      "dxf",
      deps,
    );
    expect(deps.confirm).toHaveBeenCalledTimes(1);
    const config = deps.confirm.mock.calls[0]?.[0] as {
      title: string;
      content: string;
      okText: string;
      cancelText: string;
      onOk: () => void;
    };
    expect(config.title).toBe("结果集已过期（stale）");
    expect(config.content).toBe("结果集落后当前设计 2 版");
    expect(config.okText).toBe("仍导出旧结果（force）");
    expect(config.cancelText).toBe("先重算");
    expect(deps.retry).not.toHaveBeenCalled();
    config.onOk();
    expect(deps.retry).toHaveBeenCalledTimes(1); // okText「仍导出旧结果（force）」→force 重发支线
    expect(deps.notifyError).not.toHaveBeenCalled();
  });

  it("ExportSourceNotFoundError → notifyError 固定摘要+NO_CALC_HINTS[kind] 尾词（dxf 面全文）", () => {
    const deps = makeDeps();
    surfaceExportError(
      new WaterprintApiError("ExportSourceNotFoundError", "raw 服务端句式不入用户面"),
      "dxf",
      deps,
    );
    expect(deps.notifyError).toHaveBeenCalledWith(
      "项目暂无完成的计算结果。——请先在工艺画布工具条提交计算，完成后再导出图纸。",
    );
    expect(deps.confirm).not.toHaveBeenCalled();
  });

  it("ExportSourceNotFoundError ifc 面 → 尾词随 kind 化（…完成后再导出模型）", () => {
    const deps = makeDeps();
    surfaceExportError(
      new WaterprintApiError("ExportSourceNotFoundError", "no done calc"),
      "ifc",
      deps,
    );
    expect(deps.notifyError).toHaveBeenCalledWith(
      "项目暂无完成的计算结果。——请先在工艺画布工具条提交计算，完成后再导出模型。",
    );
  });

  it("其余 code（501 未就绪等）→ notifyError(error.message) 原文诚实透传", () => {
    const deps = makeDeps();
    surfaceExportError(
      new WaterprintApiError("ArtifactKindNotReady", "ifc 模板尚未实现"),
      "ifc",
      deps,
    );
    expect(deps.notifyError).toHaveBeenCalledWith("ifc 模板尚未实现");
    expect(deps.confirm).not.toHaveBeenCalled();
  });
});
