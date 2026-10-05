/**
 * 领域码门控（2A4 批 2026-10-05 UF-59）：R3 F1''/R3b 门控分支单源收口件。
 *
 * 输入:  error:unknown（查询/mutation onError 面）+code:string（领域码
 *        ——WaterprintApiError.code=服务端 error_type 归一）+fixedText:
 *        string（命中面固定摘要——raw 服务端消息含 API 句式/项目 hash
 *        不入用户面）
 * 输出:  {domain, text}——domain 命中={domain:true, text:fixedText}；否则
 *        ={domain:false, text:raw 兜底}（Error.message｜「未知错误」）
 *
 * 规格说明（2A4 brief D2——I-3 分级口径逐字移植，不改语义只收形）：
 *   - 匹配律：WaterprintApiError 且 code 全等（===，大小写敏感——error_
 *     type 归一后原样比较）→domain 命中；Error→raw=message；其余→raw=
 *     「未知错误」（三分支与 R3 F1''/R3b 六点 inline 三元逐字等价——
 *     纯重构面）；
 *   - 消费面：Scene 404/drawingsPane exports/CheckedUnitsPanel toast
 *     （UF-59 三面）+五 pane 六 no-calc 分支两态化（UF-60①）；
 *   - 网络错/其他错保 raw 透出=诊断诚实先例（R3 已裁，I-3 口径）。
 */
import { WaterprintApiError } from "./http";

/** 领域码门控（R3 F1''/R3b I-3 分级口径单源收口）：
 *  domain 命中={domain:true, text:fixedText}；否则={domain:false,
 *  text:raw 兜底}（Error.message｜「未知错误」）。 */
export function domainGate(
  error: unknown,
  code: string,
  fixedText: string,
): { domain: boolean; text: string } {
  if (error instanceof WaterprintApiError && error.code === code) {
    return { domain: true, text: fixedText };
  }
  return { domain: false, text: error instanceof Error ? error.message : "未知错误" };
}
