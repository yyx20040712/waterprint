/**
 * legacy 壳 JSX 主体（B7 收口批 2026-10-10——App.tsx 拆件纯搬运：Header/
 * aside 三区/main 五槽/右列 Settings+AI 席位+StatusBar 整块随迁，本件
 * 零新逻辑——App.tsx 状态编排面（hooks/setTab/拖拽回调/AUTH_EVENT 自愈
 * 监听）留守原位经 props 下穿；文案/结构/交互逐字节不变，probe-2b6 G1
 * 五区锚与 legacy 全测试双闸承载）。
 *
 * 输入:  App 既有 state/setter 面（props 下穿：projectId/activeSlot+
 *        onSlotChange/studioSubface+onSubfaceChange/libraryFocusId+
 *        onLibraryFocusChange/selectedUnitId+onSelectedUnitChange/
 *        settingsHeight+onDividerPointerDown/三浮层开态回调）+四槽懒
 *        装载器（siteplan/viewer3d/elevation/studio——模块级单例随迁）
 * 输出:  M1 四区骨架渲染：Header（品牌+项目徽章｜Ribbon｜项目管理/AI
 *        连接/设置）+左列双区（模型树+单元库）+中央五槽 Tabs（canvas
 *        直渲染+四槽 LazyPane 懒装载）+右列二分（Settings 窗+AI 席位，
 *        纵向分隔可拖）+StatusBar；懒实例记忆表（UF-67 根治位）随迁
 *        ——WeakMap 模块级单例语义跨 remount 恒同实例不变。
 */
import { lazy, Suspense, useState, type ComponentType, type LazyExoticComponent, type ReactNode } from "react";
import { Button, Layout, Spin, Tabs, Typography } from "antd";
import { FolderOpenOutlined, SettingOutlined } from "@ant-design/icons";

import { CanvasPane } from "./canvasPane";
import { AiSeat } from "./aiSeat";
import { ErrorBoundary } from "./ErrorBoundary";
import { lazyPaneLoader } from "./lazyPaneLoader";
import { ModelTree } from "./modelTree";
import { ParamTabs } from "../features/params/components/ParamTabs";
import { Ribbon } from "./ribbon";
import type { SlotId, StudioSubface, TabTarget } from "./router";
import { StatusBar } from "./statusBar";
import { UnitDetailPanel } from "./unitDetailPanel";
import { UnitLibrary } from "./unitLibrary";
import { AiConnectButton } from "../features/aiconnect/components/AiConnectButton";

const { Content, Header } = Layout;

/** 四非 canvas 槽懒装载器（FE-2——then 包装取 named export；studio 槽
 *  装配件=studioPane，其内部四子面另经注入 LazyPane 懒装载；UF-66 批
 *  起=lazyPaneLoader 工厂形——chunk 失败重试经 cache-bust 恢复；回炉
 *  R1/R2：冷却窗限速+chunkHint=specifier 基名归因）。 */
const siteplanLoader = lazyPaneLoader(() => import("./siteplanPane"), "siteplanPane", (m) => m.SiteplanPane as ComponentType);
const viewer3dLoader = lazyPaneLoader(() => import("./viewer3dPane"), "viewer3dPane", (m) => m.Viewer3dPane as ComponentType);
const elevationLoader = lazyPaneLoader(() => import("./elevationPane"), "elevationPane", (m) => m.ElevationPane as ComponentType);
const studioLoader = lazyPaneLoader(() => import("./studioPane"), "studioPane", (m) => m.StudioPane as ComponentType);

/** 页签装载占位（FE-2——Spin 居中+统一文案，薄组件；App.tsx IS_V4 分支
 *  Suspense 占位同形件留守=两份同文字面独立实例，零行为差）。 */
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

/** studio 子面懒装载注入（legacyShell 单源 LazyPane——studioPane 零反向 import）。 */
function renderLazyPane(label: string, load: () => Promise<{ default: ComponentType }>): ReactNode {
  return <LazyPane label={label} load={load} />;
}

/** legacy 壳主体（B7 拆件——App.tsx JSX 整块随迁；props=App 既有
 *  state/setter 面，overlays 三 Modal 留守 App 由 Providers 包内同层渲染）。 */
export function LegacyShell({
  projectId,
  activeSlot,
  onNavigate,
  onSlotChange,
  studioSubface,
  onSubfaceChange,
  libraryFocusId,
  onLibraryFocusChange,
  selectedUnitId,
  onSelectedUnitChange,
  settingsHeight,
  onDividerPointerDown,
  onOpenManager,
  onOpenAiConnect,
  onOpenSettings,
}: {
  projectId: string | null;
  /** 中央五槽激活键（activeTarget.slot——App 状态编排面下穿）。 */
  activeSlot: SlotId;
  /** 切槽唯一通道（App setTab——槽条/模型树/子面条/Ribbon 全经此）。 */
  onNavigate: (target: TabTarget) => void;
  /** 槽条切槽（App handleSlotChange——studio 恒带会话子面记忆）。 */
  onSlotChange: (key: string) => void;
  /** studio 会话子面（App lastStudioSubface 投影——受控下穿）。 */
  studioSubface: StudioSubface;
  onSubfaceChange: (subface: StudioSubface) => void;
  /** 单元库聚焦（UnitLibrary 受控+Settings 双态换显+画布定位光环）。 */
  libraryFocusId: string | null;
  onLibraryFocusChange: (id: string | null) => void;
  /** 画布选中提升（D7——切项目清陈旧 effect 在 App）。 */
  selectedUnitId: string | null;
  onSelectedUnitChange: (id: string | null) => void;
  /** 右列 Settings 窗高（拖拽状态在 App——挂载期 clamp+pointercancel 清理）。 */
  settingsHeight: number;
  onDividerPointerDown: (event: React.PointerEvent<HTMLDivElement>) => void;
  /** 三浮层开态回调（Modal 承载留守 App.tsx——Providers 包内同层）。 */
  onOpenManager: () => void;
  onOpenAiConnect: () => void;
  onOpenSettings: () => void;
}) {
  return (
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
          <Ribbon projectId={projectId} onNavigate={onNavigate} />
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 12, flex: "none" }}>
          <Button
            type="text"
            icon={<FolderOpenOutlined />}
            onClick={onOpenManager}
            aria-label="项目管理"
            title="项目管理（重命名/复制/删除）"
            data-testid="wp-open-manager-header"
          />
          <AiConnectButton onClick={onOpenAiConnect} />
          {/* M7 批：设计对话顶栏钮退役（B4-4b 入口随席位常驻终结——对话
              经右列 AI 席位 ChatSeat 常驻呈现） */}
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={onOpenSettings}
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
            <ModelTree onNavigate={onNavigate} />
          </div>
          <div style={{ height: 1, background: "var(--wp-border-2)", flex: "none" }} />
          <div data-region="unit-library" style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
            <UnitLibrary
              focusId={libraryFocusId}
              onFocusChange={onLibraryFocusChange}
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
            activeKey={activeSlot}
            onChange={onSlotChange}
            items={[
              {
                key: "canvas",
                label: "工艺画布",
                children: (
                  <CanvasPane libraryFocusId={libraryFocusId} selectedUnitId={selectedUnitId} onSelectedUnitChange={onSelectedUnitChange} />
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
                    childProps={{ subface: studioSubface, onSubfaceChange, renderLazyPane }}
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
                <UnitDetailPanel unitId={libraryFocusId} onClose={() => onLibraryFocusChange(null)} onNavigateTab={() => onNavigate({ slot: "canvas" })} />
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
            <AiSeat onOpenAiConnect={onOpenAiConnect} />
          </section>
        </aside>
      </Layout>
      <StatusBar />
    </Layout>
  );
}
