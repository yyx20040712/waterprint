/**
 * feature 级错误边界：画布崩溃不清空整个应用（教训 §15 工程细节 4）。
 *
 * 输入:  子组件树 + 面板路由名 label（错误上报与降级 UI 共用）+可选
 *        onRetry（重试转调——消费面重建 React.lazy thenable）
 * 输出:  捕获渲染异常后的隔离降级 UI（label+分级摘要+「重试」+诊断详情
 *        原生折叠区）+结构化上报（errorReportPayload 四字段不变）
 *
 * 规格说明（FE3 批 6b 段一 D4 最小接线；R1 补 2026-08-29；2B5 批 UF-65
 * 范式件 2026-10-07）：
 *   - componentDidCatch=console.error 结构化单对象上报 errorReportPayload
 *     {feature, message, stack, componentStack}（含路由名可反查；升级
 *     上报通道挂账 UX 批）——上报语义零改（2B5 D5：该语句逐字不动）；
 *   - UF-65（2B5 D2/D3/D4）：raw 客户端库言不直插用户面——
 *     gradeClientError 纯函数三分级（chunk/词典命中/未知：非 Error 归一
 *     String 后同管道）+库言词典（模块级常量数组，词条可扩=后续批加
 *     词条零机制改）；raw message 与 componentStack 收进原生
 *     <details> 折叠区（默认收起、零新依赖——antd Collapse 不引入；
 *     「复制诊断」挂账 UX 批）；
 *   - fallback：label+分级摘要+「重试」按钮——onRetry 在场则转调
 *     （R1/一审 I-1：消费面借此重建 React.lazy 失败 thenable——chunk
 *     加载失败被复位重挂载不会重执行 import，须换新 lazy 实例）；
 *     不在场则维持复位 hasError（子树重挂载）；
 *   - 禁止吞错：getDerivedStateFromError 与 componentDidCatch 双通道在场，
 *     不许静默渲染 fallback；
 *   - payload/分级纯函数与类同文件（node 测试 import react 无 DOM 安全
 *     ——payload 直测面在 app/queryClient.test.ts D6-③ 组；分级+降级面
 *     jsdom 组件测试在 app/errorBoundary.test.tsx）。
 */
import React from "react";

/** 结构化上报载荷（D4 冻结结构：四字段；缺 stack 容错为 null）。 */
export interface ErrorReportPayload {
  feature: string;
  message: string;
  stack: string | null;
  componentStack: string | null;
}

/** 上报载荷纯函数：error 归一 message/stack（非 Error 与缺 stack 容错）。 */
export function errorReportPayload(
  label: string,
  error: unknown,
  componentStack: string | null,
): ErrorReportPayload {
  return {
    feature: label,
    message: error instanceof Error ? error.message : String(error),
    stack:
      error instanceof Error && typeof error.stack === "string"
        ? error.stack
        : null,
    componentStack,
  };
}

/** 客户端错误分级（2B5 D2 三分支：chunk=动态模块加载失败族；dictionary=
 *  库言词典命中；unknown=兜底）。 */
export type ClientErrorGrade = "chunk" | "dictionary" | "unknown";

/** 分级产物：summary=主面分级摘要；detail=归一 raw 消息（只进诊断折叠区）。 */
export interface GradedClientError {
  grade: ClientErrorGrade;
  summary: string;
  detail: string;
}

/** chunk 级固定摘要（D2 分支①逐字；UF-66 批 2026-10-07 联动改文——
 *  cache-bust 恢复重试有效性外，措辞补「或刷新页面」reload 兜底）。 */
const CHUNK_SUMMARY =
  "页面模块加载失败——多为网络中断或系统刚更新所致，请重试或刷新页面";

/** 未知级兜底摘要（D2 分支③逐字）。 */
const UNKNOWN_SUMMARY =
  "面板发生未预期错误，请重试；若持续出现请展开诊断详情反馈";

/** chunk 级消息族（动态模块加载失败——浏览器/打包器原生日志形态集；
 *  独立于词典常量：分级序 chunk→词典→未知（D2 ①②③），固定摘要由
 *  D2 逐字给定不走词条面。Firefox 方言小写起头（回炉 R2）——/i 容错）。 */
const CHUNK_MESSAGE_PATTERNS: readonly RegExp[] = [
  /Loading chunk/,
  /Failed to fetch dynamically imported module/,
  /Importing a module script failed/,
  /error loading dynamically imported module/i,
];

/** 库言词典（2B5 D3——[pattern, 摘要][] 序匹配先命中先用；词条可扩=
 *  后续批加词条零机制改。种子两族：Minified React error/THREE.
 *  WebGLRenderer〔M5 前置种子〕——chunk 族归 CHUNK_MESSAGE_PATTERNS，
 *  词典实码两词条与 D3 基准一致（回炉 R3 勘误：原注「三族」系把
 *  chunk 族并入误计）。 */
const LIBRARY_ERROR_DICTIONARY: readonly (readonly [RegExp, string])[] = [
  [/Minified React error/, "界面组件内部错误，请重试"],
  [/THREE\.WebGLRenderer/, "三维渲染环境不可用（显卡/浏览器支持不足）"],
];

/** 错误分级纯函数（2B5 D2）：非 Error 归一 String 后同管道
 *  （「未知错误」口径沿 errorReportPayload 的 message 归一面）。 */
export function gradeClientError(error: unknown): GradedClientError {
  const detail = error instanceof Error ? error.message : String(error);
  if (CHUNK_MESSAGE_PATTERNS.some((pattern) => pattern.test(detail))) {
    return { grade: "chunk", summary: CHUNK_SUMMARY, detail };
  }
  for (const [pattern, summary] of LIBRARY_ERROR_DICTIONARY) {
    if (pattern.test(detail)) {
      return { grade: "dictionary", summary, detail };
    }
  }
  return { grade: "unknown", summary: UNKNOWN_SUMMARY, detail };
}

export class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode;
    label: string;
    onRetry?: () => void;
  },
  {
    hasError: boolean;
    graded: GradedClientError | null;
    componentStack: string | null;
  }
> {
  state: {
    hasError: boolean;
    graded: GradedClientError | null;
    componentStack: string | null;
  } = { hasError: false, graded: null, componentStack: null };

  static getDerivedStateFromError(error: unknown) {
    return { hasError: true, graded: gradeClientError(error) };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    // D4 最小接线：结构化单对象上报（升级上报通道挂账 UX 批）
    console.error(
      errorReportPayload(this.props.label, error, info.componentStack ?? null),
    );
    // UF-65（2B5 D4）：componentStack 进诊断折叠区（渲染期不可得——
    // 提交阶段随上报同源捕获；上报语句上面逐字不动）
    this.setState({ componentStack: info.componentStack ?? null });
  }

  render() {
    // graded 与 hasError 恒同置（GDSFE 单点写入）——窄化防御（回炉 R6）
    if (this.state.hasError && this.state.graded !== null) {
      return (
        <div role="alert">
          <div>面板异常（{this.props.label}）</div>
          <div>{this.state.graded.summary}</div>
          <button
            type="button"
            onClick={() => {
              // R1（一审 I-1）：onRetry 在场先转调（同一事件批内——消费面
              // 重建 lazy thenable 与本边界复位一次渲染共同生效）
              this.props.onRetry?.();
              this.setState({
                hasError: false,
                graded: null,
                componentStack: null,
              });
            }}
          >
            重试
          </button>
          {/* UF-65（2B5 D4）：raw/组件栈收进原生折叠区（默认收起）——
              「复制诊断」挂账 UX 批 */}
          <details>
            <summary>诊断详情</summary>
            <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
              {this.state.graded.detail}
            </pre>
            {this.state.componentStack !== null ? (
              <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                {this.state.componentStack}
              </pre>
            ) : null}
          </details>
        </div>
      );
    }
    return this.props.children;
  }
}
