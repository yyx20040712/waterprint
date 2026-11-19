/**
 * v4 工作台区（b2 壳重组批 2026-11-19 八入口着陆页；b3 功能面重涂批同日
 * 重制——稿 workbench.html 形：页头〔标题+副题+导入/新建钮〕+主列〔指标带
 * 3 格+当前工艺面板〔水线条+泥线注〕+项目列表面板〕+右列〔继续工作/任务/
 * 运行方式/规划能力〕；沿革 B1 projectsZone 独立 zone→b2 归工作台入口→
 * b3 信息组织重造〔ProjectsZone 逻辑件保留=列表/搜索/打开/复制/重命名/
 * 删除——B1/V3 D4 逻辑零改；建项 Modal 上提本区页头〕）。
 *
 * 输入:  onNavigate（跨入口导航——shellV4 setNav 单通道）+onOpenRuntime
 *        （运行方式卡设置/配对钮——shellV4 运行方式与联机 Modal）+
 *        useProjectId（建项成功=openProject：切项目+清 ?node=+落工艺页）
 *        +useReadProject（当前项目 raw→projectFlow 投影统计——canvas
 *        通道同键缓存共享）+useValidationQuery（聚合警告计数）+
 *        useGetRuntimeApiRuntimeGet（运行方式卡真实角色——联机第五批）+
 *        parseTaskParam/parseEnumParam+useGetTaskStatus（最新任务态）
 * 输出:  工作台页：指标带（工艺单元/单元连接/聚合警告）+当前工艺（水线
 *        序列条+泥线注+打开画布钮）+ProjectsZone（项目列表面板）+右列四
 *        卡（继续工作三行/最新任务行/运行方式〔真实角色：单机/服务端
 *        两态——联机第五批接真〕/规划能力条〔wp-pending-network 锚族
 *        沿承——G5 在场断言面〕）
 *
 * 规格说明（b3 批准稿 workbench.html+workbench-server.html——视觉与信息
 *   组织重造，数据流零变；联机第五批 2026-11-19 运行方式卡接真）：
 *   - 指标带=当前项目投影统计（projectFlow nodes/edges 计数+validation
 *     聚合警告数——既有 GET 通道消费，无项目/未算=「—」占位不虚造）；
 *   - 当前工艺=水线单元拓扑序条（layout 坐标排序）+泥线独立注——水/泥
 *     线计数徽标；打开画布=onNavigate process；
 *   - 建项两钮=CreateProjectModal 上提（initialMode 直开导入态——件
 *     本体零行为变）；成功=openProject 同链（切项目+清选中+落工艺页）；
 *   - 任务卡=?task=/?enum= 最新任务快照（无任务=空态引导——任务历史
 *     面在「AI 助手」页，本卡单行现状）；
 *   - 运行方式卡=真实角色（/api/runtime：server 态=「服务端模式」徽标
 *     +局域网地址行+「地址与配对 token」入口——稿 workbench-server
 *     运行方式段；standalone/读不到=单机说明零变承袭 b3 文案）；
 *   - 规划能力条=诚实说明（微文案白名单挂起说明族）；管网定线不进
 *     八入口导航（不设虚假入口）。
 */
import { useMemo, useState } from "react";
import { Button } from "antd";

import { useValidationQuery } from "../../features/validation/api/useValidationQuery";
import { projectFlow } from "../../features/canvas/lib/projectFlow";
import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../../shared/api/generated/calc/calc";
import { useReadProjectApiProjectsProjectIdGet } from "../../shared/api/generated/projects/projects";
import { taskStatusToView, type TaskView } from "../../features/solutions/lib/taskFeed";
import { parseEnumParam, parseTaskParam } from "../projectParam";
import { CreateProjectModal } from "../createProjectModal";
import { useProjectId } from "../useProjectId";
import { withNodeParam } from "../zoneParam";
import type { NavTarget } from "../zoneParam";
import { ProjectsZone } from "./projectsZone";
import { WorkbenchRuntimeCard } from "./workbenchRuntimeCard";

/** 任务状态文案（aiZone STATE_TEXT 同源子集——单行现状卡消费面）。 */
const STATE_TEXT: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  done: "已完成",
  cancelled: "已取消",
  failed: "失败",
};

/** 继续工作三行（稿 workbench.html 继续工作段——跨入口导航锚定）。 */
const CONTINUE_ENTRIES: readonly {
  key: string;
  title: string;
  sub: string;
  target: NavTarget;
}[] = [
  {
    key: "params",
    title: "调整单元参数",
    sub: "约束参数与经验取值",
    target: { nav: "parameters" },
  },
  {
    key: "analysis",
    title: "查看诊断与出水",
    sub: "警告聚合与单元明细",
    target: { nav: "analysis" },
  },
  {
    key: "report",
    title: "阅读计算说明书",
    sub: "逐单元计算与公式",
    target: { nav: "deliverables", subpage: "report" },
  },
];

export function WorkbenchZone({
  onNavigate,
  onOpenRuntime,
}: {
  /** 跨入口导航（shellV4 setNav 单通道）。 */
  onNavigate: (target: NavTarget) => void;
  /** 运行方式卡设置/配对钮（shellV4 承载 RuntimeSettingsModal——联机第五批）。 */
  onOpenRuntime: () => void;
}) {
  const [projectId, setProjectId] = useProjectId();
  const [createOpen, setCreateOpen] = useState(false);
  const [createMode, setCreateMode] = useState<"blank" | "import">("blank");

  // 当前项目 raw（canvas/params 通道同键缓存共享——指标带/当前工艺消费；
  // enabled 门=未选项目零请求）
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null },
  });
  const validationQuery = useValidationQuery(projectId);
  const catalog = useListUnitsApiUnitsGet();

  // 投影统计+水/泥线序列（layout 坐标序——失败/缺数据=null 占位）
  const stats = useMemo(() => {
    if (projectId === null || rawQuery.data === undefined) {
      return null;
    }
    try {
      const flow = projectFlow(rawQuery.data);
      const metaByUnit = new Map<
        string,
        { name: string; line: string | null }
      >();
      for (const unit of catalog.data?.units ?? []) {
        metaByUnit.set(unit.unit_id, {
          name: unit.name_zh,
          line: unit.business_line ?? null,
        });
      }
      const named = flow.nodes
        .map((node) => {
          const meta = metaByUnit.get(node.data.kind ?? node.data.unitId);
          return {
            id: node.id,
            label: meta?.name ?? node.id,
            x: node.position.x,
            y: node.position.y,
            line: meta?.line ?? null,
          };
        })
        .sort((a, b) => a.x - b.x || a.y - b.y);
      return {
        unitCount: flow.nodes.length,
        edgeCount: flow.edges.length,
        water: named.filter((node) => node.line !== "sludge"),
        sludge: named.filter((node) => node.line === "sludge"),
      };
    } catch {
      return null;
    }
  }, [projectId, rawQuery.data, catalog.data]);

  const warningCount =
    validationQuery.data?.warnings.length !== undefined
      ? validationQuery.data.warnings.length
      : null;

  /** 建项成功=打开项目（切项目+清 ?node=+落工艺页——projectsZone 同链）。 */
  const openProject = (id: string) => {
    setProjectId(id);
    const nextSearch = withNodeParam(window.location.search, null);
    window.history.replaceState(
      null,
      "",
      nextSearch
        ? `${window.location.pathname}?${nextSearch}`
        : window.location.pathname,
    );
    onNavigate({ nav: "process" });
  };

  return (
    <section data-region="workbench" className="wp-wb">
      <div className="wp-wb-scroll">
        <header className="wp-wb-head">
          <div>
            <h1>项目工作台</h1>
            <p className="wp-wb-sub">
              从项目语境进入工艺、诊断与交付，不再经过多层功能区跳转。
            </p>
          </div>
          <div className="wp-wb-actions">
            <Button
              onClick={() => {
                setCreateMode("import");
                setCreateOpen(true);
              }}
              data-testid="wp-v4-proj-import"
            >
              导入项目
            </Button>
            <Button
              type="primary"
              onClick={() => {
                setCreateMode("blank");
                setCreateOpen(true);
              }}
              data-testid="wp-v4-proj-create"
            >
              新建项目
            </Button>
          </div>
        </header>
        <div className="wp-wb-grid">
          <div className="wp-wb-col">
            {/* 指标带（稿 .metric-grid——投影统计+聚合警告；无项目=—） */}
            <div className="wp-wb-metrics" data-region="workbench-metrics">
              <div className="wp-wb-metric">
                <div className="label">工艺单元</div>
                <div className="value">{stats?.unitCount ?? "—"}</div>
                <div className="note">
                  {projectId === null ? "打开项目后统计" : "水线、泥线与内置节点"}
                </div>
              </div>
              <div className="wp-wb-metric">
                <div className="label">单元连接</div>
                <div className="value">{stats?.edgeCount ?? "—"}</div>
                <div className="note">
                  {projectId === null ? "打开项目后统计" : "画布设计数据"}
                </div>
              </div>
              <div className="wp-wb-metric">
                <div className="label">聚合警告</div>
                <div
                  className="value"
                  style={
                    warningCount !== null && warningCount > 0
                      ? { color: "var(--wp-warning)" }
                      : undefined
                  }
                >
                  {warningCount ?? "—"}
                </div>
                <div className="note">
                  {projectId === null
                    ? "打开项目后统计"
                    : validationQuery.isError
                      ? "聚合面读取失败"
                      : "声明级、跨工况与单工况"}
                </div>
              </div>
            </div>
            {/* 当前工艺（稿 .process-strip——水线序+泥线注；无项目=面板缺省） */}
            {projectId !== null ? (
              <section className="wp-wb-panel" data-region="workbench-process">
                <div className="wp-wb-panel-head">
                  <div className="aux">
                    <h3>当前工艺</h3>
                    <span className="wp-v4-badge water">
                      水线 {stats?.water.length ?? "—"} 单元
                    </span>
                    <span className="wp-v4-badge sludge">
                      泥线 {stats?.sludge.length ?? "—"} 单元
                    </span>
                  </div>
                  <Button
                    size="small"
                    onClick={() => onNavigate({ nav: "process" })}
                  >
                    打开画布 ›
                  </Button>
                </div>
                <div className="wp-wb-panel-body">
                  {stats === null ? (
                    <p style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
                      工艺图读取中…
                    </p>
                  ) : (
                    <>
                      <div className="wp-wb-strip">
                        {stats.water.map((node, index) => (
                          <span key={node.id} title={node.id}>
                            {index > 0 ? (
                              <span className="arr" aria-hidden>
                                →{" "}
                              </span>
                            ) : null}
                            {node.label}
                          </span>
                        ))}
                      </div>
                      <p
                        style={{
                          margin: "8px 0 0",
                          color: "var(--wp-text-2)",
                          fontSize: 11,
                        }}
                      >
                        {stats.sludge.length > 0 ? (
                          <>
                            <span className="arr sludge" aria-hidden>
                              →{" "}
                            </span>
                            {stats.sludge.map((node) => node.label).join(" → ")}
                            （泥线独立着色）
                          </>
                        ) : (
                          "泥线未布置——污泥处理单元可自单元库加入"
                        )}
                      </p>
                    </>
                  )}
                </div>
              </section>
            ) : null}
            {/* 项目列表（ProjectsZone 逻辑件——列表/搜索/打开/复制/重命名/删除） */}
            <ProjectsZone onOpen={() => onNavigate({ nav: "process" })} />
          </div>
          <div className="wp-wb-col">
            {/* 继续工作（稿 .list——跨入口导航三行） */}
            <section className="wp-wb-panel">
              <div className="wp-wb-panel-head">
                <h3>继续工作</h3>
              </div>
              <div className="wp-v4-list">
                {CONTINUE_ENTRIES.map((entry) => (
                  <button
                    key={entry.key}
                    type="button"
                    className="wp-v4-row"
                    data-testid={`wp-v4-continue-${entry.key}`}
                    onClick={() => onNavigate(entry.target)}
                  >
                    <span className="main">
                      <span className="t">{entry.title}</span>
                      <span className="s">{entry.sub}</span>
                    </span>
                    <span aria-hidden>›</span>
                  </button>
                ))}
              </div>
            </section>
            {/* 任务（最新任务单行——历史面在「AI 助手」页） */}
            <WorkbenchTaskCard />
            {/* 运行方式（联机第五批拆件 workbenchRuntimeCard——真实角色两态） */}
            <WorkbenchRuntimeCard onOpenRuntime={onOpenRuntime} />
            {/* 规划能力条（旧 networkZone 占位语义迁入——锚族沿承） */}
            <section className="wp-wb-panel">
              <div className="wp-wb-panel-head">
                <h3>规划能力</h3>
              </div>
              <div className="wp-wb-panel-body">
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                  }}
                >
                  <span>管网定线</span>
                  <span className="wp-v4-badge" data-testid="wp-pending-network">
                    规划中，未实装
                  </span>
                </div>
                <p
                  style={{
                    margin: "8px 0 0",
                    color: "var(--wp-text-2)",
                    fontSize: 11,
                  }}
                >
                  不设置虚假入口。现有工艺画布和厂区总平面保持可用。
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
      <CreateProjectModal
        open={createOpen}
        initialMode={createMode}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => {
          setCreateOpen(false);
          openProject(created);
        }}
      />
    </section>
  );
}

/** 任务现状卡（?task=/?enum= 最新任务快照单行——aiZone TaskStrip 同源
 *  取数面凝缩；无任务=空态引导）。 */
function WorkbenchTaskCard() {
  const taskId =
    parseTaskParam(window.location.search) ??
    parseEnumParam(window.location.search);
  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(taskId ?? "", {
    query: { enabled: taskId !== null },
  });
  const view: TaskView | null =
    statusQuery.data !== null && statusQuery.data !== undefined
      ? taskStatusToView(statusQuery.data)
      : null;
  const state = view?.state ?? "";
  const stateLabel = taskId === null ? null : (STATE_TEXT[state] ?? state);

  return (
    <section className="wp-wb-panel" data-region="workbench-tasks">
      <div className="wp-wb-panel-head">
        <h3>任务</h3>
        {taskId !== null && state === "done" ? (
          <span className="wp-v4-badge ok">服务已回执</span>
        ) : null}
      </div>
      <div className="wp-v4-list">
        {taskId === null || view === null ? (
          <p
            style={{
              margin: 0,
              padding: "10px 12px",
              color: "var(--wp-text-2)",
              fontSize: 11,
            }}
          >
            暂无任务记录——计算与枚举任务在「AI 助手」页跟踪
          </p>
        ) : (
          <div className="wp-v4-row">
            <span className="main">
              <span className="t">任务 {taskId.slice(0, 8)}</span>
              <span className="s">当前任务快照</span>
            </span>
            <span
              className={`wp-v4-badge ${
                state === "done"
                  ? "ok"
                  : state === "failed"
                    ? "error"
                    : state === "running"
                      ? "accent"
                      : ""
              }`}
            >
              {stateLabel}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
