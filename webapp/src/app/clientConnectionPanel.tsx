/**
 * 客户端模式连接面板（联机架构第六批 2026-11-19——稿 connection.html
 * 客户端段：远程地址+token 录入+测试连接+版本握手结果；自
 * runtimeSettingsModal 拆件〔行数预算，reportExports 先例〕）。
 *
 * 输入:  本地 state（地址/token/探测结果）+performHandshake（探测）+
 *        getApiToken/setApiToken（token 既有 Bearer 通道）+setRemoteServer/
 *        clearRemoteServer（远程档案）+useClientConnectionStore（已连接态
 *        呈现：phase/serverMeta/mismatch）
 * 输出:  未连接态=录入面（地址+token+测试连接）+握手结果卡（四态）+
 *        连接钮（ok 才可达）；已连接态=当前连接呈现（host+phase+版本/
 *        mismatch 明细）+重新测试/断开连接钮
 *
 * 规格说明（联机第六批任务书——稿 connection.html 客户端面板段）：
 *   - 测试连接=performHandshake 三步（meta 豁免面→token 探针→版本比对
 *     ——remoteHandshake 单源）；结果卡四态：握手完成（ok 绿）/无法完成
 *     版本握手（unreachable）/服务器拒绝当前凭据（token_invalid）/
 *     API 契约不一致·数据包不匹配（version_mismatch——双方版本并陈）；
 *   - 连接=写 token（既有 waterprint.api_token 键）+写远程档案
 *     （waterprint.remote_server）+整页 reload（客户端模式全量重装配：
 *     URL 键/缓存键语义不变仅 API origin 变——本地缓存零混入）；
 *   - 断开=清远程档案+reload；token 保留（单一槽位——本地态若需不同
 *     token 由既有 TokenSettingsModal 自愈回路处理，v1 瑕疵记档）；
 *   - 归一化拒绝：地址非法（normalizeRemoteBaseUrl null）测试连接不
 *     发起（表单内联提示，非探测结果）；
 *   - 三主题零字面色：自建样式全走 var(--wp-*) 轴（global.css 客户端
 *     连接段），antd 面经 ConfigProvider 换肤。
 */
import { Button, Input, Typography } from "antd";
import { useEffect, useState } from "react";

import {
  clearApiToken,
  getApiToken,
  setApiToken,
} from "../shared/api/token";
import {
  clearRemoteServer,
  getRemoteBaseUrl,
  normalizeRemoteBaseUrl,
  setRemoteServer,
} from "../shared/api/remoteBase";
import {
  performHandshake,
  type HandshakeOutcome,
} from "./remoteHandshake";
import { useClientConnectionStore } from "./clientConnectionStore";
import { remoteHostLabel } from "./shellV4/runtimeFace";

/** 握手结果卡徽标+文案（四态——稿 connection.html state 段）。 */
const OUTCOME_BADGE: Record<HandshakeOutcome["status"], string> = {
  ok: "握手完成",
  unreachable: "握手失败",
  token_invalid: "token 失效",
  version_mismatch: "版本不匹配",
};

const OUTCOME_BADGE_CLASS: Record<HandshakeOutcome["status"], string> = {
  ok: "ok",
  unreachable: "error",
  token_invalid: "error",
  version_mismatch: "error",
};

const OUTCOME_TEXT: Record<HandshakeOutcome["status"], string> = {
  ok: "版本一致——可以连接该服务器。",
  unreachable: "无法完成版本握手：检查服务器地址、网络连接和服务端运行状态。",
  token_invalid: "服务器拒绝当前凭据：请重新录入有效配对 token。",
  version_mismatch: "远程契约需要对齐：更新客户端或服务端到兼容版本后再连接。",
};

export function ClientConnectionPanel() {
  const phase = useClientConnectionStore((state) => state.phase);
  const remoteBase = useClientConnectionStore((state) => state.remoteBase);
  const serverMeta = useClientConnectionStore((state) => state.serverMeta);
  const mismatch = useClientConnectionStore((state) => state.mismatch);

  const [address, setAddress] = useState("");
  const [token, setToken] = useState("");
  const [testing, setTesting] = useState(false);
  const [outcome, setOutcome] = useState<HandshakeOutcome | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const connected = phase !== "local";

  // 开面板/连接态变化时同步现值（地址预填当前档案；token 预填运行期真相）
  useEffect(() => {
    const current = getRemoteBaseUrl();
    if (current !== null) {
      setAddress(current);
    }
    setToken(getApiToken() ?? "");
    setOutcome(null);
    setFormError(null);
  }, [connected]);

  /** 测试连接（归一化先行——非法地址不发探测）。 */
  const handleTest = async () => {
    const normalized = normalizeRemoteBaseUrl(address);
    if (normalized === null) {
      setFormError("地址须为 http(s)://主机[:端口] 形态（不含路径）。");
      setOutcome(null);
      return;
    }
    setFormError(null);
    setTesting(true);
    try {
      setOutcome(await performHandshake(normalized, token));
    } finally {
      setTesting(false);
    }
  };

  /** 连接（token+远程档案落盘→整页 reload 重装配客户端模式）。 */
  const handleConnect = () => {
    const normalized = normalizeRemoteBaseUrl(address);
    if (normalized === null || outcome?.status !== "ok") {
      return; // 非 ok 结果不连接（阻断逻辑正门）
    }
    const trimmed = token.trim();
    if (trimmed === "") {
      clearApiToken();
    } else {
      setApiToken(trimmed);
    }
    setRemoteServer(normalized);
    window.location.reload();
  };

  /** 断开（清远程档案→reload 回本地模式；token 单槽保留——瑕疵记档）。 */
  const handleDisconnect = () => {
    clearRemoteServer();
    window.location.reload();
  };

  return (
    <div data-testid="wp-v4-client-panel">
      <div className="wp-v4-runtime-row">
        <div>
          <strong>客户端模式</strong>
          <div className="wp-v4-runtime-sub">
            本地只运行界面，不起计算引擎——项目、计算与产物全部经下列
            远程服务器 API。
          </div>
        </div>
        <span
          className={`wp-v4-badge${connected ? " water" : ""}`}
          data-testid="wp-v4-client-mode-badge"
        >
          {connected ? "已连接" : "未连接"}
        </span>
      </div>
      {connected && remoteBase !== null ? (
        <>
          <div className="wp-v4-pair-card" data-testid="wp-v4-client-current">
            <div className="wp-v4-pair-head">
              <div>
                <h4>当前连接</h4>
                <span className="wp-v4-runtime-sub">
                  客户端模式下项目列表只显示该服务器的项目
                </span>
              </div>
              <span className="wp-v4-badge water">
                {remoteHostLabel(remoteBase)}
              </span>
            </div>
            <div className="wp-v4-pair-line">
              <span className="wp-v4-runtime-mono">{remoteBase}</span>
              <Button size="small" onClick={() => void handleTest()}>
                重新测试
              </Button>
            </div>
            {serverMeta !== null ? (
              <div className="wp-v4-pair-line">
                <span className="wp-v4-runtime-sub">
                  服务器版本 {serverMeta.app_version}
                </span>
                <span className="wp-v4-runtime-mono">
                  {serverMeta.data_version}
                </span>
              </div>
            ) : null}
            {mismatch !== null ? (
              <Typography.Paragraph
                type="warning"
                style={{ marginBottom: 0 }}
                data-testid="wp-v4-client-mismatch-detail"
              >
                {mismatch.kind === "api" ? "API 契约" : "数据包版本"}不一致
                ——本客户端期望 {mismatch.expected}，服务器为 {mismatch.actual}
                ；项目与计算入口已锁定。
              </Typography.Paragraph>
            ) : null}
          </div>
          <Button
            danger
            onClick={handleDisconnect}
            data-testid="wp-v4-client-disconnect"
          >
            断开连接（返回本地模式）
          </Button>
        </>
      ) : (
        <>
          <div className="wp-v4-client-form">
            <label className="wp-v4-client-field" htmlFor="wp-v4-client-address">
              远程服务器地址
              <Input
                id="wp-v4-client-address"
                className="wp-v4-client-input"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                data-testid="wp-v4-client-address"
              />
            </label>
            <label className="wp-v4-client-field" htmlFor="wp-v4-client-token">
              配对 token（服务端配对卡分发）
              <Input.Password
                id="wp-v4-client-token"
                className="wp-v4-client-input"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                autoComplete="new-password"
                data-testid="wp-v4-client-token"
              />
            </label>
          </div>
          {formError !== null ? (
            <Typography.Text type="danger" data-testid="wp-v4-client-form-error">
              {formError}
            </Typography.Text>
          ) : null}
          <Button
            type="primary"
            loading={testing}
            onClick={() => void handleTest()}
            data-testid="wp-v4-client-test"
            style={{ marginTop: 8 }}
          >
            测试连接
          </Button>
          {outcome !== null ? (
            <div className="wp-v4-pair-card" data-testid="wp-v4-client-result">
              <div className="wp-v4-pair-head">
                <div>
                  <h4>版本握手结果</h4>
                  <span className="wp-v4-runtime-sub">{OUTCOME_TEXT[outcome.status]}</span>
                </div>
                <span
                  className={`wp-v4-badge ${OUTCOME_BADGE_CLASS[outcome.status]}`}
                  data-testid="wp-v4-client-result-badge"
                >
                  {OUTCOME_BADGE[outcome.status]}
                </span>
              </div>
              {outcome.status === "ok" || outcome.status === "version_mismatch" ? (
                <>
                  <div className="wp-v4-pair-line">
                    <span className="wp-v4-runtime-mono">服务器版本</span>
                    <span className="wp-v4-runtime-mono">
                      {outcome.meta.app_version}
                    </span>
                  </div>
                  <div className="wp-v4-pair-line">
                    <span className="wp-v4-runtime-mono">数据包版本</span>
                    <span className="wp-v4-runtime-mono">
                      {outcome.status === "version_mismatch" &&
                      outcome.check.kind === "data"
                        ? `${outcome.check.expected} ↔ ${outcome.check.actual}`
                        : outcome.meta.data_version}
                    </span>
                  </div>
                  <div className="wp-v4-pair-line">
                    <span className="wp-v4-runtime-mono">API 契约</span>
                    <span className="wp-v4-runtime-mono">
                      {outcome.status === "version_mismatch" &&
                      outcome.check.kind === "api"
                        ? `期望 ${outcome.check.expected} ↔ 服务器 ${outcome.check.actual}`
                        : "一致"}
                    </span>
                  </div>
                </>
              ) : null}
              {outcome.status === "ok" ? (
                <Button
                  type="primary"
                  onClick={handleConnect}
                  data-testid="wp-v4-client-connect"
                >
                  连接远程服务器
                </Button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
