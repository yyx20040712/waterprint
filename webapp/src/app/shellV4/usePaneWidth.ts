/**
 * v4 侧栏拖宽 hook（v2-20261015 笔1 自 designZone 61-203 提取——单侧栏
 * 宽度状态+document 级拖拽会话+localStorage 宽度记忆单源；语义逐条照抄
 * 样板：常挂监听/onUp 不摘监听/终值=onMove 记录值直读/持久写在 updater 外）。
 *
 * 输入:  config（key=localStorage 键/fallback=缺省宽/min~max=钳位域/
 *        side=left|right——left 宽度=startWidth+delta、right=startWidth−delta）
 * 输出:  { width, onDragStart }——width=当前栏宽（style width 消费）；
 *        onDragStart=拖柄 onPointerDown 接线（仅主键启动会话+body cursor
 *        =col-resize；拖拽终值 onUp 落定持久）
 */
import { useEffect, useRef, useState } from "react";

/** 受控配置（一次配置恒定——实例化后不随渲染漂移）。 */
export interface PaneWidthConfig {
  /** localStorage 持久键（如 wp-v4-left-w）。 */
  key: string;
  /** 缺省宽（无存储/非法值/无 window 面）。 */
  fallback: number;
  /** 钳位下界。 */
  min: number;
  /** 钳位上界。 */
  max: number;
  /** 拖拽方向（left=+delta/right=−delta——delta=clientX−startX）。 */
  side: "left" | "right";
}

/** 宽度持久读（localStorage——undefined window/非法值回 fallback/越界钳域）。 */
function readWidth(key: string, fallback: number, min: number, max: number): number {
  if (typeof window === "undefined") {
    return fallback;
  }
  const raw = window.localStorage.getItem(key);
  const value = raw === null ? NaN : Number(raw);
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return Math.max(min, Math.min(max, value));
}

/** 拖拽会话（onDragStart 置位/onUp 清位——startX 起点+startWidth 会话起点宽）。 */
interface DragSession {
  startX: number;
  startWidth: number;
}

export function usePaneWidth(config: PaneWidthConfig): {
  width: number;
  onDragStart: (event: React.PointerEvent<HTMLDivElement>) => void;
} {
  const { key, fallback, min, max, side } = config;
  const [width, setWidth] = useState(() =>
    readWidth(key, fallback, min, max),
  );
  // 拖拽会话（dragRef 空转零开销——常挂面）
  const dragRef = useRef<DragSession | null>(null);
  // 拖拽会话最新宽度（onUp 终值直读源，免 setState updater 副作用——R14 制式）
  const lastWidthRef = useRef<number | null>(null);

  // 拖拽 document 级监听（pointermove/up/cancel 常挂——挂/卸对称；onUp
  // 不摘监听：常挂面语义，二次拖动即用；卸载清理含 body cursor 复位）。
  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      const drag = dragRef.current;
      if (drag === null) {
        return;
      }
      const delta = event.clientX - drag.startX;
      const next =
        side === "left"
          ? Math.max(min, Math.min(max, drag.startWidth + delta))
          : Math.max(min, Math.min(max, drag.startWidth - delta));
      lastWidthRef.current = next;
      setWidth(next);
    };
    const onUp = () => {
      const drag = dragRef.current;
      if (drag !== null) {
        dragRef.current = null;
        document.body.style.cursor = "";
        // 宽度记忆：拖放落定持久（终值=onMove 记录值，零移动回落起点；
        // cancel 态终值与视觉一致——localStorage 写在 setState 外）
        const finalWidth = lastWidthRef.current ?? drag.startWidth;
        setWidth(finalWidth);
        window.localStorage.setItem(key, String(Math.round(finalWidth)));
        
        lastWidthRef.current = null;
      }
    };
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
    document.addEventListener("pointercancel", onUp);
    return () => {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      document.removeEventListener("pointercancel", onUp);
      document.body.style.cursor = "";
    };
  }, [key, min, max, side]);

  /** 拖柄按下（仅主键——启动会话拖拽）。 */
  const onDragStart = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return;
    }
    dragRef.current = { startX: event.clientX, startWidth: width };
    document.body.style.cursor = "col-resize";
  };

  return { width, onDragStart };
}
