/**
 * 三维首帧门（FE-4 批 2026-09-30；2A4 批 2026-10-05 UF-56 超时降级）：
 * 数据就绪→Canvas 首帧渲染空窗的用户反馈+超时退出路径。
 *
 * 输入:  无外部数据（纯 view 态门——Scene 挂钩 Canvas 生命周期：信号源=
 *        Canvas 内 FirstFrameSignal 的 useFrame 首帧回调）
 * 输出:  ①createFirstFrameGate 纯核（闭包状态单元：isDone/isTimedOut/
 *        signal/armTimeout/disarmTimeout/subscribe——signal 与超时到达各
 *        幂等恰通知一次；首帧先到=清窗取消降级）；②useFirstFrameGate 薄
 *        适配（useSyncExternalStore——返回 [done, timedOut, signal] 三元，
 *        effect 挂/卸计时器）；③FirstFrameOverlay 薄壳（role="status" 居中
 *        Spin+「正在构建三维场景…」，absolute 覆盖 Canvas 区，首帧即随
 *        done 卸载）；④FirstFrameTimeoutPanel 薄壳（UF-56：role="alert"
 *        超时降级面板+重试钮）；⑤FirstFrameSignal 薄壳（Canvas 内挂载，
 *        useFrame 首帧回调一次触发 onFirstFrame——ref 守卫+signal 幂等
 *        双保险，每帧重入零副作用）
 *
 * 规格说明（brief-FE-20260930 P4；2A4 brief D1/UF-56）：
 *   - 「数据就绪→首帧」空窗=FE-4 修的目标面：Scene 数据请求期「场景加载
 *     中…」既有文案不动，本门只覆盖 scene 就绪分支到 Canvas 首帧渲染的
 *     视觉空窗（WebGL 上下文创建+首帧绘制耗时用户可感）；
 *   - UF-56 超时降级（渲染循环死锁无 React 可捕错误——ErrorBoundary 路弃）：
 *     WebGL 上下文创建失败或 useFrame 永不触发时，10s 超时翻 timedOut 出
 *     降级面板（Scene 卸载 Canvas 子树释放坏 GL 上下文；重试=attempt 复位
 *     →cell 重建→子树重挂天然重建）；超时后 signal 到达=done 仍翻 true
 *     （cell 状态诚实独立，消费面 Scene timedOut 先判属优先级分工）；
 *   - W1 回炉（2A4 R1）：窗起点=scene 就绪——hook 增 enabled 参（Scene 喂
 *     sceneReady），effect 守卫 !enabled 零计时器（取数期/错误态零副作用；
 *     取数>10s 数据到达即误报「不支持 WebGL」病根收口）；enabled 翻真=
 *     arm 新窗（就绪→首帧窗语义成立）；
 *   - FIRST_FRAME_TIMEOUT_MS=10_000：FE-20260930 门二探针基线 overlay 寿命
 *     363~439ms（SwiftShader 无头）——20×+ 余量；慢设备假阳性防线（值单点
 *     可调，重试钮=假阳性自愈路径）；面板文案秒数由常量派生（R3——禁
 *     字面双写）；面板 minHeight=240（R4——Canvas 塌缩过渡缓和）；
 *   - 状态单源=纯核闭包（非 React state 直持——useFrame 回调在 R3F 渲染
 *     循环内触发，经 cell.signal→订阅通知→useSyncExternalStore 收口为
 *     Scene 重渲染，跨 Canvas 内外两 React 根安全）；
 *   - 幂等契约（测试锚）：signal 首调翻 done 且通知订阅者恰一次，重复
 *     调用早退——useFrame 每帧重入与 StrictMode 双挂载均零副作用；超时
 *     到达对偶（timedOut 翻 true 恰通知一次）；armTimeout 重挂窗=
 *     clearTimeout+set 新窗（StrictMode 双 effect/重挂幂等安全，done=true
 *     早退 no-op）；SSR 面 server 不跑 effect=零计时器；
 *   - FirstFrameSignal/FirstFrameOverlay/FirstFrameTimeoutPanel=薄壳不测
 *     裁量沿 app 层惯例（文案/role 属用户可见契约入测试断言面；行为面
 *     归纯核测试+门二无头探针 DOM 断言）。
 */
import { useEffect, useMemo, useRef, useSyncExternalStore } from "react";
import { Button, Spin } from "antd";
import { useFrame } from "@react-three/fiber";

/** 首帧超时窗（ms）——探针基线 363~439ms×20+ 余量；值单点可调（A1）。 */
export const FIRST_FRAME_TIMEOUT_MS = 10_000;

/** 首帧门纯核（闭包状态单元——node 可直测，React 零依赖）。 */
export type FirstFrameGateCell = {
  isDone: () => boolean;
  isTimedOut: () => boolean;
  signal: () => void;
  armTimeout: (ms: number) => void;
  disarmTimeout: () => void;
  subscribe: (listener: () => void) => () => void;
};

/** 纯核工厂：done/timedOut 初 false；signal 首调翻 done 且恰通知一次
 *  （幂等）+清窗（首帧先到=取消降级）；armTimeout 到点翻 timedOut 恰通知
 *  一次（幂等旗标——signal 对偶结构；重挂窗=clear+set 新窗，done 时 no-op）；
 *  超时后 signal 到达 done 仍翻 true（状态诚实独立）。 */
export function createFirstFrameGate(): FirstFrameGateCell {
  let done = false;
  let timedOut = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  const listeners = new Set<() => void>();
  const clearWindow = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  };
  return {
    isDone: () => done,
    isTimedOut: () => timedOut,
    signal: () => {
      if (done) {
        return; // 幂等早退——重复回调零再通知（防每帧重入抖动）
      }
      done = true;
      clearWindow(); // 首帧先到=取消降级（UF-56）
      listeners.forEach((notify) => notify());
    },
    armTimeout: (ms) => {
      if (done) {
        return; // 首帧已收口——零降级面 no-op
      }
      clearWindow(); // 重挂窗=clear+set 新窗（StrictMode 双 effect 幂等安全）
      timer = setTimeout(() => {
        timer = null;
        if (timedOut) {
          return; // 幂等旗标——恰通知一次（signal 对偶结构）
        }
        timedOut = true;
        listeners.forEach((notify) => notify());
      }, ms);
    },
    disarmTimeout: clearWindow,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}

/** hook 返回形（Scene 消费：done 驱动 overlay 卸载、timedOut 驱动超时
 *  面板替代 Canvas 块、signal 喂 FirstFrameSignal）。 */
export type FirstFrameGate = readonly [boolean, boolean, () => void];

/** 薄适配：[done, timedOut, signal]——done/timedOut 变更经订阅通知驱动重
 *  渲染；effect 挂/卸计时器（SSR 面 server 不跑 effect=零计时器）。
 *  R1 F1（d1-W3/k2-W2 升格 B 面）：resetKey 变更→useMemo 重建 cell——
 *  done/timedOut 归 false、新首帧窗口重新有 overlay（Scene 不随 projectId
 *  重挂是门一已核事实，复位经本参数承载；undefined=永不复位=原行为）。
 *  W1 回炉：enabled=false 零计时器（窗=就绪→首帧——Scene 喂 sceneReady；
 *  翻真=arm 新窗，取数期/错误态零副作用）。 */
export function useFirstFrameGate(resetKey?: unknown, enabled = true): FirstFrameGate {
  const cell = useMemo(createFirstFrameGate, [resetKey]);
  const done = useSyncExternalStore(cell.subscribe, cell.isDone, cell.isDone);
  const timedOut = useSyncExternalStore(
    cell.subscribe,
    cell.isTimedOut,
    cell.isTimedOut,
  );
  useEffect(() => {
    if (!enabled) {
      return; // 未就绪零计时器——窗起点=scene 就绪（W1 回炉）
    }
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    return () => cell.disarmTimeout();
  }, [cell, enabled]);
  return [done, timedOut, cell.signal];
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

/** 超时降级面板（UF-56 薄壳：role="alert"+重试钮——onRetry 驱动 Scene
 *  attempt+1 复位=cell 重建+Canvas 子树重挂天然重建 GL 上下文；文案秒数
 *  由常量派生〔R3〕；minHeight 缓和 Canvas 塌缩视觉跳变〔R4〕）。 */
export function FirstFrameTimeoutPanel({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      role="alert"
      style={{
        padding: 16,
        minHeight: 240,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        alignItems: "flex-start",
      }}
    >
      <span>
        三维渲染初始化未在 {FIRST_FRAME_TIMEOUT_MS / 1000} 秒内完成——设备可能不支持
        WebGL 或资源紧张。可重试；若持续失败，请检查浏览器硬件加速设置。
      </span>
      <Button onClick={onRetry}>重试</Button>
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
