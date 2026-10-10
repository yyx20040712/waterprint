/**
 * @vitest-environment jsdom
 *
 * v4 连接设置自愈层测试（B3 R1 回炉 R1-W1——AUTH_EVENT 监听+TokenSettings
 * Modal 上提 shellV4 恒挂载层后的独立测试缝：hook+Modal 组合直测，
 * mount→dispatch AUTH_EVENT→Modal 开；dockBar.test B3 describe 的自愈例
 * 随本缝迁移〔dockBar 卸载=监听死区根因——上提后 zone 切换不卸载〕）。
 *
 * 输入:  useSettingsSelfHeal（状态+AUTH_EVENT 监听 hook）+TokenSettingsModal
 *        真件——Harness=shellV4 生产组合形最小复刻（手动入口钮=dockBar
 *        设置钮经 onOpenSettings 透传的等价触发位）
 * 输出:  断言族：①dispatch AUTH_EVENT→Modal 自动开（401 自愈 parity
 *        ——legacy App.tsx:305-307 同款；恒挂载层语义）②openSettings
 *        手动入口同源开（单一 state 承载自愈/手动两面）③卸载移除监听
 *        （单实例语义——k2-N8 注记面；卸载后 dispatch 零残留）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { AUTH_EVENT } from "../../shared/events";
import { TokenSettingsModal } from "../tokenSettingsModal";
import { useSettingsSelfHeal } from "./settingsSelfHeal";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** shellV4 组合形最小复刻（hook+Modal；harness 钮=onOpenSettings 等价位）。 */
function Harness() {
  const { settingsOpen, openSettings, closeSettings } = useSettingsSelfHeal();
  return (
    <>
      <button type="button" data-testid="h-open-settings" onClick={openSettings} />
      <TokenSettingsModal open={settingsOpen} onClose={closeSettings} />
    </>
  );
}

afterEach(cleanup);

describe("连接设置自愈层（R1-W1——恒挂载层）", () => {
  it("dispatch AUTH_EVENT→Modal 自动开（401 自愈 parity——上提后 zone 切换不卸载）", async () => {
    render(<Harness />);
    // 关闭态起点：Modal 未渲染（antd 关态零 portal 内容）
    expect(document.querySelector(".ant-modal")).toBeNull();
    window.dispatchEvent(new Event(AUTH_EVENT));
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")).not.toBeNull();
      expect(document.querySelector(".ant-input-password")).not.toBeNull();
    });
  });

  it("openSettings 手动入口同源开（dockBar 设置钮经 onOpenSettings 同一 state）", async () => {
    const { container } = render(<Harness />);
    fireEvent.click(
      container.querySelector<HTMLButtonElement>(
        '[data-testid="h-open-settings"]',
      ) as HTMLButtonElement,
    );
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")).not.toBeNull();
    });
    // 标题单一承载（自愈面/手动面同 Modal）
    const title = document.querySelector(".ant-modal-title")?.textContent;
    expect(title).toBe("连接设置");
  });

  it("卸载移除监听（单实例语义——卸载后 dispatch 零残留监听）", async () => {
    const { unmount } = render(<Harness />);
    unmount();
    window.dispatchEvent(new Event(AUTH_EVENT));
    await Promise.resolve();
    expect(document.querySelector(".ant-modal")).toBeNull();
  });
});
