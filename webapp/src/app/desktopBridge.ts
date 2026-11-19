/**
 * 桌面壳桥接口约定（联机第五批 2026-11-19 类型冻结；第七批 b7 实装扩面）。
 *
 * 输入:  window.pywebview（pywebview 桌面壳注入的桥对象——浏览器态缺席）
 * 输出:  DesktopNetworkRole/DesktopBootstrapRole/DesktopConfigSnapshot/
 *        DesktopBridgeApi 接口约定+getDesktopBridge() 探测（null=无壳——
 *        调用方走诚实降级分支）
 *
 * 规格说明（第五批任务书：绑定切换本体〔127.0.0.1↔0.0.0.0+重启生效〕
 *   属 desktop 壳；第七批 b7 落地 Python 侧实现=desktop/waterprint_desktop/
 *   bridge.py，两面包名/键集逐名对齐）：
 *   - setNetworkRole(role)：切换运行角色（standalone=回环绑定关联机；
 *     server=0.0.0.0+token 强制；client=不起引擎+本地静态壳供 UI——
 *     b7 扩 "client" 联合成员供首启三选，签名形状不变）；
 *   - 返回 { ok, restartRequired }——ok+restartRequired=false=活体重启
 *     已在调用内完成（壳侧承担「重启生效」）；ok=false+restartRequired=
 *     true=装配失败但配置已持久化（下次应用启动按新角色装配）；
 *   - getConfig()（b7 新增）：四角色快照（unconfigured=首启向导注入态
 *     ——OnboardingGate 消费）+shellOrigin/engineOrigin（null=对应服务
 *     未运行——窗口导航与降级展示消费）；
 *   - window.pywebview 全局类型增广单源在本件（其余消费面经
 *     getDesktopBridge 探测取用，不直摸 window 成员）。
 */
export type DesktopNetworkRole = "standalone" | "server" | "client";

/** 快照角色面（DesktopNetworkRole ∪ 首启未配置态）。 */
export type DesktopBootstrapRole = "unconfigured" | DesktopNetworkRole;

/** 桌面壳配置快照（getConfig 返回——desktop bridge.getConfig 同形）。 */
export interface DesktopConfigSnapshot {
  /** 当前角色（unconfigured=首启向导注入态）。 */
  role: DesktopBootstrapRole;
  /** 静态壳 origin（客户端/引导态在跑=http://127.0.0.1:8620；null=未运行）。 */
  shellOrigin: string | null;
  /** 引擎 origin（单机/服务端态在跑；null=未运行——client/unconfigured 态）。 */
  engineOrigin: string | null;
}

/** b7 桌面壳桥 API 约定（第五批冻结签名+b7 扩 getConfig/客户端角色）。 */
export interface DesktopBridgeApi {
  /** 切换运行角色（活体重启在壳侧本调用内完成）。 */
  setNetworkRole(
    role: DesktopNetworkRole,
  ): Promise<{ ok: boolean; restartRequired: boolean }>;
  /** 配置快照（首启向导与降级展示消费）。 */
  getConfig(): Promise<DesktopConfigSnapshot>;
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
