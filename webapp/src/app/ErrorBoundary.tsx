/**
 * feature 级错误边界：画布崩溃不清空整个应用（教训 §15 工程细节 4）。
 *
 * 输入:  子组件树 + 面板路由名 label（错误上报与降级 UI 共用）
 * 输出:  捕获渲染异常后的隔离降级 UI（label+错误摘要+重试）+结构化上报
 *
 * 规格说明（FE3 批 6b 段一，D4 最小接线——去骨架 throw 占位；
 * R1 补 2026-08-29）：
 *   - componentDidCatch=console.error 结构化单对象上报 errorReportPayload
 *     {feature, message, stack, componentStack}（含路由名可反查；升级
 *     上报通道挂账 UX 批）——onRetry 只外转重试动作，上报语义不变；
 *   - fallback：label+错误 message 摘要+「重试」按钮——onRetry 在场则
 *     转调（R1/一审 I-1：消费面借此重建 React.lazy 失败 thenable——
 *     chunk 加载失败被复位重挂载不会重执行 import，须换新 lazy 实例）；
 *     不在场则维持复位 hasError（子树重挂载）。「复制诊断」挂账 UX 批；
 *   - 禁止吞错：getDerivedStateFromError 与 componentDidCatch 双通道在场，
 *     不许静默渲染 fallback；
 *   - payload 纯函数与类同文件（node 测试 import react 无 DOM 安全——
 *     直测面在 app/queryClient.test.ts D6-③ 组）。
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

export class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode;
    label: string;
    onRetry?: () => void;
  },
  { hasError: boolean; message: string | null }
> {
  state: { hasError: boolean; message: string | null } = {
    hasError: false,
    message: null,
  };

  static getDerivedStateFromError(error: unknown) {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    // D4 最小接线：结构化单对象上报（升级上报通道挂账 UX 批）
    console.error(
      errorReportPayload(this.props.label, error, info.componentStack ?? null),
    );
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert">
          <div>
            面板异常（{this.props.label}）：{this.state.message ?? "未知错误"}
          </div>
          <button
            type="button"
            onClick={() => {
              // R1（一审 I-1）：onRetry 在场先转调（同一事件批内——消费面
              // 重建 lazy thenable 与本边界复位一次渲染共同生效）
              this.props.onRetry?.();
              this.setState({ hasError: false, message: null });
            }}
          >
            重试
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
