/**
 * 桌面壳桥接口约定（联机架构第五批 2026-11-19——b7 批实装，本批仅类型）。
 *
 * 输入:  window.pywebview（pywebview 桌面壳注入的桥对象——浏览器态缺席）
 * 输出:  DesktopNetworkRole/DesktopBridgeApi 接口约定+getDesktopBridge()
 *        探测（null=无壳——调用方走诚实降级分支）
 *
 * 规格说明（第五批任务书：绑定切换本体〔127.0.0.1↔0.0.0.0+重启生效〕
 *   属 desktop 壳 b7 批）：
 *   - setNetworkRole(role)：切换运行角色（standalone=回环绑定关联机；
 *     server=0.0.0.0+token 强制——token 生成/保管与重启流程归壳侧）；
 *   - 返回 { ok, restartRequired }——角色切换经本地服务重启生效
 *     （Minecraft 式开关模型：联机开=本地引擎照常+对外绑定）；
 *   - 本批 webapp 消费面=runtimeSettingsModal 切换控件：桥缺席时诚实
 *     降级为「当前绑定展示+桌面端可切换」提示（控件禁用非隐藏）；桥
 *     在场时调用本 API（b7 实装后生效——签名本批冻结防两批间漂移）；
 *   - window.pywebview 全局类型增广单源在本件（其余消费面经
 *     getDesktopBridge 探测取用，不直摸 window 成员）。
 */
export type DesktopNetworkRole = "standalone" | "server";

/** b7 桌面壳桥 API 约定（本批冻结签名——实现 b7 批落地）。 */
export interface DesktopBridgeApi {
  /** 切换运行角色（重启生效——壳侧负责重启本地服务与 token 流程）。 */
  setNetworkRole(
    role: DesktopNetworkRole,
  ): Promise<{ ok: boolean; restartRequired: boolean }>;
}

declare global {
  interface Window {
    pywebview?: { api: DesktopBridgeApi };
  }
}

/** 桥探测（null=浏览器态/壳未注入——调用方走诚实降级分支）。 */
export function getDesktopBridge(): DesktopBridgeApi | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.pywebview?.api ?? null;
}
