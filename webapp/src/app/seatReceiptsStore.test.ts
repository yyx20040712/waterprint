/**
 * 席位操作回执 store 测试（M7 批 2026-10-07——F.1 骨架：确认队列+撤销栈+
 * 禁区前置拒止+深度 cap；node 面纯 store 直测，零 DOM 依赖）。
 *
 * 输入:  useSeatReceiptsStore（zustand store——enqueueReceipt/confirmReceipt/
 *        rejectReceipt/revokeReceipt 四 API+receipts 状态）
 * 输出:  断言组：①白名单三 kind（settings-param/tree-select/canvas-select）
 *        enqueue 成功入列（ok:true+id 非空+pending 态）；②禁区两 kind
 *        （canvas-geometry/contract）前置拒止（ok:false reason=
 *        forbidden-zone）不入列；③id 唯一性+最新置顶（倒序）；④状态机
 *        迁移（pending→executed/rejected；executed→revoked）；⑤非法迁移
 *        no-op（终态/越序/未知 id）；⑥深度 cap 50（满员丢最旧）。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  useSeatReceiptsStore,
  type SeatReceipt,
  type SeatReceiptTargetKind,
} from "./seatReceiptsStore";

/** 白名单/禁区 kind 组（P-B2 准绳：可写面=Settings 参数面+树/画布选择；禁区=画布几何+契约层）。 */
const WRITABLE_KINDS: SeatReceiptTargetKind[] = [
  "settings-param",
  "tree-select",
  "canvas-select",
];
const FORBIDDEN_KINDS: SeatReceiptTargetKind[] = ["canvas-geometry", "contract"];

/** enqueue 便捷面（kind+序号——action/target.name 可区分）。 */
function enqueueOf(kind: SeatReceiptTargetKind, index: number) {
  return useSeatReceiptsStore.getState().enqueueReceipt({
    action: `操作-${index}`,
    target: { kind, name: `目标-${index}` },
    paramDiff: `参数差异-${index}`,
  });
}

/** 现态快照（断言面）。 */
function receipts(): SeatReceipt[] {
  return useSeatReceiptsStore.getState().receipts;
}

beforeEach(() => {
  useSeatReceiptsStore.setState({ receipts: [] });
});

describe("enqueueReceipt：白名单入列+禁区前置拒止", () => {
  it("白名单三 kind 均入列：ok:true+id 非空+pending 态+字段全承袭", () => {
    for (const [index, kind] of WRITABLE_KINDS.entries()) {
      const outcome = enqueueOf(kind, index);
      expect(outcome).toEqual({ ok: true, id: expect.any(String) });
      if (!outcome.ok) {
        throw new Error("unreachable——上断言已保 ok:true");
      }
      expect(outcome.id.length).toBeGreaterThan(0);
    }
    const list = receipts();
    expect(list).toHaveLength(3);
    for (const [index, kind] of WRITABLE_KINDS.entries()) {
      // 倒序：最新在前——后入列的在前位
      const entry = list[2 - index] as SeatReceipt;
      expect(entry.action).toBe(`操作-${index}`);
      expect(entry.target).toEqual({ kind, name: `目标-${index}` });
      expect(entry.paramDiff).toBe(`参数差异-${index}`);
      expect(entry.state).toBe("pending");
      expect(entry.createdAt).toBeGreaterThanOrEqual(0);
    }
  });

  it("禁区两 kind 前置拒止：ok:false reason=forbidden-zone 且不入列（返回值式拒止不抛）", () => {
    for (const [index, kind] of FORBIDDEN_KINDS.entries()) {
      expect(() => enqueueOf(kind, index)).not.toThrow();
      expect(enqueueOf(kind, index)).toEqual({ ok: false, reason: "forbidden-zone" });
    }
    expect(receipts()).toHaveLength(0);
  });

  it("禁区拒止不挤占白名单：先白名单入列再禁区拒止——列表不变", () => {
    enqueueOf("settings-param", 0);
    const before = receipts().length;
    enqueueOf("canvas-geometry", 1);
    enqueueOf("contract", 2);
    expect(receipts()).toHaveLength(before);
  });

  it("id 唯一性：两次 enqueue 的 id 不同", () => {
    const first = enqueueOf("settings-param", 0);
    const second = enqueueOf("settings-param", 1);
    if (!first.ok || !second.ok) {
      throw new Error("白名单 enqueue 应 ok:true");
    }
    expect(first.id).not.toBe(second.id);
  });

  it("crypto 缺位兜底防碰撞：Date.now 路径两次 enqueue id 不同且互不为前缀", () => {
    // stub 面仅本用例（finally 恢复——不渗后续用例）
    vi.stubGlobal("crypto", undefined);
    try {
      const first = enqueueOf("settings-param", 0);
      const second = enqueueOf("settings-param", 1);
      if (!first.ok || !second.ok) {
        throw new Error("白名单 enqueue 应 ok:true");
      }
      expect(first.id).not.toBe(second.id);
      expect(first.id.startsWith(second.id)).toBe(false);
      expect(second.id.startsWith(first.id)).toBe(false);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("最新置顶：第二条在前位（页面倒序呈现的数据面）", () => {
    enqueueOf("settings-param", 1);
    enqueueOf("settings-param", 2);
    const list = receipts();
    expect((list[0] as SeatReceipt).action).toBe("操作-2");
    expect((list[1] as SeatReceipt).action).toBe("操作-1");
  });
});

describe("状态机迁移（确认队列+撤销栈——非法迁移一律 no-op）", () => {
  it("confirmReceipt：pending→executed", () => {
    const outcome = enqueueOf("settings-param", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().confirmReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("executed");
  });

  it("confirmReceipt 非法迁移 no-op：executed 再 confirm 仍 executed；未知 id 列表不变", () => {
    const outcome = enqueueOf("settings-param", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().confirmReceipt(outcome.id);
    useSeatReceiptsStore.getState().confirmReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("executed");
    const before = receipts();
    useSeatReceiptsStore.getState().confirmReceipt("no-such-id");
    expect(receipts()).toEqual(before);
  });

  it("rejectReceipt：pending→rejected", () => {
    const outcome = enqueueOf("tree-select", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().rejectReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("rejected");
  });

  it("rejectReceipt 越序 no-op：executed→rejected 不迁（确认后不可改判被拒）", () => {
    const outcome = enqueueOf("tree-select", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().confirmReceipt(outcome.id);
    useSeatReceiptsStore.getState().rejectReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("executed");
  });

  it("revokeReceipt：executed→revoked（已撤销栈语义）", () => {
    const outcome = enqueueOf("canvas-select", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().confirmReceipt(outcome.id);
    useSeatReceiptsStore.getState().revokeReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("revoked");
  });

  it("revokeReceipt 越序 no-op：pending→revoked 不迁（未确认无可撤销）", () => {
    const outcome = enqueueOf("canvas-select", 0);
    if (!outcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().revokeReceipt(outcome.id);
    expect((receipts()[0] as SeatReceipt).state).toBe("pending");
  });

  it("终态封口：revoked/rejected 对 confirm/reject/revoke 全 no-op", () => {
    const revokedOutcome = enqueueOf("settings-param", 0);
    const rejectedOutcome = enqueueOf("settings-param", 1);
    if (!revokedOutcome.ok || !rejectedOutcome.ok) {
      throw new Error("unreachable");
    }
    useSeatReceiptsStore.getState().confirmReceipt(revokedOutcome.id);
    useSeatReceiptsStore.getState().revokeReceipt(revokedOutcome.id);
    useSeatReceiptsStore.getState().rejectReceipt(rejectedOutcome.id);
    for (const id of [revokedOutcome.id, rejectedOutcome.id]) {
      useSeatReceiptsStore.getState().confirmReceipt(id);
      useSeatReceiptsStore.getState().rejectReceipt(id);
      useSeatReceiptsStore.getState().revokeReceipt(id);
    }
    const states = receipts().map((entry) => entry.state);
    expect(states).toContain("revoked");
    expect(states).toContain("rejected");
  });
});

describe("撤销栈深度 cap（M7 裁量=50：满员丢最旧）", () => {
  it("第 51 条入列丢最旧：长度恒 50+队首=最新+最旧 id 不在列", () => {
    const ids: string[] = [];
    for (let index = 0; index < 51; index += 1) {
      const outcome = enqueueOf("settings-param", index);
      if (!outcome.ok) {
        throw new Error("unreachable");
      }
      ids.push(outcome.id);
    }
    const list = receipts();
    expect(list).toHaveLength(50);
    expect((list[0] as SeatReceipt).action).toBe("操作-50");
    expect(list.some((entry) => entry.id === ids[0])).toBe(false);
    expect(list.some((entry) => entry.id === ids[1])).toBe(true);
  });
});
