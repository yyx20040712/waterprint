/**
 * 聊天模型接入（LLM）配置区（F1 批 2026-09-25）：三键+超时表单与状态行。
 *
 * 输入:  enabled（Modal 开态门控——useAiConfig 查询面）；GET /api/ai/config
 *        五键投影（base_url/model/timeout 回填；api_key 仅 has_api_key）
 * 输出:  保存动作（PUT /api/ai/config——载荷经 buildSavePayload 构造：
 *        api_key 空输入不发送防误清除；成功 message「已写入 .env 并即时
 *        生效（无需重启）」+draft 重同步）+状态行（configured 两态文案）
 *
 * 规格说明（F1 批；AiConnectPanel 纯展示先例+ExportButton message 口径）：
 *   - 回填口径：base_url/model/llm_timeout_s 自 GET 回显（draft 覆盖式
 *     受控——未交互=服务端真值，交互后=用户草稿）；api_key 永不回显，
 *     has_api_key=true 时密码框占位符「已配置（不回显）」；
 *   - 载荷纪律：api_key 空输入=键缺席（不改动）——密钥不回显故空≠清除；
 *     base_url/model 恒发送（回显值原样重写无副作用；清空=显式清除）；
 *     config 未加载=空载荷且保存钮禁用（未知现值上禁盲写）；
 *   - 状态行文案冻结：✓「已配置——对话将调用模型」/✗「未配置——对话
 *     运行在降级模式（仅设计类话术模板回应）」（语义误导 R2 修复面）。
 */
import { Button, Input, InputNumber, Typography, message } from "antd";
import { useState } from "react";

import type { AiConfigResponse, AiConfigUpdate } from "../../../shared/api/generated/model";

import { useAiConfig } from "../api/useAiConfig";

/** 表单草稿形态（timeout null=未指定——服务端键缺席）。 */
export interface LlmConfigFormValues {
  baseUrl: string;
  model: string;
  apiKey: string;
  timeout: number | null;
}

const SAVED_TOAST = "已写入 .env 并即时生效（无需重启）";
const CONFIGURED_LINE = "已配置——对话将调用模型";
const UNCONFIGURED_LINE = "未配置——对话运行在降级模式（仅设计类话术模板回应）";

/** 保存载荷构造（纯函数——测试直测面）：api_key 空输入不发送；未加载=空载荷。 */
export function buildSavePayload(
  config: AiConfigResponse | undefined,
  values: LlmConfigFormValues,
): AiConfigUpdate {
  if (config === undefined) {
    return {};
  }
  const payload: AiConfigUpdate = {
    base_url: values.baseUrl.trim(),
    model: values.model.trim(),
  };
  const apiKey = values.apiKey.trim();
  if (apiKey !== "") {
    payload.api_key = apiKey;
  }
  if (values.timeout !== null) {
    payload.llm_timeout_s = values.timeout;
  }
  return payload;
}

/** 行内栅格行（label 固定列+输入自适应列——面板既有 inline style 口径）。 */
function fieldRow(label: string, control: React.ReactNode) {
  return (
    <>
      <Typography.Text style={{ justifySelf: "end" }}>{label}</Typography.Text>
      <div>{control}</div>
    </>
  );
}

export function LlmConfigSection({ enabled }: { enabled: boolean }) {
  const { configQuery, saveMutation } = useAiConfig(enabled);
  const [draft, setDraft] = useState<Partial<LlmConfigFormValues>>({});
  const [messageApi, contextHolder] = message.useMessage();
  const config = configQuery.data ?? null;
  const values: LlmConfigFormValues = {
    baseUrl: draft.baseUrl ?? config?.base_url ?? "",
    model: draft.model ?? config?.model ?? "",
    apiKey: draft.apiKey ?? "", // 密钥永不回显（draft 覆盖=用户本次输入）
    timeout: draft.timeout ?? config?.llm_timeout_s ?? null,
  };
  const ready = config !== null;

  /** 保存（mutate 变量={data}——orval 生成面；成功 toast+draft 重同步真值）。 */
  const save = () => {
    if (!ready) {
      return;
    }
    saveMutation.mutate(
      { data: buildSavePayload(configQuery.data, values) },
      {
        onSuccess: () => {
          messageApi.success(SAVED_TOAST);
          setDraft({});
        },
        onError: (error) => {
          messageApi.error(error instanceof Error ? error.message : "保存失败");
        },
      },
    );
  };

  return (
    <section style={{ marginTop: 24 }}>
      <Typography.Title level={5} style={{ marginTop: 0 }}>
        聊天模型接入（LLM）
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
        对话面板的模型调用配置（OpenAI 兼容端点三键）。与上方 Zcode 工具接入（MCP）
        相互独立；保存即写入服务端 .env 并即时生效，无需重启。
      </Typography.Paragraph>
      {contextHolder}
      {configQuery.isError ? (
        <Typography.Text type="danger">
          配置读取失败：{configQuery.error instanceof Error ? configQuery.error.message : "未知错误"}
        </Typography.Text>
      ) : null}
      {!ready ? (
        <Typography.Text type="secondary">配置读取中…</Typography.Text>
      ) : (
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
          <Typography.Text
            strong
            style={{ color: config?.configured ? "var(--wp-success)" : "var(--wp-error)", width: 14 }}
          >
            {config?.configured ? "✓" : "✗"}
          </Typography.Text>
          <Typography.Text>
            {config?.configured ? CONFIGURED_LINE : UNCONFIGURED_LINE}
          </Typography.Text>
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "88px 1fr",
          gap: "8px 12px",
          alignItems: "center",
        }}
      >
        {fieldRow(
          "Base URL",
          <Input
            value={values.baseUrl}
            onChange={(event) => setDraft({ ...draft, baseUrl: event.target.value })}
          />,
        )}
        {fieldRow(
          "模型名",
          <Input
            value={values.model}
            onChange={(event) => setDraft({ ...draft, model: event.target.value })}
          />,
        )}
        {fieldRow(
          "API Key",
          <Input.Password
            value={values.apiKey}
            onChange={(event) => setDraft({ ...draft, apiKey: event.target.value })}
            placeholder={config?.has_api_key ? "已配置（不回显）" : "未配置"}
          />,
        )}
        {fieldRow(
          "超时秒",
          <InputNumber
            style={{ width: "100%" }}
            min={5}
            max={900}
            value={values.timeout}
            onChange={(value) => setDraft({ ...draft, timeout: value })}
          />,
        )}
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
        <Button
          type="primary"
          loading={saveMutation.isPending}
          disabled={!ready || saveMutation.isPending}
          onClick={save}
        >
          保存并生效
        </Button>
      </div>
    </section>
  );
}
