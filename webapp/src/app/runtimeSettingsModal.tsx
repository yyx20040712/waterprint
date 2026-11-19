/**
 * 运行方式与联机设置 Modal（联机架构第五批 2026-11-19——稿 connection.
 * html 服务端态：两级开关说明+服务端配对卡〔本机地址/配对 token/局域网
 * 发现提示〕+绑定切换诚实降级+客户端模式下一批占位说明）。
 *
 * 输入:  open（Modal 开态——状态栏运行标识/工作台运行方式卡两入口，
 *        shellV4 单 state 承载）+onClose 关闭回调；useGetRuntimeApi
 *        RuntimeGet（/api/runtime——角色/绑定/地址/token reveal 面）+
 *        getDesktopBridge（b7 桌面壳桥探测——缺席走诚实降级）
 * 输出:  Modal（标题「运行方式与联机」：联机开关〔服务端模式〕+当前
 *        绑定展示+服务端配对卡+客户端模式下一批说明+关闭钮）
 *
 * 规格说明（第五批任务书——用户裁决 Minecraft 式开关模型）：
 *   - 两级开关模型说明：联机关=单机（本地引擎 127.0.0.1）；联机开+
 *     服务端=本地引擎照常+0.0.0.0 绑定+token 强制+局域网可连；
 *   - 绑定切换本体属 desktop 壳（b7 批）：桥缺席（window.pywebview
 *     不存在）时切换控件诚实降级为「当前绑定展示+桌面端可切换」提示
 *     （禁用非隐藏）；桥在场时调用 setNetworkRole（b7 实装——签名
 *     desktopBridge.ts 本批冻结）；
 *   - token 展示门=服务端 token_reveal 字段（仅回环请求者非 null）：
 *     null=非本机连接不展示（诚实提示）；空串=未配置 token 警示；
 *   - 客户端模式（连远程 API）是下一批——本面只作说明行不设入口；
 *   - 三主题零字面色：自建样式全走 var(--wp-*) 轴（global.css pairing
 *     卡段），antd 面经 ConfigProvider 换肤。
 */
import { Button, Modal, Switch, Typography } from "antd";
import { useState } from "react";

import { useGetRuntimeApiRuntimeGet } from "../shared/api/generated/meta/meta";
import { getDesktopBridge } from "./desktopBridge";
import { pairingAddressUrl } from "./shellV4/runtimeFace";

/** 剪贴板复制（不可用静默——非安全上下文/权限拒绝不阻断，可手动选择）。 */
async function copyText(text: string): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    }
  } catch {
    // 剪贴板不可用——不阻断（用户可手动选择复制）
  }
}

/** token 复制钮（prop 形参收窄 string——闭包内 token_reveal 联合型不穿透）。 */
function TokenCopyButton({ token }: { token: string }) {
  return (
    <Button size="small" onClick={() => void copyText(token)}>
      复制 token
    </Button>
  );
}

export function RuntimeSettingsModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const runtimeQuery = useGetRuntimeApiRuntimeGet();
  const runtime = runtimeQuery.data;
  const bridge = getDesktopBridge();
  const [switching, setSwitching] = useState(false);
  const [switchNotice, setSwitchNotice] = useState<string | null>(null);

  const isServer = runtime?.role === "server";
  const bindHost = runtime?.bind_host ?? "127.0.0.1";
  // 回环 reveal 面（null=非本机连接；空串=未配置——两空态分支文案区分）
  const revealedToken: string | null = runtime?.token_reveal ?? null;

  /** 联机开关（桥在场才可达——b7 实装；切换经壳重启生效）。 */
  const handleToggle = async (checked: boolean) => {
    if (bridge === null) {
      return;
    }
    setSwitching(true);
    try {
      const result = await bridge.setNetworkRole(
        checked ? "server" : "standalone",
      );
      setSwitchNotice(
        result.restartRequired
          ? "已请求切换运行角色——重启桌面应用后生效。"
          : "已请求切换运行角色。",
      );
    } catch {
      setSwitchNotice("切换请求失败——请在桌面端重试。");
    } finally {
      setSwitching(false);
    }
  };

  return (
    <Modal
      title="运行方式与联机"
      open={open}
      onCancel={onClose}
      width={620}
      footer={[
        <Button key="close" type="primary" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
        两级开关：联机关闭即单机模式（本地引擎与本地项目）；开启服务端后
        本地引擎照常运行，局域网客户端凭本机地址与配对 token 加入。
      </Typography.Paragraph>
      {runtimeQuery.isError ? (
        <Typography.Paragraph
          type="warning"
          style={{ marginBottom: 12 }}
          data-testid="wp-v4-runtime-read-error"
        >
          运行状态读取失败——以下按单机模式显示。
        </Typography.Paragraph>
      ) : null}
      {/* 联机开关（服务端模式）——桥缺席=禁用+诚实降级提示 */}
      <div className="wp-v4-runtime-row">
        <div>
          <strong>联机开关（服务端模式）</strong>
          <div className="wp-v4-runtime-sub">
            {isServer
              ? "已开启——本机作为服务端，局域网客户端可配对连接"
              : "已关闭——单机运行，不向局域网开放项目"}
          </div>
        </div>
        <Switch
          checked={isServer}
          disabled={bridge === null}
          loading={switching}
          onChange={handleToggle}
          aria-label="联机开关（服务端模式）"
          data-testid="wp-v4-runtime-switch"
        />
      </div>
      {bridge === null ? (
        <Typography.Paragraph
          type="secondary"
          style={{ marginBottom: 12 }}
          data-testid="wp-v4-runtime-bridge-note"
        >
          当前绑定：{bindHost}
          {isServer ? "（对外）" : "（仅本机）"}。绑定切换（127.0.0.1 ↔
          0.0.0.0，重启生效）在桌面端提供——浏览器打开的页面不切换服务器绑定。
        </Typography.Paragraph>
      ) : null}
      {switchNotice !== null ? (
        <Typography.Paragraph style={{ marginBottom: 12 }}>
          {switchNotice}
        </Typography.Paragraph>
      ) : null}
      {/* 服务端配对卡（稿 connection.html pairing-card 段——仅 server 态） */}
      {isServer && runtime !== undefined ? (
        <div className="wp-v4-pair-card" data-testid="wp-v4-runtime-pairing">
          <div className="wp-v4-pair-head">
            <div>
              <h4>本机地址</h4>
              <span className="wp-v4-runtime-sub">
                客户端在 WaterPrint 中输入同一地址
              </span>
            </div>
            <span className="wp-v4-badge ok">监听中</span>
          </div>
          {runtime.lan_addresses.length > 0 ? (
            runtime.lan_addresses.map((address) => (
              <div key={address} className="wp-v4-pair-line">
                <code className="wp-v4-pair-code">
                  {pairingAddressUrl(address)}
                </code>
                <Button size="small" onClick={() => void copyText(pairingAddressUrl(address))}>
                  复制地址
                </Button>
              </div>
            ))
          ) : (
            <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
              未发现局域网地址——客户端无法经地址直连（检查网络连接；
              本机可用 {pairingAddressUrl("127.0.0.1")} 调试）。
            </Typography.Paragraph>
          )}
          <div className="wp-v4-divider" />
          <div className="wp-v4-pair-head">
            <div>
              <h4>配对 token</h4>
              <span className="wp-v4-runtime-sub">
                分发给加入的客户端（服务端重启或重新生成前有效）
              </span>
            </div>
            <span className="wp-v4-badge accent">主动配对</span>
          </div>
          {revealedToken !== null && revealedToken !== "" ? (
            <div className="wp-v4-token-value" data-testid="wp-v4-runtime-token">
              <code>{revealedToken}</code>
              <TokenCopyButton token={revealedToken} />
            </div>
          ) : revealedToken === null ? (
            <Typography.Paragraph
              type="secondary"
              style={{ marginBottom: 8 }}
              data-testid="wp-v4-runtime-token-hidden"
            >
              token 仅在本机（回环连接）可见——当前页面非本机回环连接，
              不展示。
            </Typography.Paragraph>
          ) : (
            <Typography.Paragraph type="warning" style={{ marginBottom: 8 }}>
              服务端未配置 token（对外绑定必须配置——见部署环境变量
              WATERPRINT_API_TOKEN）。
            </Typography.Paragraph>
          )}
          <Typography.Paragraph
            type="secondary"
            style={{ marginBottom: 0, marginTop: 8 }}
          >
            局域网客户端输入上述地址与配对 token 即可加入；自动发现服务端
            的能力后续批提供。
          </Typography.Paragraph>
        </div>
      ) : null}
      {/* 客户端模式（下一批）——诚实说明行非虚假入口 */}
      <div className="wp-v4-runtime-row" data-testid="wp-v4-runtime-client-next">
        <div>
          <strong>客户端模式</strong>
          <div className="wp-v4-runtime-sub">
            连接远程服务器（本地不起引擎，项目与计算经远程 API）——下一批
            提供
          </div>
        </div>
        <span className="wp-v4-badge">下一批</span>
      </div>
      {runtime !== undefined ? (
        <Typography.Paragraph
          type="secondary"
          style={{ marginBottom: 0, marginTop: 4 }}
        >
          服务器绑定：{runtime.bind_host}
          （角色由绑定地址决定，无独立配置项）。
        </Typography.Paragraph>
      ) : null}
    </Modal>
  );
}
