/**
 * projectId 跨面板共享 hook（UX1 S3——URL ?project= 单一真相的订阅面）。
 *
 * 输入:  URL ?project= 参数（初值经 parseProjectParam+normalizeProjectId
 *        既有纯函数——函数零改动）+PROJECT_EVENT 事件（写方 setter 写后
 *        派发）
 * 输出:  [projectId, setProjectId]（读方解构首元消费；写方两 pane
 *        [canvas/viewer3d] setter 消费——回写 URL+派发事件一步收敛）
 *
 * 规格说明（UX1 批 6b 段八 D1；TASK_EVENT 事件桥 S12/AUDIT2 同机制）：
 *   - S3 缺陷面：六 pane 原各持 useState 初值快照（惰性初始化仅首挂载
 *     执行一次）——切项目（URL ?project= 变更）后已挂载面板恒旧值；
 *     本 hook 内部 useEffect 监听 PROJECT_EVENT 重读 location.search
 *     更新态（同值早退），React Query 键随 projectId 态变自动 refetch
 *     （key-driven——零手动 invalidate）；
 *   - setter=withProjectParam+replaceState+写后派发 dispatch
 *     （PROJECT_EVENT——写方自身监听经 URL 重读同值早退不扰动）；
 *     canvas/viewer3d 既有 W1/W2 三行回写代码收敛进本 hook；
 *   - popstate 不挂（replaceState 无历史条目——挂了恒不触发=死码）；
 *   - 薄壳不测裁量（简报 D1 记档）：app 层零测试惯例+jsdom 零新依赖
 *     红线——纯函数面（parse/with/normalize）已在 projectParam.test
 *     锁定，事件桥浏览器行为面归终裁亲验；
 *   - 不动 ParamForm task 写入面（分层禁令维持——task 传播已有
 *     TASK_EVENT）。
 */
import { useCallback, useEffect, useState } from "react";

import { PROJECT_EVENT } from "../shared/events";
import {
  normalizeProjectId,
  parseProjectParam,
  withProjectParam,
} from "./projectParam";

/** projectId 共享态（读写双元组——读方 [id]、写方 [id, setter] 按需解构）。 */
export function useProjectId(): [string | null, (value: string | null) => void] {
  const [projectId, setProjectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );

  // S3 订阅面：写方派发后重读 URL（同值早退）；卸载移除监听
  useEffect(() => {
    const onProjectParam = () => {
      const next = normalizeProjectId(parseProjectParam(window.location.search));
      setProjectId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(PROJECT_EVENT, onProjectParam);
    return () => window.removeEventListener(PROJECT_EVENT, onProjectParam);
  }, []);

  // S3 写方收敛面：态更新→回写 URL（replaceState 不留历史、不清其余
  // 参数）→写后派发（已挂载 pane 经各自 useProjectId 监听刷新）
  const setProject = useCallback((value: string | null) => {
    setProjectId(value);
    const search = withProjectParam(window.location.search, value);
    window.history.replaceState(
      null,
      "",
      search
        ? `${window.location.pathname}?${search}`
        : window.location.pathname,
    );
    window.dispatchEvent(new CustomEvent(PROJECT_EVENT, { detail: value }));
  }, []);

  return [projectId, setProject];
}
