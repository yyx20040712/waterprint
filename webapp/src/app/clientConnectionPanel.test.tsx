/**
 * @vitest-environment jsdom
 *
 * 客户端模式连接面板 vitest（联机架构第六批 2026-11-19——稿 connection.
 * html 客户端段：录入面/握手结果四态/连接与断开动作）。
 *
 * 输入:  ClientConnectionPanel（performHandshake 模块替身受控四态+真
 *        clientConnectionStore〔setState 控 phase〕+真 localStorage token/
 *        remote 档案+window.location.reload 替身）
 * 输出:  断言五组：①本地态录入面在场（地址/token/测试连接）②非法地址
 *        =表单内联拒（探测不发）③ok：结果卡+连接钮→点击落 token+档案
 *        +reload ④version_mismatch：双方版本并陈+连接钮缺席（阻断）；
 *        token_invalid：凭据提示 ⑤已连接态：当前连接卡+断开→清档案
 *        reload（token 保留——v1 瑕疵面行为锚）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ClientConnectionPanel } from "./clientConnectionPanel";
import { useClientConnectionStore } from "./clientConnectionStore";
import type { HandshakeOutcome } from "./remoteHandshake";
import {
  clearRemoteServer,
  getRemoteBaseUrl,
  REMOTE_SERVER_STORAGE_KEY,
} from "../shared/api/remoteBase";
import { getApiToken, setApiToken } from "../shared/api/token";

const META = {
  app_version: "waterprint-server 0.1.0",
  data_version: "assumptions@1.0.0+coefficients@1.8.0+unit_prices@1.2.0",
  api_version: "1.0",
};

/** 探测替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  outcome: null as HandshakeOutcome | null,
  calls: 0,
}));

vi.mock("./remoteHandshake", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./remoteHandshake")>();
  return {
    ...actual,
    performHandshake: vi.fn(async () => {
      gate.calls += 1;
      return gate.outcome ?? { status: "unreachable" };
    }),
  };
});

/** reload 替身（jsdom location.reload 缺席面——defineProperty 直换）。 */
const reloadSpy = vi.fn();
function installReloadSpy(): void {
  Object.defineProperty(window, "location", {
    value: { ...window.location, reload: reloadSpy },
    writable: true,
  });
}

beforeEach(() => {
  gate.outcome = null;
  gate.calls = 0;
  reloadSpy.mockClear();
  installReloadSpy();
  localStorage.clear();
  clearRemoteServer();
  useClientConnectionStore.setState({
    phase: "local",
    remoteBase: null,
    serverMeta: null,
    mismatch: null,
  });
});

afterEach(() => {
  cleanup();
});

/** 面板输入（受控 Input——value 直设后派 change）。 */
function setInput(testId: string, value: string): void {
  const input = document.querySelector(
    `[data-testid="${testId}"]`,
  );
  expect(input).not.toBeNull();
  fireEvent.change(input as HTMLInputElement, { target: { value } });
}

describe("客户端模式连接面板（联机第六批）", () => {
  it("本地态录入面在场：地址+token+测试连接（无结果卡）", () => {
    render(<ClientConnectionPanel />);
    expect(
      document.querySelector('[data-testid="wp-v4-client-address"]'),
    ).not.toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-client-token"]'),
    ).not.toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-client-test"]'),
    ).not.toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-client-result"]'),
    ).toBeNull();
  });

  it("非法地址=表单内联拒（探测不发——normalize 先行）", async () => {
    render(<ClientConnectionPanel />);
    setInput("wp-v4-client-address", "不是地址");
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-client-test"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(
        document.querySelector('[data-testid="wp-v4-client-form-error"]')
          ?.textContent,
      ).toContain("http(s)://主机[:端口]");
    });
    expect(gate.calls).toBe(0);
  });

  it("ok：结果卡握手完成+连接钮→落 token+远程档案+reload", async () => {
    gate.outcome = { status: "ok", meta: META };
    render(<ClientConnectionPanel />);
    setInput("wp-v4-client-address", "http://127.0.0.1:8100/");
    setInput("wp-v4-client-token", "tok-1234567890abcdef");
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-client-test"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(
        document.querySelector('[data-testid="wp-v4-client-result-badge"]')
          ?.textContent,
      ).toContain("握手完成");
    });
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-client-connect"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(reloadSpy).toHaveBeenCalled();
    });
    expect(getApiToken()).toBe("tok-1234567890abcdef");
    expect(getRemoteBaseUrl()).toBe("http://127.0.0.1:8100");
  });

  it("version_mismatch：双方版本并陈+连接钮缺席（握手阻断）", async () => {
    gate.outcome = {
      status: "version_mismatch",
      meta: { ...META, api_version: "2.0" },
      check: { ok: false, kind: "api", expected: "1.0", actual: "2.0" },
    };
    render(<ClientConnectionPanel />);
    setInput("wp-v4-client-address", "http://127.0.0.1:8100");
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-client-test"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(
        document.querySelector('[data-testid="wp-v4-client-result-badge"]')
          ?.textContent,
      ).toContain("版本不匹配");
    });
    const result = document.querySelector(
      '[data-testid="wp-v4-client-result"]',
    );
    expect(result?.textContent).toContain("期望 1.0 ↔ 服务器 2.0");
    expect(
      document.querySelector('[data-testid="wp-v4-client-connect"]'),
    ).toBeNull();
    expect(reloadSpy).not.toHaveBeenCalled();
    expect(getRemoteBaseUrl()).toBeNull();
  });

  it("token_invalid：凭据提示+连接钮缺席", async () => {
    gate.outcome = { status: "token_invalid" };
    render(<ClientConnectionPanel />);
    setInput("wp-v4-client-address", "http://127.0.0.1:8100");
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-client-test"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(
        document.querySelector('[data-testid="wp-v4-client-result-badge"]')
          ?.textContent,
      ).toContain("token 失效");
    });
    expect(
      document.querySelector('[data-testid="wp-v4-client-connect"]'),
    ).toBeNull();
  });

  it("已连接态：当前连接卡+断开→清档案+reload（token 保留——v1 行为锚）", async () => {
    setApiToken("keep-me-token-123456");
    localStorage.setItem(
      REMOTE_SERVER_STORAGE_KEY,
      JSON.stringify({ base_url: "http://127.0.0.1:8100" }),
    );
    useClientConnectionStore.setState({
      phase: "online",
      remoteBase: "http://127.0.0.1:8100",
      serverMeta: META,
      mismatch: null,
    });
    render(<ClientConnectionPanel />);
    const current = document.querySelector(
      '[data-testid="wp-v4-client-current"]',
    );
    expect(current?.textContent).toContain("http://127.0.0.1:8100");
    expect(current?.textContent).toContain(META.app_version);
    fireEvent.click(
      document.querySelector(
        '[data-testid="wp-v4-client-disconnect"]',
      ) as HTMLElement,
    );
    await waitFor(() => {
      expect(reloadSpy).toHaveBeenCalled();
    });
    expect(getRemoteBaseUrl()).toBeNull();
    expect(getApiToken()).toBe("keep-me-token-123456"); // 单槽保留（瑕疵记档）
  });
});
