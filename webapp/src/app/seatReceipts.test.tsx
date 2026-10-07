/**
 * @vitest-environment jsdom
 *
 * 席位操作回执分页测试（M7 批 2026-10-07——F.1 骨架页面：倒序卡片列表+
 * 空态引导+状态 Tag+动作钮迁移；store 直注（enqueue/confirm/reject/revoke
 * 经 store API 驱动——零网络零 mock 面））。
 *
 * 输入:  SeatReceipts（store 驱动纯展示面；每用例 reset receipts 后经
 *        useSeatReceiptsStore.getState() 注入态）
 * 输出:  断言组：①空态文案+wp-seat-receipts 根；②卡片倒序（最新前）+
 *        摘要行（action/target.name/paramDiff）；③pending 卡双钮（确认/
 *        拒绝）+「待确认」Tag；④确认→「已执行」+撤销钮换场；⑤拒绝→
 *        「被拒」无钮；⑥撤销→「已撤销」无钮；⑦时间戳在场。
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { SeatReceipts } from "./seatReceipts";
import { useSeatReceiptsStore, type SeatReceiptTargetKind } from "./seatReceiptsStore";

/** 经 store API 入列（返回 id 供卡片锚定位）。 */
function enqueue(kind: SeatReceiptTargetKind, action: string): string {
  const outcome = useSeatReceiptsStore.getState().enqueueReceipt({
    action,
    target: { kind, name: `${action}-目标` },
    paramDiff: `${action}-参数差异`,
  });
  if (!outcome.ok) {
    throw new Error(`enqueue 应 ok:true（${action}）`);
  }
  return outcome.id;
}

beforeEach(() => {
  useSeatReceiptsStore.setState({ receipts: [] });
});
afterEach(cleanup);

describe("SeatReceipts 空态与卡片渲染", () => {
  it("空态文案在场+体根 wp-seat-receipts 在场", () => {
    render(<SeatReceipts />);
    expect(screen.getByTestId("wp-seat-receipts")).toBeTruthy();
    expect(
      screen.getByText("暂无操作回执——AI 写操作经确认队列派发，回执与撤销在此呈现"),
    ).toBeTruthy();
  });

  it("卡片倒序：后入列的最新卡在前+摘要行三件在场（action/target.name/paramDiff）", () => {
    const firstId = enqueue("settings-param", "调整参数");
    const secondId = enqueue("tree-select", "选中单元");
    const view = render(<SeatReceipts />);
    const cards = view.container.querySelectorAll('[data-testid^="wp-seat-receipt-"]');
    expect(cards).toHaveLength(2);
    expect(screen.getByTestId(`wp-seat-receipt-${secondId}`)).toBeTruthy();
    expect(screen.getByTestId(`wp-seat-receipt-${firstId}`)).toBeTruthy();
    // 倒序：首卡=最新（选中单元）
    expect(cards[0] as HTMLElement).toBe(screen.getByTestId(`wp-seat-receipt-${secondId}`));
    expect(screen.getByText("调整参数")).toBeTruthy();
    expect(screen.getByText("选中单元-目标")).toBeTruthy();
    expect(screen.getByText("调整参数-参数差异")).toBeTruthy();
  });

  it("时间戳在场（createdAt → toLocaleTimeString 呈现）", () => {
    enqueue("settings-param", "调整参数");
    render(<SeatReceipts />);
    expect(screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/).length).toBeGreaterThan(0);
  });
});

describe("状态 Tag 与动作钮迁移（确认队列+撤销栈）", () => {
  it("pending 卡：「待确认」Tag+「确认」「拒绝」双钮在场", () => {
    const id = enqueue("settings-param", "调整参数");
    render(<SeatReceipts />);
    const card = screen.getByTestId(`wp-seat-receipt-${id}`);
    expect(within(card).getByText("待确认")).toBeTruthy();
    expect(within(card).getByRole("button", { name: /确\s*认/ })).toBeTruthy();
    expect(within(card).getByRole("button", { name: /拒\s*绝/ })).toBeTruthy();
  });

  it("确认迁移：点「确认」→「已执行」Tag+「撤销」钮换场（确认/拒绝退场）", () => {
    const id = enqueue("settings-param", "调整参数");
    render(<SeatReceipts />);
    fireEvent.click(screen.getByRole("button", { name: /确\s*认/ }));
    const card = screen.getByTestId(`wp-seat-receipt-${id}`);
    expect(within(card).getByText("已执行")).toBeTruthy();
    expect(within(card).getByRole("button", { name: /撤\s*销/ })).toBeTruthy();
    expect(within(card).queryByRole("button", { name: /确\s*认/ })).toBeNull();
    expect(within(card).queryByRole("button", { name: /拒\s*绝/ })).toBeNull();
  });

  it("拒绝迁移：点「拒绝」→「被拒」Tag+无动作钮", () => {
    const id = enqueue("tree-select", "选中单元");
    render(<SeatReceipts />);
    fireEvent.click(screen.getByRole("button", { name: /拒\s*绝/ }));
    const card = screen.getByTestId(`wp-seat-receipt-${id}`);
    expect(within(card).getByText("被拒")).toBeTruthy();
    expect(within(card).queryByRole("button", { name: /确\s*认/ })).toBeNull();
    expect(within(card).queryByRole("button", { name: /拒\s*绝/ })).toBeNull();
    expect(within(card).queryByRole("button", { name: /撤\s*销/ })).toBeNull();
  });

  it("撤销迁移：executed 点「撤销」→「已撤销」Tag+无动作钮", () => {
    const id = enqueue("canvas-select", "画布选中");
    useSeatReceiptsStore.getState().confirmReceipt(id);
    render(<SeatReceipts />);
    fireEvent.click(screen.getByRole("button", { name: /撤\s*销/ }));
    const card = screen.getByTestId(`wp-seat-receipt-${id}`);
    expect(within(card).getByText("已撤销")).toBeTruthy();
    expect(within(card).queryByRole("button", { name: /撤\s*销/ })).toBeNull();
  });

  it("多卡独立迁移：确认首卡不影响次卡 pending 态", () => {
    const firstId = enqueue("settings-param", "调整参数");
    const secondId = enqueue("settings-param", "再调整");
    render(<SeatReceipts />);
    fireEvent.click(within(screen.getByTestId(`wp-seat-receipt-${firstId}`)).getByRole("button", { name: /确\s*认/ }));
    expect(within(screen.getByTestId(`wp-seat-receipt-${firstId}`)).getByText("已执行")).toBeTruthy();
    const secondCard = screen.getByTestId(`wp-seat-receipt-${secondId}`);
    expect(within(secondCard).getByText("待确认")).toBeTruthy();
    expect(within(secondCard).getByRole("button", { name: /确\s*认/ })).toBeTruthy();
  });
});
