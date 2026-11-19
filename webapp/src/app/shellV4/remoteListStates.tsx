/**
 * 远程项目列表态卡（联机架构第六批 2026-11-19——稿 workbench-remote.html
 * 「远程列表的异常状态」state-gallery 段：离线/token 失效/版本不匹配三
 * 阻断态+在线说明行——不回退本地项目、旧列表不当可用数据）。
 *
 * 输入:  RemoteListNotice（host——在线态说明行）；RemoteListStateCard
 *        （phase 三阻断态+hostLabel+mismatch 明细+onRetry/onOpenSettings
 *        两动作）
 * 输出:  在线=说明行（只显示所连服务器项目——本地项目不混入）；阻断
 *        态=态卡（徽标显因+标题+说明+动作钮）替代表格渲染
 *
 * 规格说明（联机第六批任务书——稿 state-gallery 三卡逐字锚）：
 *   - 离线：显示来源与重试入口，不把旧列表当可用数据（无缓存规则）；
 *   - token 失效：列表操作与计算禁用，引导更新 token（连接设置）；
 *   - 版本不匹配：保留服务器来源和版本详情（期望↔服务器并陈），入口
 *     锁定防误用不兼容数据；
 *   - 三主题零字面色：var(--wp-*) 轴（global.css wp-v4-remote-state 段）。
 */
import { Button, Typography } from "antd";

import type { ClientPhase, VersionMismatch } from "../clientConnectionStore";

/** 在线说明行（稿 notice 段——host=远程主机展示名）。 */
export function RemoteListNotice({ host }: { host: string }) {
  return (
    <div className="wp-v4-remote-notice" data-testid="wp-v4-remote-notice">
      只显示 {host} 的项目。本地项目不会混入此列表，计算与导出也走同一
      远程连接。
    </div>
  );
}

/** 阻断态卡结构（三态共用——徽标/标题/说明/动作）。 */
function StateCard({
  badgeClass,
  badge,
  title,
  detail,
  action,
}: {
  badgeClass: string;
  badge: string;
  title: string;
  detail: React.ReactNode;
  action: React.ReactNode;
}) {
  return (
    <div className="wp-v4-remote-state" data-testid="wp-v4-remote-state">
      <span className={`wp-v4-badge ${badgeClass}`}>{badge}</span>
      <h4>{title}</h4>
      <Typography.Paragraph
        type="secondary"
        style={{ marginBottom: 10, fontSize: 12 }}
      >
        {detail}
      </Typography.Paragraph>
      <div>{action}</div>
    </div>
  );
}

/** 三阻断态卡（offline 重试/token_invalid 更新凭据/version_mismatch 详情）。 */
export function RemoteListStateCard({
  phase,
  hostLabel,
  mismatch,
  onRetry,
  onOpenSettings,
}: {
  phase: Exclude<ClientPhase, "local" | "online" | "connecting">;
  hostLabel: string;
  mismatch: VersionMismatch | null;
  onRetry: () => void;
  onOpenSettings: () => void;
}) {
  if (phase === "offline") {
    return (
      <StateCard
        badgeClass="warn"
        badge="离线"
        title="无法读取远程项目"
        detail={
          <>
            显示 {hostLabel} 的来源与重试入口。没有已确认的缓存规则时，
            不把旧列表当作可用数据。
          </>
        }
        action={
          <Button size="small" onClick={onRetry} data-testid="wp-v4-remote-retry">
            重试连接
          </Button>
        }
      />
    );
  }
  if (phase === "token_invalid") {
    return (
      <StateCard
        badgeClass="error"
        badge="token 失效"
        title="配对凭据需要更新"
        detail="列表操作与计算禁用——请到连接设置更新配对 token。"
        action={
          <Button
            size="small"
            onClick={onOpenSettings}
            data-testid="wp-v4-remote-update-token"
          >
            更新 token
          </Button>
        }
      />
    );
  }
  return (
    <StateCard
      badgeClass="error"
      badge="版本不匹配"
      title="远程契约需要对齐"
      detail={
        mismatch !== null ? (
          <>
            保留服务器来源（{hostLabel}）和版本详情：本客户端期望{" "}
            {mismatch.expected}，服务器为 {mismatch.actual}。项目与计算入口
            锁定，避免误用不兼容数据。
          </>
        ) : (
          <>
            服务器来源（{hostLabel}）版本与本客户端不兼容。项目与计算入口
            锁定，避免误用不兼容数据。
          </>
        )
      }
      action={
        <Button
          size="small"
          onClick={onOpenSettings}
          data-testid="wp-v4-remote-handshake-detail"
        >
          查看握手详情
        </Button>
      }
    />
  );
}
