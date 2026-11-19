/**
 * 客户端连接状态机 store vitest（联机架构第六批 2026-11-19——node 直测：
 * 六态转移+水合初值+本地态守卫〔转移 no-op〕）。
 *
 * 输入:  clientConnectionStore（useClientConnectionStore——zustand 直测
 *        getState/setState；remoteBase 经 localStorage 替身受控）
 * 输出:  断言四组：①无档案水合=local 态 ②有档案水合=connecting 起点
 *        ③五转移（connecting/online 携 meta/mismatch 清面/offline/
 *        token_invalid/version_mismatch 携明细）④本地态守卫（remoteBase
 *        null 时全转移 no-op——单机面零状态写入）
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MetaInfo } from "../shared/api/generated/model";
import {
  clearRemoteServer,
  setRemoteServer,
} from "../shared/api/remoteBase";
import { useClientConnectionStore } from "./clientConnectionStore";

const META: MetaInfo = {
  app_version: "waterprint-server 0.1.0",
  data_version: "assumptions@1.0.0+coefficients@1.8.0+unit_prices@1.2.0",
  api_version: "1.0",
};

/** node 环境内存 localStorage 替身（remoteBase.test 同制式）。 */
function installMemoryStorage(): void {
  const store = new Map<string, string>();
  globalThis.localStorage = {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
    removeItem: (key: string) => void store.delete(key),
    clear: () => store.clear(),
    key: () => null,
    get length() {
      return store.size;
    },
  } as Storage;
}

/** 模块重导重放水合（store 创建期同步读 storage——vi.resetModules 后
 *  动态 import 得新模块实例；返回新 store 供断言）。 */
async function freshStore(): Promise<typeof useClientConnectionStore> {
  vi.resetModules();
  return (await import("./clientConnectionStore")).useClientConnectionStore;
}

beforeEach(() => {
  installMemoryStorage();
  clearRemoteServer();
});

describe("clientConnectionStore（连接状态机——联机第六批）", () => {
  it("无档案水合=local 态（单机缺省）", async () => {
    const store = await freshStore();
    expect(store.getState().phase).toBe("local");
    expect(store.getState().remoteBase).toBeNull();
  });

  it("有档案水合=connecting 起点（客户端模式装配期）", async () => {
    setRemoteServer("http://127.0.0.1:8100");
    const store = await freshStore();
    const state = store.getState();
    expect(state.phase).toBe("connecting");
    expect(state.remoteBase).toBe("http://127.0.0.1:8100");
  });

  it("五转移：online 携 meta 清 mismatch；version_mismatch 携明细", async () => {
    const store = await freshStore();
    store.setState({ remoteBase: "http://h:1" });
    const actions = store.getState();
    actions.setPhaseConnecting();
    expect(store.getState().phase).toBe("connecting");
    actions.setOnline(META);
    expect(store.getState()).toMatchObject({
      phase: "online",
      serverMeta: META,
      mismatch: null,
    });
    actions.setOffline();
    expect(store.getState().phase).toBe("offline");
    actions.setTokenInvalid();
    expect(store.getState().phase).toBe("token_invalid");
    actions.setVersionMismatch(META, {
      kind: "api",
      expected: "1.0",
      actual: "2.0",
    });
    expect(store.getState()).toMatchObject({
      phase: "version_mismatch",
      mismatch: { kind: "api", expected: "1.0", actual: "2.0" },
    });
  });

  it("本地态守卫：remoteBase null 时转移全 no-op（单机零状态写入）", async () => {
    const store = await freshStore();
    store.setState({ remoteBase: null });
    const actions = store.getState();
    actions.setPhaseConnecting();
    actions.setOnline(META);
    actions.setOffline();
    actions.setTokenInvalid();
    actions.setVersionMismatch(META, {
      kind: "data",
      expected: "x",
      actual: "y",
    });
    const state = store.getState();
    expect(state.phase).toBe("local");
    expect(state.serverMeta).toBeNull();
    expect(state.mismatch).toBeNull();
  });
});
