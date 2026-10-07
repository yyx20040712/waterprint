/**
 * AI 席位容器（M7 批 2026-10-07——右列席位三分页实装：对话｜任务｜回执，
 * P-B2 定案序；M1 占位空态容器退役）。
 *
 * 输入:  onOpenAiConnect（App 开 AiConnectModal——单一 Modal 面不变）+
 *        window.location.search（一次性初始化——席位初值解析）+
 *        useAiConnection(true)（席位常驻语义：挂载即一次状态查询；与 Modal
 *        同键缓存共享，setup 后 invalidate 翻绿即时反映）
 * 输出:  席位容器（根 wp-seat）：头行（「AI 席位」标题+连接徽标
 *        wp-seat-conn+三分页 Segmented size=small 受控）+体（三页
 *        mount-on-first-activation+display 切换保持——studioPane 先例泛化：
 *        activated 集随到访增长，已挂载页 display:none 保持态；对话页会话态/
 *        任务页任务轨跨切页保持）
 *
 * 规格说明（brief D1；mapping-2b4 §A M7 行+§B 边缘语义）：
 *   - seatInitialPage 纯函数：①?task=/?enum= 深链→"task"（边缘 c 席位聚焦
 *     ——App initialTarget hasDeepLink 同口径）；②裸 tab 键==="opsdebug"
 *     →"task"（§B 副作用列「兼容层一次性切席位任务分页」——归一后槽=
 *     canvas 视图不变，席位侧效应在此落位；不改写地址栏 M1 已承，刷新
 *     幂等）；③缺省 "chat"；优先序①>②（双条件并存同归 task）；
 *   - 页态=会话内不进 URL（studioPane Segmented 先例——D3）：初始化一次性
 *     （useState 惰性初值——后续 URL 变更不联动）；TASK_EVENT 运行期不自动
 *     切页（边缘 a「席位不自动切」限定语——席位只呈现不抢焦点）；
 *   - 连接徽标判据：statusQuery.data?.ready===true→Tag success「已接入」；
 *     否则 Tag default「未接入」（loading/失败=「未接入」诚实降级不猜因
 *     ——自裁申报项③）；徽标 onClick=onOpenAiConnect；
 *   - Segmented options 常量单源（studioPane 先例）；嵌套 antd Tabs 禁用面
 *     （GC-08）不触；三分页定序=对话｜任务｜回执（P-B2 定案序）；
 *   - 样式经 var() 消费既有 token（tokens-2b3 §F 纪律——新色值禁自造）。
 */
import { useEffect, useState } from "react";
import { Segmented, Tag, Typography } from "antd";

import { ChatSeat } from "../features/ai_chat/components/ChatSeat";
import { useAiConnection } from "../features/aiconnect/api/useAiConnection";
import { parseEnumParam, parseTaskParam } from "./projectParam";
import { SeatReceipts } from "./seatReceipts";
import { SeatTaskPage } from "./seatTaskPage";

/** 席位分页三值（P-B2 定案序：对话｜任务｜回执）。 */
export type SeatPage = "chat" | "task" | "receipts";

/** 席位初值解析（纯函数——brief D1 三分支：深链→task/opsdebug 兼容→task/
 *  缺省 chat；优先序①>②）。 */
export function seatInitialPage(search: string): SeatPage {
  if (parseTaskParam(search) !== null || parseEnumParam(search) !== null) {
    return "task";
  }
  // 裸读 tab 键：parseTabParam 已把 opsdebug 归一为 canvas（槽值域面），
  // 席位侧效应须在归一前判原始值（§B 副作用列落位）
  return new URLSearchParams(search).get("tab") === "opsdebug" ? "task" : "chat";
}

/** 三分页 Segmented 选项（常量单源——studioPane 先例）。 */
const SEAT_PAGE_OPTIONS: { label: string; value: SeatPage }[] = [
  { label: "对话", value: "chat" },
  { label: "任务", value: "task" },
  { label: "回执", value: "receipts" },
];

export function AiSeat({ onOpenAiConnect }: { onOpenAiConnect: () => void }) {
  // 页态=会话内不进 URL；初始化一次性（后续 URL 变更不联动——TASK_EVENT
  // 运行期不自动切页）
  const [page, setPage] = useState<SeatPage>(() =>
    seatInitialPage(window.location.search),
  );
  // mount-on-first-activation：到访集合只增不减（display 切换保持态）
  const [activated, setActivated] = useState<ReadonlySet<SeatPage>>(
    () => new Set([page]),
  );
  useEffect(() => {
    setActivated((prev) => (prev.has(page) ? prev : new Set(prev).add(page)));
  }, [page]);

  // 席位常驻语义：连接状态查询恒启用（与 AiConnectModal 同键缓存共享）
  const { statusQuery } = useAiConnection(true);
  // 查询失败但缓存留旧 ready:true=未接入（失败=未接入字面口径——诚实降级）
  const ready = statusQuery.data?.ready === true && !statusQuery.isError;

  return (
    <div
      data-testid="wp-seat"
      style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}
    >
      <div
        style={{
          flex: "none",
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 10px",
          borderBottom: "1px solid var(--wp-border-2)",
        }}
      >
        <Typography.Text strong>AI 席位</Typography.Text>
        <Tag
          data-testid="wp-seat-conn"
          color={ready ? "success" : "default"}
          onClick={onOpenAiConnect}
          style={{ cursor: "pointer", marginInlineEnd: 0 }}
        >
          {ready ? "已接入" : "未接入"}
        </Tag>
        <Segmented
          size="small"
          value={page}
          options={SEAT_PAGE_OPTIONS}
          onChange={(value) => setPage(value as SeatPage)}
          style={{ marginLeft: "auto" }}
        />
      </div>
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        {activated.has("chat") ? (
          <div
            style={
              page === "chat"
                ? { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }
                : { display: "none" }
            }
          >
            <ChatSeat />
          </div>
        ) : null}
        {activated.has("task") ? (
          <div
            style={
              page === "task"
                ? { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }
                : { display: "none" }
            }
          >
            <SeatTaskPage />
          </div>
        ) : null}
        {activated.has("receipts") ? (
          <div
            style={
              page === "receipts"
                ? { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }
                : { display: "none" }
            }
          >
            <SeatReceipts />
          </div>
        ) : null}
      </div>
    </div>
  );
}
