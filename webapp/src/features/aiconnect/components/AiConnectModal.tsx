/**
 * AI 接入 Modal（AI2 批）：状态四项检查列表+一键接入+重启引导。
 *
 * 输入:  open/onClose（App.tsx 顶栏 AiConnectButton 入口受控）
 * 输出:  Modal 壳（AiConnectPanel 承载——useAiConnection open 门控取数：
 *        四项 ✓/✗ 列表+ready 横幅+一键接入按钮+成功引导/失败展示；F1 批
 *        起下挂 LlmConfigSection——聊天模型（LLM）三键配置区）
 *
 * 规格说明（AI2 批 2026-09-13；F1 批 2026-09-25 增挂）：
 *   - 壳/面板分离：Modal 门户层（title/open/onClose+关闭重置）+纯展示
 *     AiConnectPanel（props 注入查询/mutation 句柄——面板测试零 mock 直
 *     构结果对象；antd Modal SSR 门户零内容，渲染面测试在面板层）；
 *   - 状态四项=服务端 GET /api/ai/connection 直投；沙箱行=路径信息行
 *     （推导恒在场——✓ 语义，非存在性检查）；
 *   - 一键接入=POST /api/ai/connection/setup（mutate 零参——写目标服务端
 *     推导）；成功态引导文案冻结（重启 Zcode 会话即连+21 个 wp_* 工具）；
 *     失败面=WaterprintApiError.message 透出（uv 缺失 400 detail 面向用户）；
 *   - F1（语义误导 R2 修复）：四项区块标题改「Zcode 工具接入（MCP）——
 *     与下方聊天模型相互独立」——四项绿=MCP 接入态与聊天 LLM 零交集的
 *     显式声明；下方挂 LlmConfigSection（enabled=open 同门控）。
 */
import { Alert, Button, Modal, Typography } from "antd";
import { useEffect } from "react";
import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";

import type { AiConnectionSetupResult, AiConnectionStatus } from "../../../shared/api/generated/model";

import { useAiConnection } from "../api/useAiConnection";

import { LlmConfigSection } from "./LlmConfigSection";

export type AiStatusQuery = UseQueryResult<AiConnectionStatus, unknown>;
export type AiSetupMutation = UseMutationResult<AiConnectionSetupResult, unknown, void, unknown>;

const SUCCESS_GUIDE =
  "配置已写入——重启 ZCode 会话（或在 waterprint 目录新开会话）即自动连接，21 个 wp_* 工具可用";

/** 错误文案提取（WaterprintApiError extends Error——instanceof 面真源）。 */
function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error ?? "未知错误");
}

/** 单行状态项：标签+✓/✗ 标记+补充详情（路径/缺失提示）。 */
function StatusRow({ label, ok, detail }: { label: string; ok: boolean; detail: string | null }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "baseline",
        gap: 8,
        padding: "4px 0",
        borderBottom: "1px solid var(--wp-border)",
      }}
    >
      <Typography.Text
        strong
        style={{ color: ok ? "var(--wp-success)" : "var(--wp-error)", width: 14 }}
      >
        {ok ? "✓" : "✗"}
      </Typography.Text>
      <Typography.Text style={{ flex: "none" }}>{label}</Typography.Text>
      {detail === null ? null : (
        <Typography.Text
          type="secondary"
          style={{ fontSize: 12, wordBreak: "break-all", fontFamily: "var(--wp-font-mono)" }}
        >
          {detail}
        </Typography.Text>
      )}
    </div>
  );
}

/**
 * 接入面板（纯展示）：四项 ✓/✗ 列表+ready 横幅+一键接入+成功引导/失败面。
 *
 * 输入:  statusQuery/setupMutation（useAiConnection 句柄 props 注入）
 * 输出:  状态渲染三态（加载/错误/四项）+动作面（一键接入按钮+关闭）
 */
export function AiConnectPanel({
  statusQuery,
  setupMutation,
  onClose,
}: {
  statusQuery: AiStatusQuery;
  setupMutation: AiSetupMutation;
  onClose: () => void;
}) {
  const status = statusQuery.data ?? null;
  return (
    <>
      <Typography.Title level={5} style={{ marginTop: 0 }}>
        Zcode 工具接入（MCP）——与下方聊天模型相互独立
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
        检查本机 waterprint-mcp（MCP server）接入条件；一键接入会把 waterprint
        server 条目写入两份工作区配置（.zcode/config.json，merge 保留既有条目）。
      </Typography.Paragraph>
      {setupMutation.isSuccess ? (
        <Alert type="success" showIcon message={SUCCESS_GUIDE} style={{ marginBottom: 12 }} />
      ) : null}
      {setupMutation.isError ? (
        <Alert
          type="error"
          showIcon
          message={`接入失败：${errorText(setupMutation.error)}`}
          style={{ marginBottom: 12 }}
        />
      ) : null}
      {statusQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message={`状态检查失败：${errorText(statusQuery.error)}`}
          style={{ marginBottom: 12 }}
        />
      ) : null}
      {statusQuery.isLoading || status === null ? (
        <Typography.Text type="secondary">状态检查中…</Typography.Text>
      ) : (
        <>
          {status.ready ? (
            <Alert
              type="success"
              showIcon
              message="已接入：waterprint-mcp 就绪（ZCode 会话内 21 个 wp_* 工具可用）"
              style={{ marginBottom: 8 }}
            />
          ) : null}
          <StatusRow
            label="工作区配置已写入（.zcode/config.json）"
            ok={status.config_written}
            detail={status.config_paths.join("；")}
          />
          <StatusRow
            label="agent 模块可导入（waterprint_agent）"
            ok={status.agent_importable}
            detail={null}
          />
          <StatusRow
            label="uv 可执行文件在 PATH"
            ok={status.uv_path !== null}
            detail={status.uv_path ?? "未找到（安装 uv 后重试）"}
          />
          <StatusRow label="AI 沙箱根目录" ok={true} detail={status.sandbox_root} />
        </>
      )}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
        <Button
          type="primary"
          loading={setupMutation.isPending}
          disabled={setupMutation.isPending}
          onClick={() => setupMutation.mutate()}
        >
          一键接入
        </Button>
        <Button onClick={onClose}>关闭</Button>
      </div>
    </>
  );
}

export function AiConnectModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { statusQuery, setupMutation } = useAiConnection(open);
  const resetSetup = setupMutation.reset;

  // 关闭即重置 mutation 态（下次打开干净引导面）
  useEffect(() => {
    if (!open) {
      resetSetup();
    }
  }, [open, resetSetup]);

  return (
    <Modal title="AI 接入" open={open} onCancel={onClose} footer={null}>
      <AiConnectPanel statusQuery={statusQuery} setupMutation={setupMutation} onClose={onClose} />
      <LlmConfigSection enabled={open} />
    </Modal>
  );
}
