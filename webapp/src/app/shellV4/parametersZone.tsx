/**
 * v4 参数方案区（b2 壳重组批 2026-11-19 八入口「参数方案」；b3 功能面
 * 重涂批同日重制——稿 parameters.html 三栏形：左=工艺对象树〔搜索+单元行
 * 点选写 ?node=——选中通道与画布同源〕+中=选中单元工作区〔pane-head 身份
 * 行+约束参数/经验取值/全局三页签+ParamForm+计算回填表〕+右=方案区〔单元
 * 方案/全厂联合两页+⟳重新枚举 Modal 唯一入口+联合枚举 Modal 唯一入口+
 * 分析面入口组〕；沿革 B1 designZone 三栏→b2 合一面→b3 信息组织重造
 * 〔左/右栏拖宽键名原样承袭〕）。
 *
 * 输入:  selectedUnitId（?node= 对象选中真相——工艺页画布选中跨页随动）
 *        +onSelectedUnitChange（对象树点选写回——shellV4 受控单源）+
 *        onOpenProcess（对象树底「返回工艺画布」）+onOpenAnalysis/
 *        onOpenCompare（分析面入口组跨入口导航）+useProjectId+
 *        useProjectUnits（对象树清单）+useUnitCatalog（单元中文名）
 * 输出:  三栏：左=对象树〔pane-head 工艺对象+计数+搜索+单元行族+返回
 *        画布钮〕；中=工作区〔身份 pane-head+三页签+ParamForm/
 *        AssumptionsPanel/全局骨架卡+BackfillSection 计算回填表〕；
 *        右=方案区壳（SolutionCards/JointSolutionCards+分析面入口组）
 *
 * 规格说明（b3 批准稿 parameters.html——视觉与信息组织重造，数据流零变）：
 *   - 对象树=useProjectUnits 清单（点行=onSelectedUnitChange 写 ?node=
 *     ——与画布选中同一通道，稿左栏语境侧栏语义落地；b2 期「本区无画布
 *     未选=空态引导」缺口就此收口）；
 *   - 中列三页签：约束参数=ParamForm（提交重算链零改）/经验取值=
 *     AssumptionsPanel/全局=项目级骨架卡（空态引导——完整卡=后续批）；
 *   - 右栏两页：选中工艺=SolutionCards（点卡 apply 回填+方案驱动来源
 *     上抛）；全厂=JointSolutionCards+联合枚举+分析面入口组（工况对比
 *     →compare 入口；灵敏度/概算/可信度/高程纵断→analysis 入口）；
 *   - 侧栏宽度：左 225/右 250 默认（B1 键名 wp-v4-left-w/right-w 沿承
 *     ——已存宽度记忆不丢）。
 */
import { useMemo, useState } from "react";
import { Button, Modal } from "antd";

import { AssumptionsPanel } from "../../features/params/components/AssumptionsPanel";
import { ParamForm } from "../../features/params/components/ParamForm";
import { useUnitCatalog } from "../../features/params/api/useUnitCatalog";
import { useProjectUnits } from "../../features/solutions/api/useProjectUnits";
import { JointSubmitForm } from "../jointSolutions";
import { useProjectId } from "../useProjectId";
import { EnumerateModal } from "./enumerateModal";
import { SolutionCards } from "./solutionCards";
import { JointSolutionCards } from "./jointSolutionCards";
import { BackfillSection } from "./backfillSection";
import { usePaneWidth } from "./usePaneWidth";

/** 空态引导（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";
const NO_UNIT_HINT = "在「工艺」画布或左侧对象树选择单元后，参数在此编辑";

/** 全局骨架卡三段（空态——完整卡=后续功能批）。 */
const GLOBAL_CARDS: readonly { key: string; title: string; hint: string }[] = [
  { key: "influent", title: "进水水质水量", hint: "设计进水水质与水量在此定义" },
  { key: "effluent", title: "出水标准", hint: "执行标准与限值在此选择" },
  { key: "conditions", title: "工况定义", hint: "计算工况在此增改" },
];

/** 分析面入口组（全厂页——跨入口导航；b2：工况对比→compare，余→
 *  analysis〔概算/可信度/高程纵断=分析视图，W2 沿承〕）。 */
const ANALYSIS_ENTRIES: readonly { label: string; target: "analysis" | "compare" }[] = [
  { label: "工况对比", target: "compare" },
  { label: "灵敏度", target: "analysis" },
  { label: "概算", target: "analysis" },
  { label: "可信度", target: "analysis" },
  { label: "高程纵断（分析视图）", target: "analysis" },
];

/** 中列页签三值（b3——稿 parameters.html 约束参数/经验取值段+全局承袭）。 */
type ParamTab = "design" | "empirical" | "global";

export function ParametersZone({
  selectedUnitId,
  onSelectedUnitChange,
  onOpenProcess,
  onOpenAnalysis,
  onOpenCompare,
}: {
  /** ?node= 对象选中真相（工艺页画布/本区对象树——参数/方案/回填随动）。 */
  selectedUnitId: string | null;
  /** 选中写入回调（对象树点选上抛——shellV4 单源写 ?node=）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
  /** 「返回工艺画布」钮（shellV4 setNav process）。 */
  onOpenProcess: () => void;
  /** 分析面入口组→「分析」入口（shellV4 setNav analysis）。 */
  onOpenAnalysis: () => void;
  /** 分析面入口组「工况对比」→「工况」入口（shellV4 setNav compare）。 */
  onOpenCompare: () => void;
}) {
  const [projectId] = useProjectId();
  const [paramTab, setParamTab] = useState<ParamTab>("design");
  const [rightTab, setRightTab] = useState<"unit" | "plant">("unit");
  // 对象树搜索（本地过滤——与项目列表搜索同制零新端点）
  const [objSearch, setObjSearch] = useState("");
  const [enumOpen, setEnumOpen] = useState(false);
  // 联合枚举 Modal 开态（B3 U2——全厂页唯一提交入口）
  const [jointOpen, setJointOpen] = useState(false);
  // 方案驱动来源（数据流① 上抛态——回填区标注消费；B2 §三.2）
  const [appliedSource, setAppliedSource] = useState<{
    unitId: string;
    no: string;
  } | null>(null);
  // 侧栏宽度+拖宽（B1 键名/限界原样——已存宽度记忆承袭）
  const leftPane = usePaneWidth({
    key: "wp-v4-left-w",
    fallback: 225,
    min: 160,
    max: 420,
    side: "left",
  });
  const rightPane = usePaneWidth({
    key: "wp-v4-right-w",
    fallback: 250,
    min: 200,
    max: 520,
    side: "right",
  });

  // 对象树清单（useProjectUnits——solutions 通道与枚举面同键缓存共享）
  const unitsQuery = useProjectUnits(projectId);
  const catalog = useUnitCatalog();
  const nameByUnit = useMemo(() => {
    const map = new Map<string, string>();
    for (const unit of catalog.data?.units ?? []) {
      map.set(unit.unit_id, unit.name_zh);
    }
    return map;
  }, [catalog.data]);

  // 对象树可见集（搜索命中过滤——名称/ID 不分大小写子串）
  const visibleUnits = useMemo(() => {
    const needle = objSearch.trim().toLowerCase();
    const all = unitsQuery.data ?? [];
    if (needle === "") {
      return all;
    }
    return all.filter((unit) => {
      const name = nameByUnit.get(unit.kind ?? unit.unitId) ?? unit.unitId;
      return (
        name.toLowerCase().includes(needle) ||
        unit.unitId.toLowerCase().includes(needle)
      );
    });
  }, [unitsQuery.data, objSearch, nameByUnit]);

  return (
    <section className="wp-v4-design" data-region="parameters-workspace">
      <div className="wp-v4-design-row">
        {/* 语境侧栏：工艺对象树（b3 稿左栏——点行写 ?node= 选中同源通道） */}
        <aside
          className="wp-v4-left"
          data-region="parameters-left"
          style={{ width: leftPane.width }}
        >
          <div
            className="wp-v4-drag"
            data-testid="wp-v4-drag-left"
            title="拖拽调整宽度"
            onPointerDown={leftPane.onDragStart}
          >
            ⟷
          </div>
          <div className="wp-v4-pane-head">
            <h3>工艺对象</h3>
            <span className="wp-v4-badge">{unitsQuery.data?.length ?? "—"}</span>
          </div>
          <div className="wp-v4-search">
            <input
              aria-label="搜索工艺对象"
              placeholder="搜索单元"
              data-testid="wp-v4-obj-search"
              value={objSearch}
              onChange={(event) => setObjSearch(event.target.value)}
            />
          </div>
          <div className="wp-v4-pbody" style={{ padding: 0 }}>
            {projectId === null ? (
              <p style={{ color: "var(--wp-text-2)", margin: 8 }}>
                {NO_PROJECT_HINT}
              </p>
            ) : unitsQuery.isError ? (
              <p
                role="alert"
                style={{ color: "var(--wp-error)", fontSize: 12, margin: 8 }}
              >
                单元清单读取失败：
                {unitsQuery.error instanceof Error
                  ? unitsQuery.error.message
                  : "未知错误"}
              </p>
            ) : (
              <div className="wp-v4-list" data-testid="wp-v4-obj-list">
                {visibleUnits.length === 0 ? (
                  <p style={{ color: "var(--wp-text-2)", fontSize: 12, padding: 8 }}>
                    {(unitsQuery.data ?? []).length === 0
                      ? "项目无单元——在「工艺」画布添加"
                      : "无匹配单元"}
                  </p>
                ) : (
                  visibleUnits.map((unit) => {
                    const selected = unit.unitId === selectedUnitId;
                    return (
                      <button
                        key={unit.unitId}
                        type="button"
                        className={`wp-v4-row${selected ? " selected" : ""}`}
                        data-testid={`wp-v4-obj-${unit.unitId}`}
                        onClick={() => onSelectedUnitChange(unit.unitId)}
                      >
                        <span className="main">
                          <span className="t">
                            {nameByUnit.get(unit.kind ?? unit.unitId) ??
                              unit.unitId}
                          </span>
                          <span className="s">{unit.unitId}</span>
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
          <div style={{ flex: "none", padding: 8, borderTop: "1px solid var(--wp-border-2)" }}>
            <Button size="small" block onClick={onOpenProcess}>
              ‹ 返回工艺画布
            </Button>
          </div>
        </aside>

        {/* 主工作区：身份头+三页签+参数面+计算回填（b3 稿中栏段） */}
        <section className="wp-v4-center" data-region="parameters-center">
          <div className="wp-v4-pane-head" style={{ background: "var(--wp-bg-container)" }}>
            <div style={{ minWidth: 0 }}>
              <h3>
                {projectId === null || selectedUnitId === null
                  ? "未选单元"
                  : (nameByUnit.get(selectedUnitId) ?? selectedUnitId)}
              </h3>
              <span style={{ color: "var(--wp-text-2)", fontSize: 11.5 }}>
                选中单元的设计参数，提交后自动重算
              </span>
            </div>
            {selectedUnitId !== null ? (
              nameByUnit.has(selectedUnitId) ? (
                <span className="wp-v4-badge ok">目录已登记</span>
              ) : (
                <span className="wp-v4-badge warn">未在目录登记</span>
              )
            ) : null}
          </div>
          <div className="wp-v4-ptabs" data-testid="wp-v4-param-tabs" style={{ margin: 8 }}>
            <button
              type="button"
              className={`wp-v4-ptab${paramTab === "design" ? " on" : ""}`}
              onClick={() => setParamTab("design")}
            >
              约束参数
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${paramTab === "empirical" ? " on" : ""}`}
              onClick={() => setParamTab("empirical")}
            >
              经验取值
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${paramTab === "global" ? " on" : ""}`}
              onClick={() => setParamTab("global")}
            >
              全局
            </button>
          </div>
          <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
            {paramTab === "design" ? (
              projectId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>
                  {NO_PROJECT_HINT}
                </p>
              ) : selectedUnitId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>
                  {NO_UNIT_HINT}
                </p>
              ) : (
                <ParamForm
                  projectId={projectId}
                  unitId={selectedUnitId}
                  commitOnBlurAndEnter
                />
              )
            ) : paramTab === "empirical" ? (
              projectId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>
                  {NO_PROJECT_HINT}
                </p>
              ) : (
                <AssumptionsPanel projectId={projectId} />
              )
            ) : (
              <div style={{ padding: 8 }}>
                {GLOBAL_CARDS.map((card) => (
                  <div className="wp-v4-sec" key={card.key}>
                    <h4>{card.title}</h4>
                    <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
                      {card.hint}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {/* 计算回填（B2 §三.2 件——b3 表形重涂；设计页签下与表单同列） */}
            {paramTab === "design" ? (
              <BackfillSection
                projectId={projectId}
                unitId={selectedUnitId}
                appliedSource={appliedSource}
              />
            ) : null}
          </div>
        </section>

        {/* inspector 位：方案两页（B1 右栏原件——样式/键名承袭） */}
        <aside
          className="wp-v4-right"
          data-region="parameters-right"
          style={{ width: rightPane.width }}
        >
          <div
            className="wp-v4-drag"
            data-testid="wp-v4-drag-right"
            title="拖拽调整宽度"
            onPointerDown={rightPane.onDragStart}
          >
            ⟷
          </div>
          <div className="wp-v4-pane-head">
            <h3 style={{ fontSize: 12.5 }}>方案</h3>
          </div>
          <div className="wp-v4-ptabs" data-testid="wp-v4-right-tabs">
            <button
              type="button"
              className={`wp-v4-ptab${rightTab === "unit" ? " on" : ""}`}
              onClick={() => setRightTab("unit")}
            >
              单元方案
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${rightTab === "plant" ? " on" : ""}`}
              onClick={() => setRightTab("plant")}
            >
              全厂联合
            </button>
          </div>
          <div className="wp-v4-pbody">
            {rightTab === "unit" ? (
              <SolutionCards
                projectId={projectId}
                unitId={selectedUnitId}
                onOpenEnumerate={() => setEnumOpen(true)}
                onApplied={setAppliedSource}
              />
            ) : (
              <>
                {/* 联合枚举唯一提交入口（B3 U2——JointSubmitForm 复用件承载，
                    提交回路零新写：生成钩子/TASK_EVENT 派发均在复用件内） */}
                <div style={{ display: "flex", gap: 6, paddingBottom: 4 }}>
                  <Button
                    size="small"
                    onClick={() => setJointOpen(true)}
                    data-testid="wp-v4-joint-open"
                    disabled={projectId === null}
                  >
                    联合枚举…
                  </Button>
                </div>
                <JointSolutionCards
                  projectId={projectId}
                  onApplied={setAppliedSource}
                />
                <div className="wp-v4-sec">
                  <h4>分析面</h4>
                  {ANALYSIS_ENTRIES.map((entry) => (
                    <button
                      key={entry.label}
                      type="button"
                      data-entry-target={entry.target}
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        border: "none",
                        background: "transparent",
                        color: "var(--wp-text)",
                        fontSize: 12, // 回炉 R12：字号归一三档（12/11/10）
                        padding: "4px 2px",
                        cursor: "pointer",
                      }}
                      onClick={() =>
                        entry.target === "compare"
                          ? onOpenCompare()
                          : onOpenAnalysis()
                      }
                    >
                      {entry.label} ›
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </aside>
      </div>
      <EnumerateModal
        open={enumOpen}
        onClose={() => setEnumOpen(false)}
        projectId={projectId}
        unitId={selectedUnitId}
      />
      {/* 联合枚举 Modal（B3 U2——enumerateModal 先例制式：v4 scoped 主题下
          antd Modal+无项目态引导；JointSubmitForm 自取清单/判据/提交） */}
      <Modal
        title="联合枚举"
        open={jointOpen}
        onCancel={() => setJointOpen(false)}
        footer={null}
        width={760}
        destroyOnHidden
        data-testid="wp-v4-joint-modal"
      >
        {projectId === null ? (
          <span style={{ color: "var(--wp-text-2)", fontSize: 12 }}>
            尚未选择项目——先在「工作台」打开或新建
          </span>
        ) : (
          <JointSubmitForm
            projectId={projectId}
            onSubmitted={() => setJointOpen(false)}
          />
        )}
      </Modal>
    </section>
  );
}
