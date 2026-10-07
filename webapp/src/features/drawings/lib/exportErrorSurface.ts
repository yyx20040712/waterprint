/**
 * 导出错误呈现调度（M4 批 D1 2026-10-07——ExportButton 与 Ribbon 导出
 * 快访两消费面共享错误链单源件；deps 注入纯函数零 antd 依赖）。
 *
 * 输入:  error: unknown（useExportArtifact mutation onError 面）+kind
 *        （"dxf"|"ifc"——404 引导尾词面）+deps{confirm, notifyError,
 *        retry}（呈现副作用注入：confirm=Modal.confirm 直传签名兼容/
 *        notifyError=messageApi.error/retry=force 重发闭包）
 * 输出:  void（三分支调度：非 WaterprintApiError→notifyError
 *        「导出失败：${message}」；code=StaleExportError→confirm 二选一
 *        〔okText=仍导出旧结果（force）/cancelText=先重算/onOk=retry——
 *        逐字承 ExportButton 原位实现〕；code=ExportSourceNotFoundError
 *        →domainGate 固定摘要「项目暂无完成的计算结果。」+NO_CALC_HINTS
 *        [kind] 尾词；其余 code→notifyError(error.message) 501 诚实透传）
 *
 * 规格说明（M4 brief D1——抽共享而非两处复制：回炉 R1 白名单式教训=同
 *   逻辑漂移防面；ExportButton onError 分支改调本函数=行为等价重构）：
 *   - NO_CALC_HINTS 常量随迁本件（ExportButton 原位删除——单源）；
 *   - 409 二选一交互保持（不降级为纯 message——静默弱化禁）；
 *   - 纯函数零 antd import（confirm/notifyError 经 deps——测试面零
 *     antd mock，exportErrorSurface.test 全 spy 注入直测）。
 */
import { WaterprintApiError } from "../../../shared/api/http";
import { domainGate } from "../../../shared/api/sourceGate";

/** 404 引导尾词（无 done calc——先提交计算；按按钮面 kind 化——R1-4 口径
 *  随迁单源；Ribbon 快访面 kind 恒 "dxf" 同源消费）。 */
export const NO_CALC_HINTS = {
  dxf: "——请先在工艺画布工具条提交计算，完成后再导出图纸。",
  ifc: "——请先在工艺画布工具条提交计算，完成后再导出模型。",
} as const;

/** 导出错误分支 kind（NO_CALC_HINTS 键域）。 */
export type ExportKind = "dxf" | "ifc";

/** deps 注入面（confirm=Modal.confirm 直传签名兼容；notifyError=
 *  messageApi.error；retry=force 重发闭包〔unitId 覆盖参由消费面闭包
 *  自持——总图面保持空串〕）。 */
export type SurfaceExportErrorDeps = {
  confirm: (config: {
    title: string;
    content: string;
    okText: string;
    cancelText: string;
    onOk: () => void;
  }) => void;
  notifyError: (text: string) => void;
  retry: () => void;
};

/** 导出错误呈现调度（三分支——纯函数，呈现副作用全经 deps 注入）。 */
export function surfaceExportError(
  error: unknown,
  kind: ExportKind,
  deps: SurfaceExportErrorDeps,
): void {
  if (!(error instanceof WaterprintApiError)) {
    // 网络错/未知面——不挂误导引导（I-3 分级口径）
    deps.notifyError(`导出失败：${error instanceof Error ? error.message : String(error)}`);
    return;
  }
  if (error.code === "StaleExportError") {
    deps.confirm({
      title: "结果集已过期（stale）",
      content: error.message,
      okText: "仍导出旧结果（force）",
      cancelText: "先重算",
      onOk: () => {
        deps.retry();
      },
    });
    return;
  }
  if (error.code === "ExportSourceNotFoundError") {
    // 回炉 R2（2A4 UF-59 真面）：404 无 done calc=固定摘要（raw 服务端
    // 消息含 API 句式不入用户面——domainGate 收口）；kind 化尾词保持
    const gate = domainGate(error, "ExportSourceNotFoundError", "项目暂无完成的计算结果。");
    deps.notifyError(`${gate.text}${NO_CALC_HINTS[kind]}`);
    return;
  }
  deps.notifyError(error.message); // 501 未就绪等——原文诚实透传
}
