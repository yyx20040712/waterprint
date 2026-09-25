/**
 * LlmConfigSection 渲染面/保存载荷测试（F1 批）。
 *
 * 输入:  LlmConfigSection（useAiConfig mock——query/mutation 句柄直构注入）
 *        + buildSavePayload 纯函数（保存载荷构造面）
 * 输出:  ①未配置态状态行文案+表单可编辑；②保存载荷键域正确（api_key 空
 *        输入不发送——防误清除既有密钥）+enabled 门控穿线；③has_api_key
 *        占位符回显不回明文（base_url/model/timeout 回填口径）
 *
 * 形态说明（沿 AiConnectModal.test.tsx SSR 先例——零 jsdom 红线：
 * renderToString 服务端渲染真 antd 树，HTML 串包含断言；按钮点击流归
 * 无头 E2E，本件锁渲染面文案/回填口径与载荷构造纯函数）。
 */
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import type { AiConfigResponse } from "../../../shared/api/generated/model";

import { buildSavePayload, LlmConfigSection } from "./LlmConfigSection";

const h = vi.hoisted(() => {
  return {
    hook: vi.fn(),
    enabledLog: [] as boolean[],
    mutation: {
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null as Error | null,
      reset: vi.fn(),
    },
  };
});

vi.mock("../api/useAiConfig", () => ({ useAiConfig: h.hook }));

/** 当前注入 config（测试前置赋值——mock 闭包读取）。 */
let currentConfig: AiConfigResponse | undefined;

h.hook.mockImplementation((enabled: boolean) => {
  h.enabledLog.push(enabled);
  return {
    configQuery: {
      data: currentConfig,
      isLoading: currentConfig === undefined,
      isError: false,
      error: null,
    },
    saveMutation: h.mutation,
  };
});

/** 配置工厂（缺省=全空未配置态——服务端 GET 投影五键）。 */
function configOf(extra?: Partial<AiConfigResponse>): AiConfigResponse {
  return {
    base_url: "",
    model: "",
    has_api_key: false,
    llm_timeout_s: 120,
    configured: false,
    ...extra,
  };
}

/** 渲染区块至 HTML 串（enabled 门控默认 true——Modal 开态消费口径）。 */
function renderSection(enabled = true): string {
  return renderToString(<LlmConfigSection enabled={enabled} />);
}

describe("LlmConfigSection 未配置态（F1）", () => {
  it("状态行呈现降级模式文案+表单四输入可编辑（无禁用标记）", () => {
    currentConfig = configOf();
    const html = renderSection();
    expect(html).toContain("未配置——对话运行在降级模式（仅设计类话术模板回应）");
    expect(html).toContain("✗");
    expect(html).toContain("Base URL");
    expect(html).toContain("模型名");
    expect(html).toContain("API Key");
    expect(html).toContain("超时秒");
    // 可编辑面：无真禁用属性（antd aria-disabled="false" 常驻非禁用语义——
    // 断言锁定 disabled="" 属性形态而非子串）
    expect(html).not.toContain('disabled=""');
  });

  it("加载态（config 未就绪）：保存钮禁用防误写", () => {
    currentConfig = undefined;
    const html = renderSection();
    expect(html).toContain('disabled=""');
  });
});

describe("LlmConfigSection 保存载荷（F1）", () => {
  it("buildSavePayload：未改字段原值回传+api_key 空输入不发送（防清除）", () => {
    const cfg = configOf({
      base_url: "https://old.example.com/v1",
      model: "old-model",
      has_api_key: true,
      configured: true,
    });
    const payload = buildSavePayload(cfg, {
      baseUrl: "https://old.example.com/v1",
      model: "old-model",
      apiKey: "",
      timeout: 120,
    });
    expect(payload).toEqual({
      base_url: "https://old.example.com/v1",
      model: "old-model",
      llm_timeout_s: 120,
    }); // api_key 键缺席=不改动（密钥不回显故空输入≠清除）
  });

  it("buildSavePayload：新值.trim() 后全量发送（含 api_key/timeout 覆盖）", () => {
    const cfg = configOf({ base_url: "https://old.example.com/v1", model: "old-model" });
    const payload = buildSavePayload(cfg, {
      baseUrl: "  https://new.example.com/v1  ",
      model: " new-model ",
      apiKey: " sk-new-123 ",
      timeout: 900,
    });
    expect(payload).toEqual({
      base_url: "https://new.example.com/v1",
      model: "new-model",
      api_key: "sk-new-123",
      llm_timeout_s: 900,
    });
  });

  it("buildSavePayload：清空面=base_url/model 空串（清除）+timeout 缺席", () => {
    const cfg = configOf({ base_url: "https://old.example.com/v1", model: "old-model" });
    expect(buildSavePayload(cfg, { baseUrl: "", model: "", apiKey: "", timeout: null })).toEqual(
      { base_url: "", model: "" },
    );
  });

  it("buildSavePayload：config 未加载=空载荷（禁在未知现值上盲写）", () => {
    expect(buildSavePayload(undefined, { baseUrl: "x", model: "y", apiKey: "z", timeout: 5 })).toEqual({});
  });

  it("区块消费 useAiConfig：enabled 门控直传（Modal 开态口径）", () => {
    currentConfig = configOf();
    renderSection(true);
    renderSection(false);
    expect(h.enabledLog.at(-2)).toBe(true);
    expect(h.enabledLog.at(-1)).toBe(false);
  });
});

describe("LlmConfigSection 回填口径（F1）", () => {
  it("has_api_key=true：密钥占位符「已配置（不回显）」+base_url/model/timeout 回填", () => {
    currentConfig = configOf({
      base_url: "https://cfg.example.com/v1",
      model: "cfg-model",
      has_api_key: true,
      llm_timeout_s: 300,
      configured: true,
    });
    const html = renderSection();
    expect(html).toContain("已配置（不回显）");
    expect(html).toContain('value="https://cfg.example.com/v1"');
    expect(html).toContain('value="cfg-model"');
    expect(html).toContain("已配置——对话将调用模型");
    expect(html).toContain("保存并生效");
  });
});
