/**
 * @vitest-environment jsdom
 *
 * 运行方式与联机 Modal vitest（联机架构第五批 2026-11-19——稿
 * connection.html 服务端态：真实角色呈现/配对卡 token 门/桥缺席诚实
 * 降级/客户端模式下一批占位）。
 *
 * 输入:  RuntimeSettingsModal（Harness 关态挂载→事件开——settingsSelfHeal
 *        .test 同制式；runtime 查询模块替身 gate 受控数据；jsdom 无
 *        window.pywebview=桥缺席降级路径天然覆盖）
 * 输出:  断言五组：①standalone 态：单机说明+开关关+桥缺席降级注记
 *        ②server 态+回环 reveal：配对卡地址行+token 明文+监听中徽标
 *        ③server 态+非回环（reveal=null）：token 不展示+仅本机可见提示
 *        ④客户端模式=下一批占位（说明行非虚假入口）⑤读失败警示行
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";

import { RuntimeSettingsModal } from "./runtimeSettingsModal";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  runtime: undefined as
    | {
        role: "standalone" | "server";
        bind_host: string;
        lan_addresses: string[];
        token_configured: boolean;
        token_reveal: string | null;
      }
    | undefined,
  isError: false,
}));

vi.mock("../shared/api/generated/meta/meta", () => ({
  useGetRuntimeApiRuntimeGet: () => ({
    data: gate.runtime,
    isError: gate.isError,
    error: gate.isError ? new Error("probe") : null,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

/** Harness：关态挂载→事件开（settingsSelfHeal.test 同制式——Modal 开态
 *  经用户事件进入非初始 render 直开，规避 antd 动效 appear 回调越环境
 *  生命周期的拆除竞态——全库 Modal 测试统一形态）。 */
function Harness() {
  const [open, setOpen] = useState(false);
  return (
    <QueryClientProvider client={queryClient}>
      <button
        type="button"
        data-testid="h-open-runtime"
        onClick={() => setOpen(true)}
      />
      <RuntimeSettingsModal open={open} onClose={() => setOpen(false)} />
    </QueryClientProvider>
  );
}

/** 挂载+开 Modal（waitFor 到 portal 在场——开关态转换经 act 结算）。 */
async function renderOpenedModal() {
  render(<Harness />);
  fireEvent.click(
    document.querySelector('[data-testid="h-open-runtime"]') as HTMLElement,
  );
  await waitFor(() => {
    expect(document.querySelector(".ant-modal")).not.toBeNull();
  });
}

beforeEach(() => {
  gate.runtime = undefined;
  gate.isError = false;
});
afterEach(async () => {
  cleanup();
  // 排空 antd Modal 动效尾帧（motion 回调 ~数百 ms 级定时器）——防调度
  // 器回调越 jsdom 环境生命周期触发 window 已拆（react-dom scheduler
  // 的 setImmediate 泄漏面——全量套件偶发 unhandled 元凶，实测加此排空
  // 后 11+ 连跑零复现；时长取动效上界 400ms）
  await new Promise((resolve) => setTimeout(resolve, 400));
});

describe("运行方式与联机 Modal（联机第五批）", () => {
  it("standalone 态：两级开关说明+开关关+桥缺席诚实降级注记（当前绑定展示）", async () => {
    gate.runtime = {
      role: "standalone",
      bind_host: "127.0.0.1",
      lan_addresses: [],
      token_configured: false,
      token_reveal: "",
    };
    await renderOpenedModal();
    expect(document.body.textContent).toContain("两级开关");
    expect(document.body.textContent).toContain("已关闭——单机运行");
    // jsdom 无 window.pywebview——桥缺席降级：绑定展示+桌面端提示
    const note = document.querySelector(
      '[data-testid="wp-v4-runtime-bridge-note"]',
    );
    expect(note?.textContent).toContain("当前绑定：127.0.0.1");
    expect(note?.textContent).toContain("桌面端提供");
    // 配对卡缺席（standalone 不展示）
    expect(
      document.querySelector('[data-testid="wp-v4-runtime-pairing"]'),
    ).toBeNull();
  });

  it("server 态+回环 reveal：配对卡在场+地址行+token 明文+监听中徽标", async () => {
    gate.runtime = {
      role: "server",
      bind_host: "0.0.0.0",
      lan_addresses: ["192.168.50.24"],
      token_configured: true,
      token_reveal: "b5-modal-token-0123456789",
    };
    await renderOpenedModal();
    const pairing = document.querySelector(
      '[data-testid="wp-v4-runtime-pairing"]',
    );
    expect(pairing).not.toBeNull();
    expect(pairing?.textContent).toContain("http://192.168.50.24");
    expect(pairing?.textContent).toContain("监听中");
    expect(
      document.querySelector('[data-testid="wp-v4-runtime-token"]')
        ?.textContent,
    ).toContain("b5-modal-token-0123456789");
    expect(document.body.textContent).toContain("已开启——本机作为服务端");
  });

  it("server 态+非回环（reveal=null）：token 不展示+仅本机可见提示", async () => {
    gate.runtime = {
      role: "server",
      bind_host: "0.0.0.0",
      lan_addresses: ["192.168.50.24"],
      token_configured: true,
      token_reveal: null,
    };
    await renderOpenedModal();
    expect(
      document.querySelector('[data-testid="wp-v4-runtime-token"]'),
    ).toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-runtime-token-hidden"]')
        ?.textContent,
    ).toContain("仅在本机（回环连接）可见");
    expect(document.body.textContent).not.toContain("WATERPRINT_SECRET");
  });

  it("客户端模式=下一批占位说明行（不设虚假入口）", async () => {
    await renderOpenedModal();
    const row = document.querySelector(
      '[data-testid="wp-v4-runtime-client-next"]',
    );
    expect(row?.textContent).toContain("客户端模式");
    expect(row?.textContent).toContain("下一批");
  });

  it("runtime 读失败=警示行（诚实降级按单机显示）", async () => {
    gate.isError = true;
    await renderOpenedModal();
    expect(
      document.querySelector('[data-testid="wp-v4-runtime-read-error"]')
        ?.textContent,
    ).toContain("运行状态读取失败");
  });
});
