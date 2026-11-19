/**
 * @vitest-environment jsdom
 *
 * 建项 Modal vitest（e2e-fix-r3 批 2026-11-19——F6/F7 回归修复锚：开态
 * initialMode 同步与提交期防抖；件本体行为面）。
 *
 * 输入:  CreateProjectModal（生成 projects 钩子模块替身——mutate 受控计
 *        数；Harness 关态挂载→两组事件钮开 blank/import 态）
 * 输出:  断言四组：①F7 首开即导入态（标题「导入项目」+文件选择在场——
 *        不再需二次点击）②F7 关后重开换态（blank↔import 开态真值同步）
 *        ③F6 连点创建钮只发一次 mutate（同步双击在飞拦截——onSettled
 *        复位后可再提交）④空白态说明文案如实（不含「建设中」过期口径）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";

import { CreateProjectModal } from "./createProjectModal";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  mutate: vi.fn(),
  isPending: false,
}));

vi.mock("../shared/api/generated/projects/projects", () => ({
  getListProjectsApiProjectsGetQueryKey: () => ["/api/projects"],
  useCreateProjectApiProjectsPost: () => ({
    mutate: gate.mutate,
    isPending: gate.isPending,
    isError: false,
    error: null,
    reset: vi.fn(),
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

/** Harness：关态挂载→事件开（全库 Modal 测试统一形态——开态经用户事件
 *  进入，规避 antd 动效 appear 回调越环境生命周期的拆除竞态）。 */
function Harness() {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"blank" | "import">("blank");
  return (
    <QueryClientProvider client={queryClient}>
      <button
        type="button"
        data-testid="h-open-blank"
        onClick={() => {
          setMode("blank");
          setOpen(true);
        }}
      />
      <button
        type="button"
        data-testid="h-open-import"
        onClick={() => {
          setMode("import");
          setOpen(true);
        }}
      />
      <CreateProjectModal
        open={open}
        initialMode={mode}
        onClose={() => setOpen(false)}
        onCreated={() => setOpen(false)}
      />
    </QueryClientProvider>
  );
}

/** 挂载并经事件开指定态（waitFor 到弹窗标题在场）。 */
async function openAs(which: "blank" | "import") {
  render(<Harness />);
  fireEvent.click(
    document.querySelector(`[data-testid="h-open-${which}"]`) as HTMLElement,
  );
  await waitFor(() => {
    expect(document.querySelector(".ant-modal-title")).not.toBeNull();
  });
  return document.querySelector(".ant-modal-title")?.textContent ?? "";
}

beforeEach(() => {
  gate.mutate.mockClear();
  gate.isPending = false;
});
afterEach(cleanup);

describe("F7 开态 initialMode 同步（一次点击即对的态）", () => {
  it("首开即导入态：标题「导入项目」+文件选择在场（不先经 blank）", async () => {
    const title = await openAs("import");
    expect(title).toBe("导入项目");
    expect(document.body.textContent).toContain("选择项目 JSON 文件");
  });

  it("关后重开换态：blank 开过→关→import 开=导入态（开态真值同步）", async () => {
    await openAs("blank");
    // antd autoInsertSpace：两字钮渲染「取 消」——按去空白文本匹配；
    // jsdom 无关闭动画结算——不候 title 卸载，直接以 import 态重开断终态
    fireEvent.click(
      [...document.querySelectorAll(".ant-modal button")].find((el) =>
        (el.textContent ?? "").replace(/\s/g, "").includes("取消"),
      ) as HTMLElement,
    );
    fireEvent.click(
      document.querySelector('[data-testid="h-open-import"]') as HTMLElement,
    );
    await waitFor(() => {
      expect(document.querySelector(".ant-modal-title")?.textContent).toBe(
        "导入项目",
      );
    });
    expect(document.body.textContent).toContain("选择项目 JSON 文件");
  });

  it("blank 首开=新建态标题（回归锚——缺省态不受影响）", async () => {
    const title = await openAs("blank");
    expect(title).toBe("新建项目");
  });
});

describe("F6 提交期防抖（双击只发一次 POST）", () => {
  it("同步双击创建钮=mutate 恰一次（在飞拦截先于 re-render）", async () => {
    await openAs("blank");
    const input = document.querySelector(
      ".ant-modal .ant-input",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "E2E-防抖" } });
    const submitButton = [...document.querySelectorAll("button")].find(
      (el) => el.textContent === "创建项目",
    ) as HTMLButtonElement;
    expect(submitButton.disabled).toBe(false);
    // 同步连击两次（渲染时序未及生效——F6 抓的双发窗口）
    fireEvent.click(submitButton);
    fireEvent.click(submitButton);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate.mock.calls[0]?.[0]?.data?.name).toBe("E2E-防抖");
  });

  it("onSettled 复位后可再次提交（失败重试面不受拦截）", async () => {
    await openAs("blank");
    const input = document.querySelector(
      ".ant-modal .ant-input",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "重试面" } });
    const submitButton = [...document.querySelectorAll("button")].find(
      (el) => el.textContent === "创建项目",
    ) as HTMLButtonElement;
    fireEvent.click(submitButton);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    // 模拟一次请求结算（onSettled 复位在飞标记）
    const settled = gate.mutate.mock.calls[0]?.[1]?.onSettled as
      | (() => void)
      | undefined;
    expect(typeof settled).toBe("function");
    settled?.();
    fireEvent.click(submitButton);
    expect(gate.mutate).toHaveBeenCalledTimes(2);
  });
});

describe("空白态说明文案如实（e2e 疑点收口）", () => {
  it("不含「建设中」过期口径（编辑面已可用）", async () => {
    await openAs("blank");
    expect(document.body.textContent).not.toContain("建设中");
    expect(document.body.textContent).toContain("在「工艺」画布中添加");
  });
});
