/**
 * feature 级错误边界：画布崩溃不清空整个应用（教训 §15 工程细节 4）。
 *
 * 输入:  子组件树 + 降级渲染（fallback）
 * 输出:  捕获渲染异常后的隔离降级 UI
 *
 * 规格说明（骨架冻结）：
 *   - 每个 feature 挂载一个本组件实例（app 层组合时逐一切包）；
 *   - 捕获后：保留其他面板 + 错误面板显示"重试/复制诊断"，
 *     错误信息走结构化日志（含 queryKey/路由名，可反查）；
 *   - 禁止吞错： componentDidCatch 必须上报，不许静默渲染 fallback。
 */
import React from "react";

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; label: string },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(_error: unknown, _info: React.ErrorInfo) {
    void _error;
    void _info;
    throw new Error("骨架未接线：错误上报待 M0 接线期实现（禁止静默吞错）");
  }

  render() {
    if (this.state.hasError) {
      return <div>面板异常（{this.props.label}）——待接线完整降级 UI</div>;
    }
    return this.props.children;
  }
}
