/**
 * 运行角色面纯函数 vitest（联机架构第五批 2026-11-19——node 直测：
 * 文案单源/降级/配对地址构造/首选地址回落）。
 *
 * 输入:  runtimeFace（RUNTIME_MODE_LABELS/runtimeModeLabel/
 *        pairingAddressUrl/runtimePrimaryAddress 纯函数）
 * 输出:  断言四组：①runtimeModeLabel 三态（standalone/server/undefined
 *        降级）②降级文案=standalone 文案（同一常量族）③pairingAddressUrl
 *        无 window 形态（node 环境=无端口段）④首选地址 lan 首选→bind_host
 *        回落
 */
import { describe, expect, it } from "vitest";

import {
  RUNTIME_FALLBACK_LABEL,
  RUNTIME_MODE_LABELS,
  pairingAddressUrl,
  runtimeModeLabel,
  runtimePrimaryAddress,
} from "./runtimeFace";

describe("runtimeFace（运行角色面纯函数——联机第五批）", () => {
  it("runtimeModeLabel 三态：standalone/server 两文案+undefined 降级单机", () => {
    expect(
      runtimeModeLabel({
        role: "standalone",
        bind_host: "127.0.0.1",
        lan_addresses: [],
        token_configured: false,
        token_reveal: "",
      }),
    ).toBe("单机模式 · 本地引擎");
    expect(
      runtimeModeLabel({
        role: "server",
        bind_host: "0.0.0.0",
        lan_addresses: ["192.168.50.24"],
        token_configured: true,
        token_reveal: null,
      }),
    ).toBe("服务端 · 局域网可被发现");
    expect(runtimeModeLabel(undefined)).toBe("单机模式 · 本地引擎");
  });

  it("降级文案=standalone 文案同源（请求失败不虚报服务端态）", () => {
    expect(RUNTIME_FALLBACK_LABEL).toBe(RUNTIME_MODE_LABELS.standalone);
    expect(Object.keys(RUNTIME_MODE_LABELS).sort()).toEqual([
      "server",
      "standalone",
    ]);
  });

  it("pairingAddressUrl：node 无 window 形态=无端口段", () => {
    expect(pairingAddressUrl("192.168.50.24")).toBe("http://192.168.50.24");
  });

  it("runtimePrimaryAddress：server lan 首选；空集/standalone=null（消费方降级）", () => {
    expect(
      runtimePrimaryAddress({
        role: "server",
        bind_host: "0.0.0.0",
        lan_addresses: ["192.168.50.24", "10.0.0.2"],
        token_configured: true,
        token_reveal: null,
      }),
    ).toBe("192.168.50.24");
    // server 空 lan 集=null——不展示 bind_host（0.0.0.0 非客户端可连地址）
    expect(
      runtimePrimaryAddress({
        role: "server",
        bind_host: "0.0.0.0",
        lan_addresses: [],
        token_configured: true,
        token_reveal: null,
      }),
    ).toBeNull();
    // standalone=无监听地址语义恒 null
    expect(
      runtimePrimaryAddress({
        role: "standalone",
        bind_host: "127.0.0.1",
        lan_addresses: [],
        token_configured: false,
        token_reveal: "",
      }),
    ).toBeNull();
  });
});
