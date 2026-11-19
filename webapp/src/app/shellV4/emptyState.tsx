/**
 * 共享空/错态视觉配方（美感抛光批 #7——图纸库/说明书/AI 空错态统一：
 * 可用区整体居中+40–48px 单线 SVG 图标+14/600 标题+12–13px 短说明
 * （max-width≈360）+32px 主按钮；说明书错误态用「标题+可展开技术详情」
 * 两层，长原始错误句不再充当唯一正文）。
 *
 * 输入:  icon（40–48px 单线 SVG——消费面给 SheetGlyph 族/currentColor
 *        形）+title（14/600）+description（短说明，可选）+action（主
 *        按钮 ReactNode，可选——高 32px 由消费面钮样式承载）+detail
 *        （可展开技术详情——错误态原文透出层，可选）
 * 输出:  EmptyState 竖排居中卡（icon/title/description/action/detail
 *        五层；外层撑满可用区由消费面容器承载居中）
 */
import type { ReactNode } from "react";

export function EmptyState({
  icon,
  title,
  description,
  action,
  detail,
}: {
  /** 40–48px 单线 SVG（currentColor——随主题换肤）。 */
  icon: ReactNode;
  /** 空态标题（14px/600）。 */
  title: string;
  /** 短说明（12–13px，max-width 360——零教学性文字，白名单口径）。 */
  description?: string;
  /** 主操作（钮高 32px——消费面钮样式承载，去计算/重试类动线）。 */
  action?: ReactNode;
  /** 可展开技术详情（错误态原文——默认收起，展开才见原始错误句）。 */
  detail?: ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 10,
        padding: "40px 24px",
        textAlign: "center",
        color: "var(--wp-text-2)",
      }}
    >
      <span
        aria-hidden
        style={{ color: "var(--wp-text-3)", display: "inline-flex" }}
      >
        {icon}
      </span>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--wp-text)" }}>
        {title}
      </div>
      {description !== undefined && description !== "" ? (
        <div style={{ fontSize: 12.5, lineHeight: 1.7, maxWidth: 360 }}>
          {description}
        </div>
      ) : null}
      {action !== undefined ? <div style={{ marginTop: 2 }}>{action}</div> : null}
      {detail !== undefined ? (
        <details
          style={{
            marginTop: 4,
            maxWidth: 480,
            fontSize: 11,
            lineHeight: 1.6,
            color: "var(--wp-text-3)",
            textAlign: "left",
          }}
        >
          <summary style={{ cursor: "pointer", color: "var(--wp-text-2)" }}>
            技术详情
          </summary>
          <div
            style={{
              marginTop: 6,
              padding: "6px 10px",
              border: "1px solid var(--wp-border-2)",
              borderRadius: 4,
              background: "var(--wp-bg-deep)",
              fontFamily: "var(--wp-font-mono)",
              overflowWrap: "anywhere",
            }}
          >
            {detail}
          </div>
        </details>
      ) : null}
    </div>
  );
}
