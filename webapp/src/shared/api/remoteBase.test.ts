/**
 * 远程基址存取 vitest（联机架构第六批 2026-11-19——node 直测：归一化
 * 纯函数+localStorage 读写环）。
 *
 * 输入:  remoteBase（normalizeRemoteBaseUrl/getRemoteBaseUrl/
 *        setRemoteServer/clearRemoteServer）
 * 输出:  断言三组：①归一化（合法 origin 归一/尾斜线剥除/非法形态 null
 *        全集）②存储环（写→读归一值→清除→null；畸形 JSON/畸形档案
 *        =null 不外泄）③本地模式缺省（无档案=null——http.ts 零行为变
 *        的地基）
 */
import { beforeEach, describe, expect, it } from "vitest";

import {
  clearRemoteServer,
  getRemoteBaseUrl,
  normalizeRemoteBaseUrl,
  REMOTE_SERVER_STORAGE_KEY,
  setRemoteServer,
} from "./remoteBase";

/** node 环境内存 localStorage 替身（最小面——getItem/setItem/removeItem）。 */
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

beforeEach(() => {
  installMemoryStorage();
});

describe("remoteBase（客户端模式远程基址存取——联机第六批）", () => {
  it("归一化：合法 origin 原样/尾斜线剥除/默认端口归一", () => {
    expect(normalizeRemoteBaseUrl("http://192.168.50.18:8000")).toBe(
      "http://192.168.50.18:8000",
    );
    expect(normalizeRemoteBaseUrl("  http://192.168.50.18:8000/ ")).toBe(
      "http://192.168.50.18:8000",
    );
    expect(normalizeRemoteBaseUrl("https://design-server.example")).toBe(
      "https://design-server.example",
    );
  });

  it("归一化：非法形态全集=null（单一空态——不向 fetch 面外泄）", () => {
    expect(normalizeRemoteBaseUrl("")).toBeNull();
    expect(normalizeRemoteBaseUrl("   ")).toBeNull();
    expect(normalizeRemoteBaseUrl("192.168.50.18:8000")).toBeNull(); // 无 scheme
    expect(normalizeRemoteBaseUrl("http://host.example/path")).toBeNull();
    expect(normalizeRemoteBaseUrl("http://host.example/?q=1")).toBeNull();
    expect(normalizeRemoteBaseUrl("http://user:pw@host.example")).toBeNull();
    expect(normalizeRemoteBaseUrl("ftp://host.example")).toBeNull();
    expect(normalizeRemoteBaseUrl("http://host.example#frag")).toBeNull();
  });

  it("存储环：写→读归一值→清除→null；畸形档案=视同未配置", () => {
    expect(getRemoteBaseUrl()).toBeNull(); // 本地模式缺省（零行为变地基）
    setRemoteServer("http://127.0.0.1:8100/");
    expect(getRemoteBaseUrl()).toBe("http://127.0.0.1:8100");
    clearRemoteServer();
    expect(getRemoteBaseUrl()).toBeNull();
    // 脏值防御：手改 localStorage 的畸形 JSON/畸形 base_url 均归 null
    localStorage.setItem(REMOTE_SERVER_STORAGE_KEY, "{not-json");
    expect(getRemoteBaseUrl()).toBeNull();
    localStorage.setItem(
      REMOTE_SERVER_STORAGE_KEY,
      JSON.stringify({ base_url: "javascript:alert(1)" }),
    );
    expect(getRemoteBaseUrl()).toBeNull();
    localStorage.setItem(REMOTE_SERVER_STORAGE_KEY, JSON.stringify({}));
    expect(getRemoteBaseUrl()).toBeNull();
  });

  it("非法地址拒写：setRemoteServer 不落非法形态", () => {
    setRemoteServer("not a url");
    expect(localStorage.getItem(REMOTE_SERVER_STORAGE_KEY)).toBeNull();
  });
});
