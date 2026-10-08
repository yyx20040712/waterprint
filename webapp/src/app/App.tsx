/**
 * 应用壳：B-1 四区骨架布局+槽路由状态机+Providers 组合（app 层组合面；
 * M1 批 2026-10-06 四区重写——draft-ia-v3 §3 B-1 形态单源+mapping-2b4
 * 落位；M7 批 2026-10-07 AI 席位实装；M2 批 2026-10-08 Settings 增强收编
 * 〔单元详情 Drawer 退役→focusId 非空右列显 unitDetailPanel——§6 动线③〕
 * ；沿革 FE3→M3→P2 十页签→P2 解冻→M1 四区→M7 席位→M2 Settings 收编→
 * rootfix-20261008 懒实例提升〔UF-67 根治位——LazyPane lazy 实例按 load
 * WeakMap 模块级记忆化提升出渲染通道，remount 复调 ctor 消除；诊断档
 * .workflow/uf67-20261008/diag-uf67-summary.md〕）。
 *
 * 输入:  各 feature 切片与 app 层装配件（app 层是唯一允许组合 features 的
 *        层）+URL ?project=/（useProjectId）?tab=（两级值域+兼容归一）
 *        ?task=/?enum=（深链意图）?token=（首参引导）
 * 输出:  四区骨架：Header（48px——品牌区+项目徽章｜Ribbon 命令带｜项目
 *        管理/AI 连接/设置〔M7 批设计对话钮退役——对话经右列 AI 席位〕）
 *        +中部三列（左列 var(--wp-pane-left) 双区+中央五槽 Tabs
 *        〔wp-scroll-tabs 承袭〕+右列 var(--wp-pane-right) 上下二分
 *        〔纵向分隔可拖〕）+StatusBar（24px）——画布常驻挂载隐藏
 *        （destroyInactiveTabPane=false）
 *
 * 规格说明（brief D3 逐条）：
 *   - 切槽唯一通道 setTab(target)：槽条/模型树/子面条/Ribbon 全经此；写
 *     URL=withTabParam replaceState（他键原序保留——UX1 D2 承袭）；mount
 *     不改写地址栏（兼容值留 URL 至下次切槽——边缘语义 a：opsdebug 不
 *     改写+全族刷新幂等）；初值=?tab= 合法〔含兼容归一〕→用之，无 ?tab=
 *     但有 ?task=/?enum=→studio.study（边缘 c 对称），缺省 canvas；
 *   - 左列=模型树+单元库（原件移入 props 面零改；两区各自 overflow:auto
 *     +1px 分隔线）；右列二分=Settings 窗（M2 批双态换显：focusId 非空挂
 *     unitDetailPanel；null=projectId null 提示/否则 ParamTabs）+AI 席位
 *     容器（M7 批实装：AiSeat 三分页 对话｜任务｜回执——席位聚焦=?task=/
 *     ?enum=/opsdebug 深链在 aiSeat 初值解析落位）；
 *     纵向分隔可拖（Q8 先例：主键判定+pointercancel+卸载清理；位置会话
 *     内不进 URL；下限 360=tokens-2b3 判据/上限=视口净高−席位最小高）；
 *   - selectedUnitId 提升 App（切项目清陈旧 effect——现状 pane 本地态未
 *     清为存量瑕疵根治；树选中联动 M2）；下穿 canvasPane+Settings 窗；
 *   - 中央五槽（次序=router.SLOTS 单源）：canvas 槽=CanvasPane 直渲染
 *     （D4 不 lazy）；其余四槽=LazyPane 懒装载（childProps 扩展——studio
 *     槽受控下穿）；solutionsPane/opsDebugPane 退役删除（提交面迁
 *     Ribbon/诊断面 M7；兼容映射承载旧深链）；
 *   - 列宽令牌物理落地（tokens-2b3 §A=定义与消费同步）：global.css :root
 *     增 --wp-pane-left/right，本文件 width 经 var() 消费（M1 不拖拽）；
 *   - R2-A 批 2 沿现状：?token= 首参引导/401 自愈回路/三浮层（连接设置/
 *     AI 接入/项目管理——M7 批 ChatPane 退役：设计对话浮层与顶栏钮随席位
 *     常驻退役）。
 */
import { FolderOpenOutlined, SettingOutlined } from "@ant-design/icons";
import { lazy, Suspense, useCallback, useEffect, useRef, useState, type ComponentType, type LazyExoticComponent, type ReactNode } from "react";
import { Button, Layout, Spin, Tabs, Typography } from "antd";

import { CanvasPane } from "./canvasPane";
import { AiSeat } from "./aiSeat";
import { ErrorBoundary } from "./ErrorBoundary";
import { lazyPaneLoader } from "./lazyPaneLoader";
import { ModelTree } from "./modelTree";
import { ParamTabs } from "../features/params/components/ParamTabs";
import { ProjectManagerModal } from "./projectManagerModal";
import { Providers } from "./providers";
import { Ribbon } from "./ribbon";
import type { SlotId, StudioSubface, TabTarget } from "./router";
import {
  clearTokenParam,
  parseEnumParam,
  parseTabParam,
  parseTaskParam,
  parseTokenParam,
  withTabParam,
} from "./projectParam";
import { StatusBar } from "./statusBar";
import { TokenSettingsModal } from "./tokenSettingsModal";
import { UnitDetailPanel } from "./unitDetailPanel";
import { UnitLibrary } from "./unitLibrary";
import { AiConnectButton } from "../features/aiconnect/components/AiConnectButton";
import { AiConnectModal } from "../features/aiconnect/components/AiConnectModal";
import { setApiToken } from "../shared/api/token";
import { AUTH_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";
import { ShellV4 } from "./shellV4/shellV4";
import { parseIaParam } from "./zoneParam";

/** 四非 canvas 槽懒装载器（FE-2——then 包装取 named export；studio 槽
 *  装配件=studioPane，其内部四子面另经注入 LazyPane 懒装载；UF-66 批
 *  起=lazyPaneLoader 工厂形——chunk 失败重试经 cache-bust 恢复；回炉
 *  R1/R2：冷却窗限速+chunkHint=specifier 基名归因）。 */
const siteplanLoader = lazyPaneLoader(() => import("./siteplanPane"), "siteplanPane", (m) => m.SiteplanPane as ComponentType);
const viewer3dLoader = lazyPaneLoader(() => import("./viewer3dPane"), "viewer3dPane", (m) => m.Viewer3dPane as ComponentType);
const elevationLoader = lazyPaneLoader(() => import("./elevationPane"), "elevationPane", (m) => m.ElevationPane as ComponentType);
const studioLoader = lazyPaneLoader(() => import("./studioPane"), "studioPane", (m) => m.StudioPane as ComponentType);

/** 页签装载占位（FE-2——Spin 居中+统一文案，薄组件）。 */
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

/** 懒装载器签名（LazyPane 消费面统一形——四槽 loader+studio 子面 loader）。 */
type LazyPaneLoad = () => Promise<{ default: ComponentType }>;

/** 懒实例模块级记忆表（rootfix-20261008——UF-67 根治位）：load→lazy
 *  实例。load 均模块级单例（四槽 loader+studio 五子面 loader）——表跨
 *  remount/跨组件树生命周期恒同实例：payload 已定局（Rejected/
 *  Resolved）即直读不再复调 ctor，拆除「ctor→import 拒绝→调度重试→
 *  初始化器重跑→新 lazy→再 ctor」自持循环（UF-67 中断源——诊断档
 *  .workflow/uf67-20261008/diag-uf67-summary.md 三证链；E1c 反事实
 *  记忆化=本形原型）。WeakMap 形=load 键可回收时实例随键回收零泄漏面。 */
const lazyByLoad = new WeakMap<LazyPaneLoad, LazyExoticComponent<ComponentType>>();

/** 取件（缺席时构造+入表）——LazyPane 初始化器/渲染通道恒经此。 */
function getLazy(load: LazyPaneLoad): LazyExoticComponent<ComponentType> {
  let instance = lazyByLoad.get(load);
  if (instance === undefined) {
    instance = lazy(load);
    lazyByLoad.set(load, instance);
  }
  return instance;
}

/** 显式重试构造器：直接构造新 lazy（现行语义零变——显式用户动作换新
 *  实例破失败占位+边界复位）+入表（rootfix 择稳形：重试后 remount 取
 *  最新实例，不回退旧拒绝态实例——不入表形下重试成功后 remount 回归
 *  降级=回归洞；判据「重试后再 remount 不回归」，lazyPaneHoist.test
 *  用例③形态锁）。 */
function retryLazy(load: LazyPaneLoad): LazyExoticComponent<ComponentType> {
  const instance = lazy(load);
  lazyByLoad.set(load, instance);
  return instance;
}

/** 懒页签隔离壳（R1 F2=viewer3dPane R1 先例泛化；M1 childProps 扩展：
 *  懒件按 props 透传重渲——studio 槽受控面经此下穿；rootfix-20261008：
 *  lazy 实例经模块级记忆表提升出渲染通道——初始化器恒取 getLazy(load)
 *  记忆实例，remount/未提交渲染重试零新构造）。 */
function LazyPane({
  label,
  load,
  childProps,
}: {
  label: string;
  load: LazyPaneLoad;
  childProps?: Record<string, unknown>;
}) {
  const [Pane, setPane] = useState(() => getLazy(load));
  return (
    <ErrorBoundary label={label} onRetry={() => setPane(retryLazy(load))}>
      <Suspense fallback={<PaneLoading />}>
        <Pane {...(childProps ?? {})} />
      </Suspense>
    </ErrorBoundary>
  );
}

/** studio 子面懒装载注入（App 单源 LazyPane——studioPane 零反向 import）。 */
function renderLazyPane(label: string, load: () => Promise<{ default: ComponentType }>): ReactNode {
  return <LazyPane label={label} load={load} />;
}

/** 右列纵向拖拽限位（D3：下限=tokens-2b3 判据 Settings 高 360；上限=
 *  视口净高〔−顶栏 48−状态栏 24〕−席位最小高 140——会话内 state 不进 URL）。 */
const SETTINGS_MIN_HEIGHT = 360;
const SETTINGS_DEFAULT_HEIGHT = 480;
const SEAT_MIN_HEIGHT = 140;
const HEADER_HEIGHT = 48;
const STATUSBAR_HEIGHT = 24;

const { Content, Header } = Layout;

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
  // B1 骨架批（2026-10-09）：?ia=v4 分支单点——v4 壳挂载；缺省（无 ?ia=）
  // M1 壳一行不改（本分支=唯一例外）。
  if (parseIaParam(window.location.search) === "v4") {
    return (
      <Providers>
        <ShellV4 />
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
  // 连接设置；卸载移除监听。
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

  return (
    <Providers>
      <Layout style={{ height: "100vh", overflow: "hidden" }}>
        <Header
          className="wp-gold-edge"
          style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 16px", flex: "none" }}
        >
          {/* C1 品牌区（现状原件零改）：水滴标+双语名 */}
          <span style={{ display: "flex", alignItems: "center", gap: 10, flex: "none" }}>
            <span
              aria-hidden
              style={{
                width: 26,
                height: 26,
                borderRadius: 7,
                position: "relative",
                display: "inline-block",
                background:
                  "radial-gradient(circle at 30% 25%, var(--wp-water) 0%, #1d5fd0 60%, #0e3a8f 100%)",
                boxShadow:
                  "0 0 0 1px color-mix(in srgb, var(--wp-gold) 45%, transparent), 0 2px 8px rgba(29, 95, 208, 0.35)",
              }}
            >
              <span
                style={{
                  position: "absolute",
                  left: 8,
                  top: 6,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#cfe6ff",
                  opacity: 0.85,
                }}
              />
            </span>
            <Typography.Text strong style={{ fontSize: 15, letterSpacing: 0.5 }}>
              智水蓝图
            </Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12, marginLeft: -2 }}>
              WaterPrint
            </Typography.Text>
            {/* C1 项目徽章：绿点=已选项目上下文+截断 id */}
            {projectId === null ? null : (
              <span
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  height: 28,
                  padding: "0 12px",
                  background: "var(--wp-bg-elevated)",
                  border: "1px solid var(--wp-border)",
                  borderRadius: 6,
                  color: "var(--wp-text-2)",
                  fontSize: 12,
                  userSelect: "none",
                  marginLeft: 6,
                }}
              >
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--wp-success)" }} />
                <span style={{ fontFamily: "var(--wp-font-mono)" }}>
                  {projectId.slice(0, 8)}
                </span>
              </span>
            )}
          </span>
          {/* M1 Ribbon 命令带（Header 中段——四命令定版） */}
          <span style={{ display: "flex", alignItems: "center", minWidth: 0, flex: 1 }}>
            <Ribbon projectId={projectId} onNavigate={setTab} />
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 12, flex: "none" }}>
            <Button
              type="text"
              icon={<FolderOpenOutlined />}
              onClick={() => setManagerOpen(true)}
              aria-label="项目管理"
              title="项目管理（重命名/复制/删除）"
              data-testid="wp-open-manager-header"
            />
            <AiConnectButton onClick={() => setAiConnectOpen(true)} />
            {/* M7 批：设计对话顶栏钮退役（B4-4b 入口随席位常驻终结——对话
                经右列 AI 席位 ChatSeat 常驻呈现） */}
            <Button
              type="text"
              icon={<SettingOutlined />}
              onClick={() => setSettingsOpen(true)}
              aria-label="连接设置"
              title="连接设置"
            />
          </span>
        </Header>
        <Layout style={{ flex: 1, minHeight: 0, overflow: "hidden", flexDirection: "row" }}>
          {/* M1 左列双区：模型树+单元库（列宽=--wp-pane-left 令牌消费） */}
          <aside
            style={{
              width: "var(--wp-pane-left)",
              flex: "none",
              display: "flex",
              flexDirection: "column",
              minHeight: 0,
              background: "var(--wp-bg-container)",
              borderRight: "1px solid var(--wp-border-2)",
            }}
          >
            <div style={{ height: "38%", minHeight: 0, overflow: "auto" }}>
              <ModelTree onNavigate={setTab} />
            </div>
            <div style={{ height: 1, background: "var(--wp-border-2)", flex: "none" }} />
            <div data-region="unit-library" style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
              <UnitLibrary
                focusId={libraryFocusId}
                onFocusChange={setLibraryFocusId}
              />
            </div>
          </aside>
          {/* 中央主视图槽条五槽（wp-scroll-tabs 承袭——nav 样式/滚动域/满高链） */}
          <Content
            data-region="main-view"
            style={{ display: "flex", flexDirection: "column", minHeight: 0, flex: 1 }}
          >
            <Tabs
              className="wp-scroll-tabs"
              activeKey={activeTarget.slot}
              onChange={handleSlotChange}
              items={[
                {
                  key: "canvas",
                  label: "工艺画布",
                  children: (
                    <CanvasPane libraryFocusId={libraryFocusId} selectedUnitId={selectedUnitId} onSelectedUnitChange={setSelectedUnitId} />
                  ),
                },
                {
                  key: "siteplan",
                  label: "厂区布置",
                  children: <LazyPane label="厂区布置" load={siteplanLoader} />,
                },
                {
                  key: "viewer3d",
                  label: "三维视图",
                  children: <LazyPane label="三维视图" load={viewer3dLoader} />,
                },
                {
                  key: "elevation",
                  label: "高程纵断",
                  children: <LazyPane label="高程纵断" load={elevationLoader} />,
                },
                {
                  key: "studio",
                  label: "研究",
                  children: (
                    <LazyPane
                      label="研究"
                      load={studioLoader}
                      childProps={{ subface: studioSubface, onSubfaceChange: handleSubfaceChange, renderLazyPane }}
                    />
                  ),
                },
              ]}
            />
          </Content>
          {/* M1 右列二分（列宽=--wp-pane-right 令牌消费）：上 Settings 属性窗
              +下 AI 席位容器（M7 占位）；纵向分隔可拖（Q8 先例） */}
          <aside
            style={{
              width: "var(--wp-pane-right)",
              flex: "none",
              display: "flex",
              flexDirection: "column",
              minHeight: 0,
              background: "var(--wp-bg-container)",
              borderLeft: "1px solid var(--wp-border-2)",
            }}
          >
            <section
              data-region="settings"
              style={{ height: settingsHeight, flex: "none", display: "flex", flexDirection: "column", minHeight: 0 }}
            >
              <div
                style={{ flex: "none", padding: "6px 10px", borderBottom: "1px solid var(--wp-border-2)", display: "flex", alignItems: "center" }}
              >
                <Typography.Text strong>Settings</Typography.Text>
              </div>
              <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "8px 10px" }}>
                {/* M2 双态换显：focusId 非空=unitDetailPanel〔Drawer 收编右窗〕；
                    null=ParamTabs〔display 切换恒挂载——草稿零丢失〕 */}
                <div
                  style={{ display: libraryFocusId !== null ? "none" : "block", height: "100%" }}
                >
                  {projectId === null ? (
                    <Typography.Paragraph type="secondary">尚未选择项目——请先在画布槽选择项目</Typography.Paragraph>
                  ) : (
                    <ParamTabs key={projectId} projectId={projectId} unitId={selectedUnitId} />
                  )}
                </div>
                {libraryFocusId !== null ? (
                  <UnitDetailPanel unitId={libraryFocusId} onClose={() => setLibraryFocusId(null)} onNavigateTab={() => setTab({ slot: "canvas" })} />
                ) : null}
              </div>
            </section>
            {/* 纵向拖拽把手（8px 命中区+3px 可视条——Q8 视觉稿形态） */}
            <div
              onPointerDown={onDividerPointerDown}
              title="拖拽调整 Settings 窗高度"
              style={{ height: 8, flex: "none", cursor: "row-resize", position: "relative" }}
            >
              <div
                style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%, -50%)", width: 36, height: 3, borderRadius: 2, background: "var(--wp-border)" }}
              />
            </div>
            {/* M7 批：AI 席位容器实装（M1 占位空态退役）——三分页 对话｜任务｜
                回执；连接徽标开 AiConnectModal（单一 Modal 面不变） */}
            <section
              data-region="ai-seat"
              style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}
            >
              <AiSeat onOpenAiConnect={() => setAiConnectOpen(true)} />
            </section>
          </aside>
        </Layout>
        <StatusBar />
      </Layout>
      <TokenSettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <AiConnectModal open={aiConnectOpen} onClose={() => setAiConnectOpen(false)} />
      <ProjectManagerModal open={managerOpen} onClose={() => setManagerOpen(false)} />
    </Providers>
  );
}
