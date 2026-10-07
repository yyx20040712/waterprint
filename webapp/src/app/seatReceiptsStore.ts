/**
 * 席位操作回执 store（M7 批 2026-10-07——F.1 骨架：确认队列+撤销栈+禁区
 * 前置拒止；mapping-2b4 §F.1 P-B2 准绳四要素的结构承载，zustand——
 * paramsStore 先例）。
 *
 * 输入:  enqueueReceipt({action,target,paramDiff})（target.kind 五值——
 *        前三=settings-param/tree-select/canvas-select 可写面白名单，后两
 *        =canvas-geometry/contract 禁区）+confirmReceipt/rejectReceipt/
 *        revokeReceipt(id)
 * 输出:  useSeatReceiptsStore（receipts 倒序列表〔最新在前〕+四 API；
 *        enqueue=返回值式拒止不抛：禁区 {ok:false,reason:"forbidden-zone"}
 *        不入列；状态机 pending→executed｜rejected、executed→revoked，
 *        非法迁移〔终态/越序/未知 id〕一律 no-op）
 *
 * 规格说明（mapping-2b4 §F.1；brief D4）：
 *   - 类型面含全五 kind 值以承载外部 AI 载荷的运行期校验，白名单在
 *     enqueue 前置拒止（禁区两面=禁直写画布几何与契约层）；
 *   - 确认迁移 pending→executed 的真执行体挂载位：写通道随后续批接入
 *     （本批骨架迁移语义即准绳四要素之「写操作经确认队列」的结构承载，
 *     本处注释即挂载占位注记）；
 *   - 撤销栈深度=50（M7 实装裁量——mapping §F.1 末行授权）：enqueue 满
 *     员丢最旧；
 *   - id=crypto.randomUUID()（缺位环境 Date.now 兜底）；createdAt=
 *     Date.now()（页面时间戳呈现源）。
 */
import { create } from "zustand";

/** 回执目标面五值（P-B2：前三个=可写面白名单；后两个=禁区）。 */
export type SeatReceiptTargetKind =
  | "settings-param"
  | "tree-select"
  | "canvas-select"
  | "canvas-geometry"
  | "contract";

/** 回执条目（F.1 字段骨架：操作摘要/状态机/时间戳）。 */
export type SeatReceipt = {
  id: string;
  action: string;
  target: { kind: SeatReceiptTargetKind; name: string };
  paramDiff: string;
  state: "pending" | "executed" | "rejected" | "revoked";
  createdAt: number;
};

/** 可写面白名单（禁区两面经差集前置拒止）。 */
const WRITABLE_KINDS: ReadonlySet<SeatReceiptTargetKind> = new Set([
  "settings-param",
  "tree-select",
  "canvas-select",
]);

/** 撤销栈深度（M7 裁量=50——enqueue 满员丢最旧）。 */
const RECEIPTS_MAX = 50;

/** 兜底路径自增序号（同毫秒两次入列防碰撞——模块级）。 */
let seq = 0;

/** 回执 id 生成（crypto.randomUUID——缺位环境 Date.now+序号兜底）。 */
function newReceiptId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `receipt-${Date.now()}-${++seq}`;
}

/** 入列载荷（状态机起点恒 pending；id/createdAt 归 store 生成）。 */
export type SeatReceiptInput = {
  action: string;
  target: { kind: SeatReceiptTargetKind; name: string };
  paramDiff: string;
};

type SeatReceiptsState = {
  receipts: SeatReceipt[];
  enqueueReceipt: (
    input: SeatReceiptInput,
  ) => { ok: true; id: string } | { ok: false; reason: "forbidden-zone" };
  confirmReceipt: (id: string) => void;
  rejectReceipt: (id: string) => void;
  revokeReceipt: (id: string) => void;
};

/** 单条状态迁移（合法迁移改写，非法迁移原样返回——no-op 单源）。 */
function transition(
  receipt: SeatReceipt,
  id: string,
  from: SeatReceipt["state"],
  to: SeatReceipt["state"],
): SeatReceipt {
  return receipt.id === id && receipt.state === from ? { ...receipt, state: to } : receipt;
}

export const useSeatReceiptsStore = create<SeatReceiptsState>((set) => ({
  receipts: [],
  enqueueReceipt: (input) => {
    // 禁区前置拒止（返回值式不抛——不入列；类型面五值承载运行期校验）
    if (!WRITABLE_KINDS.has(input.target.kind)) {
      return { ok: false, reason: "forbidden-zone" };
    }
    const id = newReceiptId();
    set((state) => {
      const entry: SeatReceipt = {
        id,
        action: input.action,
        target: input.target,
        paramDiff: input.paramDiff,
        state: "pending",
        createdAt: Date.now(),
      };
      const next = [entry, ...state.receipts];
      // 深度 cap：满员丢最旧（倒序列表尾=最旧）
      return { receipts: next.length > RECEIPTS_MAX ? next.slice(0, RECEIPTS_MAX) : next };
    });
    return { ok: true, id };
  },
  // pending→executed：真执行体挂载位=此处注释占位（写通道随后续批接入——
  // 本批骨架迁移语义即「写操作经确认队列」的结构承载）
  confirmReceipt: (id) =>
    set((state) => ({
      receipts: state.receipts.map((receipt) => transition(receipt, id, "pending", "executed")),
    })),
  rejectReceipt: (id) =>
    set((state) => ({
      receipts: state.receipts.map((receipt) => transition(receipt, id, "pending", "rejected")),
    })),
  // executed→revoked：已撤销栈语义（越序 pending 不可撤销）
  revokeReceipt: (id) =>
    set((state) => ({
      receipts: state.receipts.map((receipt) => transition(receipt, id, "executed", "revoked")),
    })),
}));
