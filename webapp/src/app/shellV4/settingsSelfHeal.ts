/**
 * v4 连接设置自愈层 hook（B3 R1 回炉 R1-W1 2026-10-10——AUTH_EVENT 监听+
 * settingsOpen 状态自 dockBar 上提壳恒挂载层：dockBar 仅 design 区挂载，
 * projects/network/drafting/viewer3d/report 五区卸载=监听死区〔legacy
 * App.tsx:305 级监听恒在=v4 parity 缺口——双审 k2-W1/d1-W6 实证〕）。
 *
 * 输入:  AUTH_EVENT（window 事件——customInstance 401 派发面 http.ts:67）
 * 输出:  {settingsOpen, openSettings, closeSettings}——自愈监听与手动入口
 *        （dockBar 设置钮经 onOpenSettings 透传）两面同源单 state；Modal
 *        承载（TokenSettingsModal）由 shellV4 在 ConfigProvider 内恒挂载
 *        渲染——zone 切换不卸载，五区自愈可达。
 *
 * 规格说明（B3 R1 回炉任务书 §一.R1-W1）：
 *   - 监听挂/卸对称（卸载移除——单实例语义：shell 唯一监听，多实例零
 *     残留〔k2-N8 注记面随修法关账〕）；
 *   - 自愈回路 parity：legacy App.tsx:305-307 同款（AUTH_EVENT→自动开
 *     连接设置）；派发侧=shared/api/http.ts 401 面（R2-A D4 在案）。
 */
import { useCallback, useEffect, useState } from "react";

import { AUTH_EVENT } from "../../shared/events";

/** 连接设置开态+AUTH_EVENT 401 自愈监听（shellV4 恒挂载层调用）。 */
export function useSettingsSelfHeal() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  // 401 自愈回路 parity（legacy App.tsx:305-307 同款——customInstance 401
  // 派发面；恒挂载层语义=zone 切换不卸载；卸载移除监听）
  useEffect(() => {
    const openSettings = () => setSettingsOpen(true);
    window.addEventListener(AUTH_EVENT, openSettings);
    return () => window.removeEventListener(AUTH_EVENT, openSettings);
  }, []);

  /** 手动入口（dockBar 设置钮经 DesignZone→DockBar onOpenSettings 透传）。 */
  const openSettings = useCallback(() => setSettingsOpen(true), []);
  const closeSettings = useCallback(() => setSettingsOpen(false), []);
  return { settingsOpen, openSettings, closeSettings };
}
