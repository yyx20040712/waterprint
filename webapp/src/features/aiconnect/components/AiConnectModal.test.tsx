/**
 * AiConnectPanel 状态渲染/一键接入/成功引导/失败面测试（AI2 批）。
 *
 * 输入:  AiConnectPanel（statusQuery/setupMutation 句柄 props 注入——直构
 *        结果对象零 mock；antd Modal SSR 门户零内容故测试在面板层）+
 *        useAiConnection Probe（mock orval client——生成 hook 消费链）
 * 输出:  四项 ✓/✗ 渲染（全假=三 ✗+沙箱信息行）/ready 横幅/一键接入按钮
 *        禁用态/成功引导文案逐字/失败错误展示/status 查询错误面；
 *        Probe：useAiConnection 封装经 mocked client（mutate 调用链+enabled 门控）
 *
 * 形态说明（沿 TaskPanel.test.tsx SSR 先例——零 jsdom 红线：renderToString
 * 服务端渲染真 antd 树，HTML 串包含断言；按钮点击流归无头 E2E，本件锁
 * 渲染面文案/禁用态与 hook→client 消费链）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import type { AiConnectionStatus } from "../../../shared/api/generated/model";

import { AiConnectPanel, type AiSetupMutation, type AiStatusQuery } from "./AiConnectModal";
import { useAiConnection } from "../api/useAiConnection";

const h = vi.hoisted(() => {
  return {
    queryHook: vi.fn(),
    mutationHook: vi.fn(),
    queryOptions: [] as unknown[],
    mutationOptions: [] as unknown[],
    mutationResult: {
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null as Error | null,
      reset: vi.fn(),
    },
  };
});

vi.mock("../../../shared/api/generated/ai-connection/ai-connection", () => ({
  useGetConnectionStatusApiAiConnectionGet: h.queryHook,
  useSetupConnectionApiAiConnectionSetupPost: h.mutationHook,
  getGetConnectionStatusApiAiConnectionGetQueryKey: () => ["/api/ai/connection"],
}));

h.queryHook.mockImplementation((options: unknown) => {
  h.queryOptions.push(options);
  return { data: undefined, isLoading: true, isError: false, error: null };
});
h.mutationHook.mockImplementation((options: unknown) => {
  h.mutationOptions.push(options);
  return h.mutationResult;
});

/** 全假状态工厂（配置未写/agent 缺/uv 缺——沙箱路径恒推导在场）。 */
function statusAllFalse(): AiConnectionStatus {
  return {
    config_written: false,
    config_paths: [
      "E:\\ws\\waterprint\\.zcode\\config.json",
      "E:\\ws\\.zcode\\config.json",
    ],
    agent_importable: false,
    uv_path: null,
    sandbox_root: "E:\\ws\\ai-sandbox",
    ready: false,
  };
}

/** statusQuery 句柄工厂（data 缺省=加载态；extra 覆盖错误面等）。 */
function statusQueryOf(
  data: AiConnectionStatus | undefined,
  extra?: Partial<AiStatusQuery>,
): AiStatusQuery {
  return {
    data,
    isLoading: data === undefined && !extra?.isError,
    isError: false,
    error: null,
    ...extra,
  } as AiStatusQuery;
}

/** setupMutation 句柄工厂（extra 覆盖 pending/成功/失败面）。 */
function mutationOf(extra?: Partial<AiSetupMutation>): AiSetupMutation {
  return {
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    reset: vi.fn(),
    ...extra,
  } as AiSetupMutation;
}

/** 渲染面板至 HTML 串（两句柄单点注入——onClose 恒空回调）。 */
function renderPanel(
  statusQuery: AiStatusQuery,
  setupMutation: AiSetupMutation,
): string {
  return renderToString(
    <AiConnectPanel
      statusQuery={statusQuery}
      setupMutation={setupMutation}
      onClose={() => undefined}
    />,
  );
}

/** 提取 Alert 可见正文容器内容（回炉 FIX-1：antd 6 将 message/title 归并渲染
 * 于 .ant-alert-title 容器；v5 形态 .ant-alert-message 一并兼容——容器内
 * 断言取代裸 toContain，杜绝 HTML 属性串假绿）。 */
function alertTexts(html: string): string {
  const matches = [
    ...html.matchAll(/class="ant-alert-(?:title|message)"[^>]*>([\s\S]*?)<\/div>/g),
  ];
  return matches.map((match) => match[1]).join("\n");
}

describe("AiConnectPanel 状态渲染（AI2）", () => {
  it("四项列表：全假状态渲染 ✗（配置/模块/uv 三行未就绪）+沙箱路径信息行", () => {
    const html = renderPanel(statusQueryOf(statusAllFalse()), mutationOf());
    expect(html).toContain("工作区配置");
    expect(html).toContain("agent 模块");
    expect(html).toContain("uv 可执行");
    expect(html).toContain("AI 沙箱");
    expect(html).toContain("✗");
    expect(html).toContain("E:\\ws\\ai-sandbox"); // 沙箱根路径展示（信息行）
    expect(html).not.toContain("ant-alert-success"); // 未就绪无成功横幅
  });

  it("全真状态：✓ 四项+已接入横幅（ready 聚合透传——正文容器内断言）", () => {
    const ready = {
      ...statusAllFalse(),
      config_written: true,
      agent_importable: true,
      uv_path: "D:\\uv\\uv.exe",
      ready: true,
    };
    const html = renderPanel(statusQueryOf(ready), mutationOf());
    expect(html).toContain("✓");
    expect(html).not.toContain("✗");
    expect(alertTexts(html)).toContain("已接入");
    expect(html).not.toContain('title="已接入'); // 非 HTML 悬浮属性形态
  });

  it("加载态：状态检查中占位（无四项列表渲染）", () => {
    const html = renderPanel(statusQueryOf(undefined), mutationOf());
    expect(html).toContain("状态检查中");
    expect(html).not.toContain("✓");
    expect(html).not.toContain("✗");
  });

  it("status 查询失败：错误展示（服务端 detail 文案透出——正文容器内断言）", () => {
    const html = renderPanel(
      statusQueryOf(undefined, { isError: true, error: new Error("服务暂不可达"), isLoading: false }),
      mutationOf(),
    );
    expect(alertTexts(html)).toContain("状态检查失败");
    expect(alertTexts(html)).toContain("服务暂不可达");
    expect(html).toContain("ant-alert-error");
  });
});

describe("AiConnectPanel 一键接入（AI2）", () => {
  it("按钮渲染「一键接入」且非 pending 态可点（无禁用标记）", () => {
    const html = renderPanel(statusQueryOf(statusAllFalse()), mutationOf());
    expect(html).toContain("一键接入");
    expect(html).not.toContain("disabled");
  });

  it("pending 态：按钮禁用（重复提交防）", () => {
    const html = renderPanel(
      statusQueryOf(statusAllFalse()),
      mutationOf({ isPending: true }),
    );
    expect(html).toContain("一键接入");
    expect(html).toContain("disabled");
  });

  it("useAiConnection 封装消费 mocked client：enabled 门控直传+mutate 调用链", () => {
    const holder: { value: ReturnType<typeof useAiConnection> | null } = { value: null };
    function Probe() {
      holder.value = useAiConnection(true);
      return null;
    }
    renderToString(
      <QueryClientProvider client={new QueryClient()}>
        <Probe />
      </QueryClientProvider>,
    );
    expect(holder.value).not.toBeNull();
    // status 查询与 setup mutation 均经生成 client 面（mock 捕获消费面）
    expect(h.queryOptions.at(-1)).toEqual({ query: { enabled: true } });
    expect(h.mutationOptions.length).toBeGreaterThan(0);
    // mutate 调用链直达生成 hook 面
    holder.value?.setupMutation.mutate();
    expect(h.mutationResult.mutate).toHaveBeenCalledTimes(1);
  });
});

describe("AiConnectPanel 成功引导/失败面（AI2）", () => {
  it("成功态：引导文案逐字入可见正文容器（重启会话即连+21 个 wp_* 工具）", () => {
    const html = renderPanel(
      statusQueryOf(statusAllFalse()),
      mutationOf({ isSuccess: true }),
    );
    expect(alertTexts(html)).toContain(
      "配置已写入——重启 ZCode 会话（或在 waterprint 目录新开会话）即自动连接，21 个 wp_* 工具可用",
    );
    expect(html).toContain("ant-alert-success");
    expect(html).not.toContain('title="配置已写入'); // 禁 HTML 悬浮属性假绿形态
  });

  it("失败态：错误正文容器展示（uv 缺失 detail 文案透出）", () => {
    const html = renderPanel(
      statusQueryOf(statusAllFalse()),
      mutationOf({ isError: true, error: new Error("uv 可执行文件不在 PATH") }),
    );
    expect(alertTexts(html)).toContain("接入失败");
    expect(alertTexts(html)).toContain("uv 可执行文件不在 PATH");
    expect(html).toContain("ant-alert-error");
  });
});
