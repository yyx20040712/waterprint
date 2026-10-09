/**
 * 失焦连跳提交节流 hook（B2 P3 V10——ParamForm 失焦通道消费；M1 缺省
 * 门关零消费=零行为变）。
 *
 * 输入:  fire（提交通道——payload 取尾发时点最新草稿）+mirror（草稿镜像
 *        同步——onChange→render 后 ref 恒新）
 * 输出:  useThrottledCommit → { schedule, mirror }——leading 即发+trailing
 *        最新合并（commitThrottle 单源；卸载 flush——R1 W-V10：挂尾
 *        立即发不静默丢）
 */
import { useEffect, useRef } from "react";

import {
  createCommitThrottle,
  type CommitThrottle,
} from "../lib/commitThrottle";

export function useThrottledCommit<P>(fire: (payload: P) => void) {
  const payloadRef = useRef<P | null>(null);
  const fireRef = useRef(fire);
  fireRef.current = fire;
  const throttleRef = useRef<CommitThrottle | null>(null);

  // 卸载面（R1 W-V10）：flush 挂尾立即发（「失焦即提交」三式承诺窗内不
  // 损——旧 cancel 静默丢；陈旧提交风险经 payload 时点最新镜像消解）
  useEffect(() => () => throttleRef.current?.flush(), []);

  return {
    /** 草稿镜像同步（effect 面——payload 取时点最新）。 */
    mirror(payload: P) {
      payloadRef.current = payload;
    },
    /** 提交通道（latest 非 null=同步覆盖镜像——归一值即时面）。 */
    schedule(latest: P | null) {
      if (throttleRef.current === null) {
        throttleRef.current = createCommitThrottle();
      }
      if (latest !== null) {
        payloadRef.current = latest;
      }
      const payload = payloadRef.current;
      throttleRef.current.schedule(() => {
        if (payload !== null) {
          fireRef.current(payload);
        }
      });
    },
  };
}
