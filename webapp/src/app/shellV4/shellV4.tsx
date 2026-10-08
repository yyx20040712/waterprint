/**
 * v4 应用壳根件（B1 骨架批 2026-10-09——?ia=v4 特性开关下六功能区壳：
 * 顶带 zoneBand+zone 体+24px 状态条；亮色基线〔起即亮色——B4 前新样式
 * 按亮色基线写〕经 scoped ConfigProvider light+global.css .wp-v4-root
 * 变量轴覆写双面达成——antd 组件面 light 算法、M1 复用件 var(--wp-*)
 * 消费面 scoped 覆写翻亮）。
 *
 * 输入:  URL ?tab=（zoneParam 两级值域+兼容归一——mount 不改写地址栏）
 *        +?node=（对象选中真相——独立键读写）+?project=（useProjectId 订阅）
 * 输出:  v4 壳：ZoneBand（zone 切换唯一通道 setZone——replaceState 写
 *        ?tab= 他键原序保留）+六 zone 分区渲染+v4 状态条（连接/项目/
 *        计算态+?ia=v4 迁移期指示+非 design 区 dock 收起入口）
 *
 * 规格说明（B1 任务书 §一/§二.①/§三——plan.md §九 v4 布局定稿）：
 *   - zone 切换唯一通道 setZone：zoneBand 页签经此——withZoneParam
 *     replaceState（他键原序保留——UX1 D2 承袭）；子页切换（design
 *     canvas↔analysis/drafting sheets↔siteplan）同经 setZone 带 subpage；
 *   - ?node= 双写主从：画布选中→withNodeParam 独立写（task/enum 各自
 *     独立互不覆盖——ENG5 D6 双轨形承袭）；?node= 变更不改 zone；
 *   - dock 仅 design 区常驻（其他区收起为状态条内入口——B1 形态=状态条
 *     「任务 ▴」入口切回 design）；
 *   - 亮色面：v4LightTheme（wireframe-d-v4 色板：AC #1677ff+FG-1/2+
 *     BG 分层白+语义色 ok/warn/err 文本值）；状态条 24px 沿承 M1 位。
 */
import { useCallback, useState, type ReactNode } from "react";
import { ConfigProvider, theme } from "antd";
import type { ThemeConfig } from "antd";

import { useProjectId } from "../useProjectId";
import {
  initialZoneTarget,
  parseNodeParam,
  withNodeParam,
  withZoneParam,
  type V4Zone,
  type V4ZoneTarget,
} from "../zoneParam";
import { ZoneBand } from "./zoneBand";
import { DesignZone } from "./designZone";
import { ProjectsZone } from "./projectsZone";
import { NetworkZone } from "./networkZone";
import { DraftingZone } from "./draftingZone";
import { Viewer3dZone } from "./viewer3dZone";
import { ReportZone } from "./reportZone";

/** v4 亮色主题（wireframe-d-v4 色板——B4 全局亮化前的 v4 局部亮面）。 */
const v4LightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#1677ff",
    colorInfo: "#1677ff",
    colorLink: "#1677ff",
    colorBgLayout: "#f5f6f8",
    colorBgContainer: "#ffffff",
    colorBgElevated: "#ffffff",
    colorBorder: "#d6d9de",
    colorBorderSecondary: "#e8eaed",
    colorText: "#1f2329",
    colorTextSecondary: "#646a73",
    colorTextTertiary: "#8a93a0",
    colorSuccess: "#2e7d32",
    colorWarning: "#8a6100",
    colorError: "#b3261e",
    borderRadius: 6,
    controlHeight: 26,
    fontSize: 12,
    fontFamily:
      '"Segoe UI", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif',
    fontFamilyCode:
      '"Cascadia Code", "JetBrains Mono", Consolas, monospace',
  },
};

/** zone 中文名（状态条/页签单源——zoneBand 同词消费）。 */
export const V4_ZONE_LABELS: Record<V4Zone, string> = {
  projects: "项目",
  design: "污水厂设计",
  network: "管网系统",
  drafting: "工程制图",
  viewer3d: "三维示意",
  report: "计算说明",
};

/** replaceState 写查询串（他键原序保留——pathname/hash 不动）。 */
function replaceSearch(next: string): void {
  window.history.replaceState(
    null,
    "",
    next ? `${window.location.pathname}?${next}` : window.location.pathname,
  );
}

export function ShellV4() {
  const [target, setTargetState] = useState<V4ZoneTarget>(() =>
    initialZoneTarget(window.location.search),
  );
  // ?node= 对象选中真相（画布选中→左栏参数/右栏方案随动——B2 批数据流）
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(() =>
    parseNodeParam(window.location.search),
  );
  const [projectId] = useProjectId();

  /** zone 切换唯一通道（含子页——replaceState 写 ?tab=）。 */
  const setZone = useCallback((next: V4ZoneTarget) => {
    setTargetState(next);
    replaceSearch(withZoneParam(window.location.search, next));
  }, []);

  /** 画布选中写 ?node=（独立键——不改 zone/?tab=；null=解除选中剥键）。 */
  const handleSelectedUnitChange = useCallback((unitId: string | null) => {
    setSelectedUnitId(unitId);
    replaceSearch(withNodeParam(window.location.search, unitId));
  }, []);

  let body: ReactNode = null;
  switch (target.zone) {
    case "projects":
      body = (
        <ProjectsZone onOpen={() => setZone({ zone: "design" })} />
      );
      break;
    case "design":
      body = (
        <DesignZone
          target={target}
          selectedUnitId={selectedUnitId}
          onSelectedUnitChange={handleSelectedUnitChange}
          onSubpageChange={(subpage) =>
            setZone({ zone: "design", subpage })
          }
        />
      );
      break;
    case "network":
      body = <NetworkZone />;
      break;
    case "drafting":
      body = (
        <DraftingZone
          subpage={target.subpage ?? "sheets"}
          onSubpageChange={(subpage) =>
            setZone({ zone: "drafting", subpage })
          }
        />
      );
      break;
    case "viewer3d":
      body = <Viewer3dZone />;
      break;
    case "report":
      body = <ReportZone />;
      break;
  }

  return (
    <ConfigProvider theme={v4LightTheme} button={{ autoInsertSpace: false }}>
      <div className="wp-v4-root">
        <ZoneBand target={target} onZoneChange={setZone} />
        <div className="wp-v4-body">{body}</div>
        <footer className="wp-v4-statusbar">
          <span style={{ color: "var(--wpv4-ok)" }}>●</span>
          <span>已连接</span>
          <span>
            项目：
            {projectId === null ? "未选择" : projectId.slice(0, 16)}
          </span>
          <span className="r">
            {target.zone !== "design" ? (
              <button
                type="button"
                title="任务与 AI 对话在「污水厂设计」区底栏"
                onClick={() => setZone({ zone: "design" })}
              >
                任务 ▴
              </button>
            ) : null}
            <span>ia=v4</span>
          </span>
        </footer>
      </div>
    </ConfigProvider>
  );
}
