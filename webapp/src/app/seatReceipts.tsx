/**
 * 席位操作回执分页（M7 批 2026-10-07——F.1 骨架页面：store 驱动纯展示，
 * 零网络零路由；确认队列+撤销栈的用户呈现面）。
 *
 * 输入:  useSeatReceiptsStore（receipts 倒序列表+三迁移 API）
 * 输出:  回执卡片列表（体根 wp-seat-receipts）：空态引导文案；卡片=操作
 *        摘要行（action+target.name+paramDiff）+状态 Tag（pending=default
 *        「待确认」/executed=success「已执行」/revoked=warning「已撤销」/
 *        rejected=error「被拒」——语义色三 token 复用面）+动作钮（pending
 *        →「确认」primary+「拒绝」danger；executed→「撤销」；其余态无钮）
 *        +时间戳（createdAt→toLocaleTimeString）；卡片锚
 *        wp-seat-receipt-{id}
 *
 * 规格说明（mapping-2b4 §F.1；brief D4）：
 *   - 倒序（最新在前）=store 入列序直读（页面不另排序）；
 *   - 动作钮 size=small（席位密度）；确认的真执行体=store 注释占位
 *     （写通道随后续批接入——本批页面只做状态机迁移呈现）；
 *   - 样式经 var() 消费既有 token（tokens-2b3 §F 纪律——新色值禁自造）。
 */
import { Button, Tag, Typography } from "antd";

import { useSeatReceiptsStore, type SeatReceipt } from "./seatReceiptsStore";

/** 状态 Tag 映射（语义色 R5 三 token 复用——antd 语义色名，TaskPanel 先例）。 */
const STATE_TAGS: Record<SeatReceipt["state"], { text: string; color: string }> = {
  pending: { text: "待确认", color: "default" },
  executed: { text: "已执行", color: "success" },
  revoked: { text: "已撤销", color: "warning" },
  rejected: { text: "被拒", color: "error" },
};

/** 空态引导文案（brief D4 逐字）。 */
const EMPTY_HINT = "暂无操作回执——AI 写操作经确认队列派发，回执与撤销在此呈现";

export function SeatReceipts() {
  const receipts = useSeatReceiptsStore((state) => state.receipts);
  const confirmReceipt = useSeatReceiptsStore((state) => state.confirmReceipt);
  const rejectReceipt = useSeatReceiptsStore((state) => state.rejectReceipt);
  const revokeReceipt = useSeatReceiptsStore((state) => state.revokeReceipt);

  return (
    <div
      data-testid="wp-seat-receipts"
      style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "8px 10px" }}
    >
      {receipts.length === 0 ? (
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {EMPTY_HINT}
        </Typography.Paragraph>
      ) : (
        receipts.map((receipt) => {
          const tag = STATE_TAGS[receipt.state];
          return (
            <div
              key={receipt.id}
              data-testid={`wp-seat-receipt-${receipt.id}`}
              style={{
                border: "1px solid var(--wp-border)",
                borderRadius: 6,
                padding: "6px 8px",
                marginBottom: 8,
                background: "var(--wp-bg-elevated)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <Typography.Text strong style={{ fontSize: 12 }}>
                  {receipt.action}
                </Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {receipt.target.name}
                </Typography.Text>
                <Tag color={tag.color} style={{ marginInlineEnd: 0 }}>
                  {tag.text}
                </Tag>
              </div>
              {receipt.paramDiff !== "" ? (
                <Typography.Text
                  type="secondary"
                  style={{ fontSize: 12, fontFamily: "var(--wp-font-mono)" }}
                >
                  {receipt.paramDiff}
                </Typography.Text>
              ) : null}
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                {receipt.state === "pending" ? (
                  <>
                    <Button size="small" type="primary" onClick={() => confirmReceipt(receipt.id)}>
                      确认
                    </Button>
                    <Button size="small" danger onClick={() => rejectReceipt(receipt.id)}>
                      拒绝
                    </Button>
                  </>
                ) : receipt.state === "executed" ? (
                  <Button size="small" onClick={() => revokeReceipt(receipt.id)}>
                    撤销
                  </Button>
                ) : null}
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(receipt.createdAt).toLocaleTimeString()}
                </Typography.Text>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
