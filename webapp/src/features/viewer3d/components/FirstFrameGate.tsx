/**
 * 三维首帧门（FE-4 批 2026-09-30）：数据就绪→Canvas 首帧渲染空窗的用户反馈。
 *
 * 输入:  无外部数据（纯 view 态门——Scene 挂钩 Canvas 生命周期：信号源=
 *        Canvas 内 FirstFrameSignal 的 useFrame 首帧回调）
 * 输出:  ①createFirstFrameGate 纯核（闭包状态单元：isDone/signal/subscribe
 *        ——signal 幂等，重复调用零再通知）；②useFirstFrameGate 薄适配
 *        （useSyncExternalStore——返回 [done, signal]）；③FirstFrameOverlay
 *        薄壳（role="status" 居中 Spin+「正在构建三维场景…」，absolute 覆盖
 *        Canvas 区，首帧即随 done 卸载）；④FirstFrameSignal 薄壳（Canvas
 *        内挂载，useFrame 首帧回调一次触发 onFirstFrame——ref 守卫+signal
 *        幂等双保险，每帧重入零副作用）
 *
 * 规格说明（brief-FE-20260930 P4；Scene.tsx 净增 ≤10 行配套件）：
 *   - 「数据就绪→首帧」空窗=本件修的目标面：Scene 数据请求期「场景加载
 *     中…」既有文案不动，本门只覆盖 scene 就绪分支到 Canvas 首帧渲染的
 *     视觉空窗（WebGL 上下文创建+首帧绘制耗时用户可感）；
 *   - 状态单源=纯核闭包（非 React state 直持——useFrame 回调在 R3F 渲染
 *     循环内触发，经 cell.signal→订阅通知→useSyncExternalStore 收口为
 *     Scene 重渲染，跨 Canvas 内外两 React 根安全）；
 *   - 幂等契约（测试锚）：signal 首调翻 done 且通知订阅者恰一次，重复
 *     调用早退——useFrame 每帧重入与 StrictMode 双挂载均零副作用；
 *   - FirstFrameSignal/FirstFrameOverlay=薄壳不测裁量（app 层惯例——
 *     行为面归纯核测试+门二无头探针 DOM 断言：role="status" 节点在
 *     Canvas 挂载后存在、首帧后消失）。
 */
import { useRef, useMemo, useSyncExternalStore } from "react";
import { Spin } from "antd";
import { useFrame } from "@react-three/fiber";

/** 首帧门纯核（闭包状态单元——node 可直测，React 零依赖）。 */
export type FirstFrameGateCell = {
  isDone: () => boolean;
  signal: () => void;
  subscribe: (listener: () => void) => () => void;
};

/** 纯核工厂：done 初 false；signal 首调翻 true 并通知订阅者恰一次（幂等）。 */
export function createFirstFrameGate(): FirstFrameGateCell {
  let done = false;
  const listeners = new Set<() => void>();
  return {
    isDone: () => done,
    signal: () => {
      if (done) {
        return; // 幂等早退——重复回调零再通知（防每帧重入抖动）
      }
      done = true;
      listeners.forEach((notify) => notify());
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/** hook 返回形（Scene 消费：done 驱动 overlay 卸载，signal 喂 FirstFrameSignal）。 */
export type FirstFrameGate = readonly [boolean, () => void];

/** 薄适配：[done, signal]——done 变更经订阅通知驱动重渲染。
 *  R1 F1（d1-W3/k2-W2 升格 B 面）：resetKey 变更→useMemo 重建 cell——
 *  done 归 false、新首帧窗口重新有 overlay（Scene 不随 projectId 重挂
 *  是门一已核事实，复位经本参数承载；undefined=永不复位=原行为）。 */
export function useFirstFrameGate(resetKey?: unknown): FirstFrameGate {
  const cell = useMemo(createFirstFrameGate, [resetKey]);
  const done = useSyncExternalStore(cell.subscribe, cell.isDone, cell.isDone);
  return [done, cell.signal];
}

/** 首帧反馈 overlay（薄壳：absolute 覆盖 Canvas 区——父容器 relative 由
 *  Scene 装配；首帧即随 done 翻转卸载，无退场动画面）。 */
export function FirstFrameOverlay() {
  return (
    <div
      role="status"
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        background: "rgba(11, 21, 38, 0.92)",
      }}
    >
      <Spin />
      <span style={{ fontSize: 13, color: "var(--wp-text-2, #cfe6ff)" }}>
        正在构建三维场景…
      </span>
    </div>
  );
}

/** 首帧信号（薄壳：Canvas 内挂载——useFrame 首帧回调一次触发；ref 守卫
 *  为 key 域内一次性[R2 F1'/B1：消费方以 key={projectId} 重挂归零 fired]
 *  +signal 幂等兜底，返回 null 零渲染面）。 */
export function FirstFrameSignal({ onFirstFrame }: { onFirstFrame: () => void }) {
  const fired = useRef(false);
  useFrame(() => {
    if (fired.current) {
      return;
    }
    fired.current = true;
    onFirstFrame();
  });
  return null;
}
