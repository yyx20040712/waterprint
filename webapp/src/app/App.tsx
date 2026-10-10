/**
 * 应用壳：B-1 四区骨架布局+槽路由状态机+Providers 组合（app 层组合面；
 * M1 批 2026-10-06 四区重写——draft-ia-v3 §3 B-1 形态单源+mapping-2b4
 * 落位；M7 批 2026-10-07 AI 席位实装；M2 批 2026-10-08 Settings 增强收编
 * 〔单元详情 Drawer 退役→focusId 非空右列显 unitDetailPanel——§6 动线③〕
 * ；沿革 FE3→M3→P2 十页签→P2 解冻→M1 四区→M7 席位→M2 Settings 收编→
 * rootfix-20261008 懒实例提升〔UF-67 根治位——LazyPane lazy 实例按 load
 * WeakMap 模块级记忆化提升出渲染通道，remount 复调 ctor 消除；诊断档
 * .workflow/uf67-20261008/diag-uf67-summary.md〕；B7 收口批 2026-10-10
 * 拆件——legacy 壳 JSX 主体整块迁 legacyShell.tsx〔纯搬运零行为变〕，
 * 本件留守=?ia=v4 分支+ShellV4 懒装载+状态编排面〔hooks/setTab/拖拽
 * 回调/AUTH_EVENT 自愈监听——第五锚消费面在本件〕+LegacyShell 挂载
 * +三浮层 overlays〔Providers 包内同层渲染——主题上下文不变〕）。
 *
 * 输入:  各 feature 切片与 app 层装配件（app 层是唯一允许组合 features 的
 *        层）+URL ?project=/（useProjectId）?tab=（两级值域+兼容归一）
 *        ?task=/?enum=（深链意图）?token=（首参引导）
 * 输出:  Providers 组合：?ia=v4→ShellV4（lazy+Suspense 占位）；缺省
 *        M1 壳=LegacyShell（四区骨架渲染主体——B7 拆件迁出）+三浮层
 *        （连接设置/AI 接入/项目管理——状态编排面在本件）
 *
 * 规格说明（brief D3 逐条——状态编排面语义零变）：
 *   - 切槽唯一通道 setTab(target)：槽条/模型树/子面条/Ribbon 全经此；写
 *     URL=withTabParam replaceState（他键原序保留——UX1 D2 承袭）；mount
 *     不改写地址栏（兼容值留 URL 至下次切槽——边缘语义 a：opsdebug 不
 *     改写+全族刷新幂等）；初值=?tab= 合法〔含兼容归一〕→用之，无 ?tab=
 *     但有 ?task=/?enum=→studio.study（边缘 c 对称），缺省 canvas；
 *   - selectedUnitId 提升 App（切项目清陈旧 effect——现状 pane 本地态未
 *     清为存量瑕疵根治；树选中联动 M2）；下穿 LegacyShell→canvasPane+
 *     Settings 窗；
 *   - R2-A 批 2 沿现状：?token= 首参引导/401 自愈回路（AUTH_EVENT 监听
 *     留守本件——B7 拆件红线）/三浮层开态（M7 批 ChatPane 退役：设计
 *     对话浮层与顶栏钮随席位常驻退役）。
 */
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Spin } from "antd";

import { LegacyShell } from "./legacyShell";
import { ProjectManagerModal } from "./projectManagerModal";
import { Providers } from "./providers";
import type { SlotId, StudioSubface, TabTarget } from "./router";
import {
  clearTokenParam,
  parseEnumParam,
  parseTabParam,
  parseTaskParam,
  parseTokenParam,
  withTabParam,
} from "./projectParam";
import { TokenSettingsModal } from "./tokenSettingsModal";
import { AiConnectModal } from "../features/aiconnect/components/AiConnectModal";
import { setApiToken } from "../shared/api/token";
import { AUTH_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";
import { parseIaParam } from "./zoneParam";

/** 回炉 R2：?ia=v4 特性开关=模块加载期定值（会话内不可变前提显式化——
 *  渲染期不再随 location 读取摆动，早退分支结构不可翻转=Rules of Hooks
 *  潜伏崩点根除；缺省/测试加载时无 ?ia=v4 → 恒 false，M1 面零行为变）。 */
const IS_V4 =
  typeof window !== "undefined" &&
  parseIaParam(window.location.search) === "v4";

/** 回炉 R3：ShellV4 懒装载（then 取具名导出——缺省 M1 视图不载 v4
 *  chunk，v4 壳整树入独立异步分片）。 */
const ShellV4 = lazy(() =>
  import("./shellV4/shellV4").then((m) => ({ default: m.ShellV4 })),
);

/** 页签装载占位（FE-2——Spin 居中+统一文案，薄组件；legacy 面同形件
 *  随 B7 拆件迁 legacyShell.tsx=两份同文字面独立实例，零行为差）。 */
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

/** 右列纵向拖拽限位（D3：下限=tokens-2b3 判据 Settings 高 360；上限=
 * 视口净高〔−顶栏 48−状态栏 24〕−席位最小高 140——会话内 state 不进 URL）。 */
const SETTINGS_MIN_HEIGHT = 360;
const SETTINGS_DEFAULT_HEIGHT = 480;
const SEAT_MIN_HEIGHT = 140;
const HEADER_HEIGHT = 48;
const STATUSBAR_HEIGHT = 24;

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

/** D2 初值三级解析：?tab= 合法（含兼容归一）→用之；无 ?tab= 但有 ?task=
 *  或 ?enum=→studio.study（深链意图——边缘语义 c+enum 对称；并席位聚焦
 *  〔席位聚焦=M7 席位实装批落位——M1 席位无分页〕）；缺省 canvas；
 *  mount 不改写地址栏（边缘语义 a 统一规则）。 */
function initialTarget(): TabTarget {
  const target = parseTabParam(window.location.search);
  if (target !== null) {
    return target;
  }
  const hasDeepLink =
    parseTaskParam(window.location.search) !== null ||
    parseEnumParam(window.location.search) !== null;
  return hasDeepLink ? { slot: "studio", subface: "study" } : { slot: "canvas" };
}

export function App() {
  // B1 骨架批（2026-10-09）：?ia=v4 分支单点——v4 壳挂载（回炉 R2：IS_V4
  // 模块级定值=会话内常量，分支不可翻转；回炉 R3：ShellV4 lazy 薄壳+
  // Suspense 占位——缺省视图不载 v4 chunk）；缺省（无 ?ia=）M1 壳一行
  // 不改（本分支=唯一例外）。
  if (IS_V4) {
    return (
      <Providers>
        <Suspense fallback={<PaneLoading />}>
          <ShellV4 />
        </Suspense>
      </Providers>
    );
  }
  const [activeTarget, setActiveTarget] = useState<TabTarget>(initialTarget);
  // studio 会话子面记忆（槽条回切 studio 恒带 subface——parse 归一同构）
  const lastStudioSubface = useRef<StudioSubface>(
    activeTarget.slot === "studio" ? activeTarget.subface ?? "study" : "study",
  );
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [aiConnectOpen, setAiConnectOpen] = useState(false);
  const [managerOpen, setManagerOpen] = useState(false);
  const [projectId] = useProjectId();
  const [libraryFocusId, setLibraryFocusId] = useState<string | null>(null);
  // D7：画布选中提升 App（联动源=画布选中；树选中联动 M2）——切项目清
  // 陈旧（现状 pane 本地态未清为存量瑕疵，提升时一并根治）
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  useEffect(() => {
    setSelectedUnitId(null);
  }, [projectId]);
  // D3 右列纵向分隔拖拽（canvasPane Q8 先例：主键判定+pointercancel+
  // 卸载清理；位置会话内不进 URL）
  // 挂载期 clamp（d1-N3-lite）：小视口默认即钳界（jsdom innerHeight=768
  // 默认态不变——768−48−24−140=556>480 钳位零扰动）
  const [settingsHeight, setSettingsHeight] = useState(() =>
    Math.min(
      SETTINGS_DEFAULT_HEIGHT,
      Math.max(
        SETTINGS_MIN_HEIGHT,
        window.innerHeight - HEADER_HEIGHT - STATUSBAR_HEIGHT - SEAT_MIN_HEIGHT,
      ),
    ),
  );
  const dragging = useRef<{ startY: number; startHeight: number } | null>(null);
  const onDividerPointerMove = useCallback((event: PointerEvent) => {
    const drag = dragging.current;
    if (drag === null) {
      return;
    }
    const max = window.innerHeight - HEADER_HEIGHT - STATUSBAR_HEIGHT - SEAT_MIN_HEIGHT;
    const height = drag.startHeight + (event.clientY - drag.startY);
    setSettingsHeight(Math.max(SETTINGS_MIN_HEIGHT, Math.min(max, height)));
  }, []);
  const onDividerPointerUp = useCallback(() => {
    dragging.current = null;
    document.body.style.cursor = "";
    document.removeEventListener("pointermove", onDividerPointerMove);
    document.removeEventListener("pointerup", onDividerPointerUp);
    document.removeEventListener("pointercancel", onDividerPointerUp);
  }, [onDividerPointerMove]);
  const onDividerPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (event.button !== 0) {
        return; // GP-N-02：仅主键启动拖拽
      }
      dragging.current = { startY: event.clientY, startHeight: settingsHeight };
      document.body.style.cursor = "row-resize";
      document.addEventListener("pointermove", onDividerPointerMove);
      document.addEventListener("pointerup", onDividerPointerUp);
      document.addEventListener("pointercancel", onDividerPointerUp); // GP-N-01
    },
    [settingsHeight, onDividerPointerMove, onDividerPointerUp],
  );
  // GP-02：拖拽途中卸载→document 监听与 body.cursor 兜底清理
  useEffect(() => {
    return () => {
      document.removeEventListener("pointermove", onDividerPointerMove);
      document.removeEventListener("pointerup", onDividerPointerUp);
      document.removeEventListener("pointercancel", onDividerPointerUp);
      document.body.style.cursor = "";
    };
  }, [onDividerPointerMove, onDividerPointerUp]);

  // R2-A 批 2 D4/D5 自愈回路：customInstance 401 → AUTH_EVENT → 自动开
  // 连接设置；卸载移除监听。（B7 拆件红线：本监听留守 App.tsx 状态编排
  // 面——uniqueEntryAnchor 第五锚消费面锚定本件。）
  useEffect(() => {
    const openSettings = () => setSettingsOpen(true);
    window.addEventListener(AUTH_EVENT, openSettings);
    return () => window.removeEventListener(AUTH_EVENT, openSettings);
  }, []);

  /** D3 切槽唯一通道：槽条/模型树/子面条/Ribbon 全部经此——replaceState
   *  写 ?tab=（他键原序保留；studio 恒归一带 subface）。 */
  const setTab = (target: TabTarget) => {
    const next: TabTarget =
      target.slot === "studio" && target.subface === undefined
        ? { slot: "studio", subface: "study" }
        : target;
    if (next.slot === "studio") {
      lastStudioSubface.current = next.subface ?? "study";
    }
    setActiveTarget(next);
    const search = withTabParam(window.location.search, next);
    window.history.replaceState(null, "", search ? `${window.location.pathname}?${search}` : window.location.pathname);
  };
  const handleSlotChange = (key: string) => {
    setTab(key === "studio" ? { slot: "studio", subface: lastStudioSubface.current } : { slot: key as SlotId });
  };
  const handleSubfaceChange = useCallback((subface: StudioSubface) => {
    setTab({ slot: "studio", subface });
  }, []);
  const studioSubface =
    activeTarget.slot === "studio"
      ? activeTarget.subface ?? "study"
      : lastStudioSubface.current;

  // B7 拆件：legacy 壳 JSX 主体迁 legacyShell.tsx（纯搬运）；三浮层
  // overlays 留守本层——Providers 包内同层渲染（主题上下文继承不变）。
  return (
    <Providers>
      <LegacyShell
        projectId={projectId}
        activeSlot={activeTarget.slot}
        onNavigate={setTab}
        onSlotChange={handleSlotChange}
        studioSubface={studioSubface}
        onSubfaceChange={handleSubfaceChange}
        libraryFocusId={libraryFocusId}
        onLibraryFocusChange={setLibraryFocusId}
        selectedUnitId={selectedUnitId}
        onSelectedUnitChange={setSelectedUnitId}
        settingsHeight={settingsHeight}
        onDividerPointerDown={onDividerPointerDown}
        onOpenManager={() => setManagerOpen(true)}
        onOpenAiConnect={() => setAiConnectOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <TokenSettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <AiConnectModal open={aiConnectOpen} onClose={() => setAiConnectOpen(false)} />
      <ProjectManagerModal open={managerOpen} onClose={() => setManagerOpen(false)} />
    </Providers>
  );
}
