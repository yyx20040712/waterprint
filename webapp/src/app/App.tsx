/**
 * 应用壳：v4 唯一壳挂载+Providers 组合（app 层组合面。沿革 FE3→M3→P2
 * 十页签→M1 四区→M7 席位→B1 ?ia=v4 特性壳→B7 拆件→v1-20261015 转正批：
 * 用户裁决「就是v4版本…旧壳层废弃」——?ia=v4 特性开关退役，v4=缺省
 * 唯一壳（宪法§2 方案切换=删除旧方案禁止并存）；legacy 状态编排面
 * 〔槽路由/右列拖拽/三浮层/AUTH_EVENT 监听〕随旧壳物理退役——v4 等价
 * 物在位：zoneParam zone 路由/designZone 侧栏拖宽/settingsSelfHeal 401
 * 自愈+TokenSettingsModal 恒挂载/dockBar AiConnectModal/projectsZone。
 * 拆迁史注：runCalcPolicy 自 ribbon 拆迁单源〔笔1〕；?token= 首参引导
 * 与 ShellV4 懒装载语义逐字保持）。
 *
 * 输入:  URL ?project=/（useProjectId——ShellV4 内消费）?tab=（zoneParam
 *        两级值域+LEGACY_ZONE_COMPAT 旧链归一）?task=/?enum=（深链意图）
 *        ?token=（首参引导——模块加载期剥离）
 * 输出:  Providers＞Suspense＞ShellV4（lazy 独立异步分片——then 取具名
 *        导出）；装载占位 PaneLoading
 */
import { lazy, Suspense } from "react";
import { Spin } from "antd";

import { Providers } from "./providers";
import { clearTokenParam, parseTokenParam } from "./projectParam";
import { setApiToken } from "../shared/api/token";

/** ShellV4 懒装载（then 取具名导出——v4 壳整树独立异步分片；v1 批转正
 *  后=唯一壳仍保懒装载形〔首屏 chunk 分离，行为零变承袭〕）。 */
const ShellV4 = lazy(() =>
  import("./shellV4/shellV4").then((m) => ({ default: m.ShellV4 })),
);

/** 壳装载占位（Spin 居中+统一文案，薄组件）。 */
function PaneLoading() {
  return (
    <div
      style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, minHeight: 240 }}
    >
      <Spin />
      <span>页面加载中…</span>
    </div>
  );
}

// R2-A 批 2 D2：?token= 首参引导（模块加载期最早时点，先于任何 React
// Query 请求；StrictMode 双挂载安全=幂等写+剥离；他键原序保留；G1-03
// node 面守卫跳过；G1-07 trim 空=不写仅剥离；G1-03 重拼 URL 含 hash）。
if (typeof window !== "undefined") {
  const bootstrapToken = parseTokenParam(window.location.search);
  if (bootstrapToken !== null) {
    const trimmed = bootstrapToken.trim();
    if (trimmed !== "") {
      setApiToken(trimmed);
    }
    const stripped = clearTokenParam(window.location.search);
    const searchPart = stripped ? `?${stripped}` : "";
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${searchPart}${window.location.hash}`,
    );
  }
}

export function App() {
  return (
    <Providers>
      <Suspense fallback={<PaneLoading />}>
        <ShellV4 />
      </Suspense>
    </Providers>
  );
}
