/**
 * v4 应用壳根件（B1 骨架批六功能区壳→b2 壳重组批 2026-11-19 八入口：
 * 顶栏 TopBar〔品牌+面包屑+语境工具区〕+窄导航轨 NavRail〔八入口〕+
 * 入口体+状态条 StatusBar〔主题切换器+单机标识槽〕；沿革 v1-20261015
 * 转正唯一壳→b1 三主题化→b2 布局=「窄导航轨+语境侧栏+主工作区+按需
 * inspector」〔批准稿 workbench/network.html〕）。
 *
 * 输入:  URL ?tab=（八入口键+deliverables 子页+旧值兼容归一——mount 不
 *        改写地址栏）+?node=（对象选中真相——独立键读写）+?project=
 *        （useProjectId 订阅）
 * 输出:  v4 壳：TopBar+〔NavRail+入口体〕+状态条+TokenSettingsModal 恒
 *        挂载（连接设置自愈层）；导航切换唯一通道 setNav——replaceState
 *        写 ?tab= 他键原序保留；e2e-fix-r3 批：首启 gate（useBootstrapGate
 *        桥探测三相）probing/unconfigured 相整壳换页〔独立三选页/
 *        探测占位——壳面不挂载=gate 期后台 API 查询零发出，F9〕
 *
 * 规格说明（b2 任务书——八入口装配+URL 迁移）：
 *   - 入口体映射：workbench=WorkbenchZone〔b3 重涂：页头+指标带+当前工艺
 *     +项目列表+右列四卡〕/process=ProcessZone〔b3 重涂：单元库目录/画布/
 *     inspector 三栏〕/parameters=ParametersZone〔b3 重涂：对象树/参数+
 *     回填/方案 三栏〕/analysis=AnalysisPane〔警告/出水/可信度/单元明细〕
 *     /compare=CompareZone〔工况矩阵〕/deliverables=DeliverablesZone〔图纸
 *     /总平面/计算说明〕/viewer3d=Viewer3dZone/ai=AiZone〔AI 窗+任务条〕；
 *   - setNav 单通道：NavRail 经此——withTabParam replaceState（他键原序
 *     保留）；deliverables 子页切换同经 setNav 带 subpage；
 *   - ?node= 双写主从：工艺画布选中→withNodeParam 独立写（task/enum
 *     各自独立互不覆盖——ENG5 D6 双轨形承袭）；?node= 变更不改导航；
 *   - B2 完成直达（§一.4）：ai 页任务条 done→analysis 入口+相关单元
 *     选中；
 *   - F1（业务缺陷批 2026-11-19）：useTaskTerminalFaceRefresh 恒挂载层
 *     ——任务终态 done 失效分析面域（提交时刻失效拉回旧轮值后终态二次
 *     点火翻新；任何 tab 在场——停留参数页场景由此承接）；
 *   - 主题面（b1）：v4ThemeConfigFor(mode)（三模色板+密度 12/26）；
 *   - B3 R1 回炉 R1-W1：连接设置自愈层恒挂载（useSettingsSelfHeal+
 *     TokenSettingsModal 在 ConfigProvider 内常驻——AUTH_EVENT 401 自愈
 *     八入口可达；AI 窗设置钮经 onOpenSettings 透传开同一 state）。
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { ConfigProvider } from "antd";

import { useThemeStore } from "../../shared/store/themeStore";
import { useProjectId } from "../useProjectId";
import { TokenSettingsModal } from "../tokenSettingsModal";
import { RuntimeSettingsModal } from "../runtimeSettingsModal";
import { v4ThemeConfigFor } from "../themeModes";
import {
  initialNavTarget,
  parseNodeParam,
  withNodeParam,
  withTabParam,
  type NavTarget,
} from "../zoneParam";
import {
  BootstrapProbePane,
  OnboardingGate,
  useBootstrapGate,
} from "../onboardingGate";
import { useClientConnectionSupervisor } from "../useClientConnection";
import { useSettingsSelfHeal } from "./settingsSelfHeal";
import { useTaskTerminalFaceRefresh } from "./taskTerminalRefresh";
import { TopBar } from "./topBar";
import { NavRail } from "./navRail";
import { StatusBar } from "./statusBar";
import { WorkbenchZone } from "./workbenchZone";
import { ProcessZone } from "./processZone";
import { ParametersZone } from "./parametersZone";
import { AnalysisPane } from "./analysisPane";
import { CompareZone } from "./compareZone";
import { DeliverablesZone } from "./deliverablesZone";
import { Viewer3dZone } from "./viewer3dZone";
import { AiZone } from "./aiZone";

/** replaceState 写查询串（他键原序保留——pathname 不动；回炉 R1：hash
 *  拼回补齐〔d1-W1——App.tsx ?token= 引导 G1-03 同口径〕）。 */
function replaceSearch(next: string): void {
  window.history.replaceState(
    null,
    "",
    next
      ? `${window.location.pathname}?${next}${window.location.hash}`
      : `${window.location.pathname}${window.location.hash}`,
  );
}

export function ShellV4() {
  const [target, setTargetState] = useState<NavTarget>(() =>
    initialNavTarget(window.location.search),
  );
  // ?node= 对象选中真相（画布选中→参数/分析/方案面随动——B2 批数据流）
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(() =>
    parseNodeParam(window.location.search),
  );
  const [projectId] = useProjectId();
  // R1-W1：连接设置自愈层（恒挂载——入口切换不卸载；手动入口经
  // AiZone→onOpenSettings 透传，AUTH_EVENT 自愈同 state）
  const { settingsOpen, openSettings, closeSettings } = useSettingsSelfHeal();
  // 联机第五批：运行方式与联机 Modal 开态（状态栏运行标识/工作台运行
  // 方式卡两入口单 state——AUTH_EVENT 自愈面属 TokenSettingsModal 不混流）
  const [runtimeOpen, setRuntimeOpen] = useState(false);
  // 联机第六批：客户端连接状态机 supervisor（单例装配——本地态零副作用）
  useClientConnectionSupervisor();
  // F1（业务缺陷批 2026-11-19）：任务终态 done 失效分析面域（恒挂载层
  // 单点——提交时刻失效拉回旧轮值后终态二次点火翻新；TaskStrip 仅 ai
  // 页挂载，停留参数页场景由此承接）
  useTaskTerminalFaceRefresh();
  // b1 三主题：scoped ConfigProvider 按模重建（CSS 轴面=store setMode
  // 内 applyThemeMode；mode 变更本组件重渲染即 antd 面换肤）
  const themeMode = useThemeStore((state) => state.mode);

  // e2e-fix-r3 批（F9）：首启 gate 三相——probing/unconfigured 整壳换页
  // （独立三选页/探测占位）：壳面〔TopBar/NavRail/入口体/状态条〕不挂载
  // =gate 期 projects/runtime/units 等后台查询零发出；本组件全部 hooks
  // （自愈/连接监督等）恒定调用先于换页 return 且 gate 期均无请求
  // （remoteBase=null 门+纯监听）——hook 顺序稳定合规
  const bootstrap = useBootstrapGate();

  // 回炉 R16：切项目清陈旧选中（URL 面清 ?node= 由 projectsZone
  //  openProject 承载，状态面在此同步清，幻影选中双面根治；初挂跳过
  // 〔prevRef 门〕——?node= 深链初值不在挂载期被抹）
  const prevProjectRef = useRef(projectId);
  useEffect(() => {
    if (prevProjectRef.current !== projectId) {
      prevProjectRef.current = projectId;
      setSelectedUnitId(null);
    }
  }, [projectId]);

  /** 导航切换唯一通道（含子页——replaceState 写 ?tab=）。 */
  const setNav = useCallback((next: NavTarget) => {
    setTargetState(next);
    replaceSearch(withTabParam(window.location.search, next));
  }, []);

  /** 画布选中写 ?node=（独立键——不改导航/?tab=；null=解除选中剥键）。 */
  const handleSelectedUnitChange = useCallback((unitId: string | null) => {
    setSelectedUnitId(unitId);
    replaceSearch(withNodeParam(window.location.search, unitId));
  }, []);

  const gatePane =
    bootstrap === "probing" ? (
      <BootstrapProbePane />
    ) : bootstrap === "unconfigured" ? (
      <OnboardingGate />
    ) : null;
  if (gatePane !== null) {
    return (
      <ConfigProvider theme={v4ThemeConfigFor(themeMode)} button={{ autoInsertSpace: false }}>
        <div className="wp-v4-root">{gatePane}</div>
      </ConfigProvider>
    );
  }

  let body: ReactNode = null;
  switch (target.nav) {
    case "workbench":
      body = (
        <WorkbenchZone
          onNavigate={setNav}
          onOpenRuntime={() => setRuntimeOpen(true)}
        />
      );
      break;
    case "process":
      body = (
        <ProcessZone
          selectedUnitId={selectedUnitId}
          onSelectedUnitChange={handleSelectedUnitChange}
          onOpenParameters={() => setNav({ nav: "parameters" })}
        />
      );
      break;
    case "parameters":
      body = (
        <ParametersZone
          selectedUnitId={selectedUnitId}
          onSelectedUnitChange={handleSelectedUnitChange}
          onOpenProcess={() => setNav({ nav: "process" })}
          onOpenAnalysis={() => setNav({ nav: "analysis" })}
          onOpenCompare={() => setNav({ nav: "compare" })}
        />
      );
      break;
    case "analysis":
      body = (
        <AnalysisPane projectId={projectId} selectedUnitId={selectedUnitId} />
      );
      break;
    case "compare":
      body = <CompareZone />;
      break;
    case "deliverables":
      body = (
        <DeliverablesZone
          subpage={target.subpage ?? "sheets"}
          onSubpageChange={(subpage) =>
            setNav({ nav: "deliverables", subpage })
          }
          onGoCalc={() => setNav({ nav: "process" })}
        />
      );
      break;
    case "viewer3d":
      body = <Viewer3dZone />;
      break;
    case "ai":
      body = (
        <AiZone
          onTaskNavigate={(taskTarget) => {
            // B2 完成直达（§一.4）：done 任务→分析入口+相关单元选中
            if (taskTarget.state === "done") {
              setNav({ nav: "analysis" });
              if (taskTarget.unitId !== null) {
                handleSelectedUnitChange(taskTarget.unitId);
              }
            }
          }}
          onOpenSettings={openSettings}
        />
      );
      break;
  }

  return (
    <ConfigProvider
      theme={v4ThemeConfigFor(themeMode)}
      button={{ autoInsertSpace: false }}
    >
      <div className="wp-v4-root">
        <TopBar />
        <div className="wp-v4-frame">
          <NavRail target={target} onNavChange={setNav} />
          <div className="wp-v4-body">{body}</div>
        </div>
        <StatusBar
          nav={target.nav}
          onTaskEntry={() => setNav({ nav: "ai" })}
          onOpenRuntime={() => setRuntimeOpen(true)}
        />
        {/* R1-W1：连接设置自愈层恒挂载（ConfigProvider 内常驻——入口切换
            不卸载，AUTH_EVENT 401 自愈八入口可达；AI 窗仅入口上抛） */}
        <TokenSettingsModal open={settingsOpen} onClose={closeSettings} />
        {/* 联机第五批：运行方式与联机 Modal 恒挂载（状态栏/工作台两入口；
            服务端配对卡按 /api/runtime 真实态呈现） */}
        <RuntimeSettingsModal
          open={runtimeOpen}
          onClose={() => setRuntimeOpen(false)}
        />
      </div>
    </ConfigProvider>
  );
}
