/**
 * @vitest-environment jsdom
 *
 * 保存冲突对话单源测试（F2 并发丢更新批 2026-11-20）。
 *
 * 输入:  surfaceSaveConflict/baseHashOf/confirmSaveConflict（本件三符号）
 *        +WaterprintApiError（code=ProjectConcurrentWriteError 载体）
 * 输出:  vitest 断言组：①baseHashOf 提取五形态；②非冲突错误零接手；
 *        ③三选对话三分支（覆盖=重拉→onOverwrite({raw,baseHash})、
 *        放弃=onDiscard、稍后=零动作）；④重拉无基线=放弃重发；
 *        ⑤对话框文案（标题/引导/服务器 detail）
 *
 * 形态说明：三分支走真实 confirmSaveConflict（antd Modal.confirm 渲染
 *   进 document.body——fireEvent 点击驱动）；调度面 deps spy 注入沿
 *   exportErrorSurface 先例（纯函数面零 mock）。
 */
import { act, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WaterprintApiError } from "../api/http";
import {
  SAVE_CONFLICT_GUIDE,
  SAVE_CONFLICT_TITLE,
  baseHashOf,
  confirmSaveConflict,
  surfaceSaveConflict,
  type SaveConflictDeps,
} from "./saveConflictModal";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
if (typeof window.matchMedia !== "function") {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}
// antd Button wave 效果取伪元素样式——jsdom 无该面剥参降噪（本件不测样式）
{
  const origGetComputedStyle = window.getComputedStyle.bind(window);
  window.getComputedStyle = (el: Element, pseudoEl?: string | null) =>
    origGetComputedStyle(el);
}

/** 冲突错误载体（服务端 409 统一错误体归一后形态）。 */
const conflictError = new WaterprintApiError(
  "ProjectConcurrentWriteError",
  "项目已被其他窗口/机器修改：你基于 aaaabbbbcccc…，服务端现行 ddddeeeeffff…（条件保存基线不符——禁止静默覆盖；选择用我的覆盖/放弃我的改动/稍后处理）",
  { detail: "…", error_type: "ProjectConcurrentWriteError" },
);

const LATEST = {
  raw: {
    format_version: "1.0",
    metadata: {
      format_version: "1.0",
      content_hash: "ddddeeeeffff0000111122223333444455556666",
      engine_version: "e",
      data_version: "d",
    },
  },
  baseHash: "ddddeeeeffff0000111122223333444455556666",
};

/** deps 全 spy 装配（confirm 可换真实呈现）。 */
function makeDeps(
  refetch: SaveConflictDeps["refetchLatest"] = vi.fn().mockResolvedValue(LATEST),
): {
  deps: SaveConflictDeps;
  onOverwrite: ReturnType<typeof vi.fn>;
  onDiscard: ReturnType<typeof vi.fn>;
  refetch: ReturnType<typeof vi.fn>;
} {
  const onOverwrite = vi.fn();
  const onDiscard = vi.fn();
  return {
    deps: {
      confirm: confirmSaveConflict,
      refetchLatest: refetch,
      onOverwrite,
      onDiscard,
    },
    onOverwrite,
    onDiscard,
    refetch: refetch as ReturnType<typeof vi.fn>,
  };
}

/** 对话钮定位（footer 三钮 testid 锚）。 */
const buttonOf = (testid: string): HTMLButtonElement => {
  const button = document.querySelector<HTMLButtonElement>(
    `[data-testid="${testid}"]`,
  );
  if (button === null) {
    throw new Error(`对话钮未渲染：${testid}`);
  }
  return button;
};

afterEach(() => {
  cleanup();
  document.body.innerHTML = ""; // Modal.confirm 挂 body——用例间清场
});

describe("baseHashOf 读时基线提取（五形态）", () => {
  it("正常 raw → metadata.content_hash 字符串", () => {
    expect(baseHashOf(LATEST.raw)).toBe(LATEST.baseHash);
  });

  it("缺 metadata/非串值/空串/null raw → null（不携基线直写兼容面）", () => {
    expect(baseHashOf({ format_version: "1.0" })).toBeNull();
    expect(
      baseHashOf({ metadata: { content_hash: 123 } } as Record<string, unknown>),
    ).toBeNull();
    expect(baseHashOf({ metadata: { content_hash: "" } })).toBeNull();
    expect(baseHashOf(undefined)).toBeNull();
    expect(baseHashOf(null)).toBeNull();
  });
});

describe("surfaceSaveConflict 接手判定", () => {
  it("非冲突错误（普通 Error/他码 WaterprintApiError）→false 零呈现", () => {
    const { deps, onOverwrite, onDiscard } = makeDeps();
    expect(surfaceSaveConflict(new Error("网络断"), deps)).toBe(false);
    expect(
      surfaceSaveConflict(new WaterprintApiError("HTTP_409", "锁冲突"), deps),
    ).toBe(false); // 锁冲突兜底码归 isLockConflict 提示面——非本对话
    expect(onOverwrite).not.toHaveBeenCalled();
    expect(onDiscard).not.toHaveBeenCalled();
    expect(document.querySelector('[data-testid="save-conflict-overwrite"]')).toBeNull();
  });
});

describe("三选对话三分支（真实 antd 呈现）", () => {
  it("分支①用我的覆盖：重拉最新→onOverwrite({raw, baseHash})——对话显标题/引导/服务器 detail", async () => {
    const { deps, onOverwrite, refetch } = makeDeps();
    expect(surfaceSaveConflict(conflictError, deps)).toBe(true);
    await waitFor(() => {
      expect(buttonOf("save-conflict-overwrite")).toBeTruthy();
    });
    // 文案：标题+三分支引导+服务器 detail（错误分级用户面）
    expect(document.body.textContent).toContain(SAVE_CONFLICT_TITLE);
    expect(document.body.textContent).toContain(SAVE_CONFLICT_GUIDE);
    expect(document.body.textContent).toContain("ddddeeeeffff…");
    await act(async () => {
      fireEvent.click(buttonOf("save-conflict-overwrite"));
    });
    expect(refetch).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(onOverwrite).toHaveBeenCalledWith(LATEST);
    });
  });

  it("分支②放弃我的改动：onDiscard——零重拉零重发", async () => {
    const { deps, onDiscard, onOverwrite, refetch } = makeDeps();
    expect(surfaceSaveConflict(conflictError, deps)).toBe(true);
    await waitFor(() => {
      expect(buttonOf("save-conflict-discard")).toBeTruthy();
    });
    await act(async () => {
      fireEvent.click(buttonOf("save-conflict-discard"));
    });
    expect(onDiscard).toHaveBeenCalledTimes(1);
    expect(refetch).not.toHaveBeenCalled();
    expect(onOverwrite).not.toHaveBeenCalled();
  });

  it("分支③稍后处理：仅关对话——本地保留零动作", async () => {
    const { deps, onDiscard, onOverwrite, refetch } = makeDeps();
    expect(surfaceSaveConflict(conflictError, deps)).toBe(true);
    await waitFor(() => {
      expect(buttonOf("save-conflict-later")).toBeTruthy();
    });
    await act(async () => {
      fireEvent.click(buttonOf("save-conflict-later"));
    });
    expect(onDiscard).not.toHaveBeenCalled();
    expect(onOverwrite).not.toHaveBeenCalled();
    expect(refetch).not.toHaveBeenCalled();
  });

  it("覆盖重拉无基线（refetchLatest=null——重拉失败/基线缺位）→放弃重发零 onOverwrite（fail-visible 不盲写）", async () => {
    const { deps, onOverwrite } = makeDeps(vi.fn().mockResolvedValue(null));
    expect(surfaceSaveConflict(conflictError, deps)).toBe(true);
    await waitFor(() => {
      expect(buttonOf("save-conflict-overwrite")).toBeTruthy();
    });
    await act(async () => {
      fireEvent.click(buttonOf("save-conflict-overwrite"));
    });
    await waitFor(() => {
      expect(onOverwrite).not.toHaveBeenCalled();
    });
  });
});
