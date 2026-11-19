/**
 * v4 参数方案区（b2 壳重组批 2026-11-19——八入口「参数方案」：语境侧栏
 * 〔参数三 tab〕+主工作区〔计算回填〕+inspector 位〔方案两页〕；沿革
 * B1 designZone 三栏〔左参数/中画布·分析/右方案〕——b2 画布拆「工艺」
 * 入口、分析拆「分析」入口后本区=参数+回填+方案合一面〔稿 parameters
 * .html〕，左/右栏件与拖宽键名原样承袭）。
 *
 * 输入:  selectedUnitId（?node= 对象选中真相——工艺页画布选中跨页随动）
 *        +onOpenAnalysis/onOpenCompare（分析面入口组跨入口导航——
 *        shellV4 setNav）+onOpenSettings（连接设置开态上抛——shellV4
 *        恒挂载层承载 Modal）+useProjectId
 * 输出:  三栏：左=ParamForm/AssumptionsPanel 复用+全局骨架卡（wp-v4-
 *        left 拖宽键原样）；中=BackfillSection 计算回填（B2 §三.2 件
 *        原样——位置自左栏底迁主工作区）；右=方案区壳（SolutionCards/
 *        JointSolutionCards+⟳重新枚举 Modal 唯一入口+全厂联合枚举
 *        Modal 唯一入口+分析面入口组）
 *
 * 规格说明（B1 任务书 §三.3 承袭+b2 拆解裁决）：
 *   - 左栏三 tab：设计=选中单元输入参数（ParamForm 复用）/经验=经验
 *     取值（AssumptionsPanel 复用）/全局=项目级输入骨架卡（空态引导）；
 *   - 单元选择=工艺页画布（?node= 共享真相——本区无画布，未选=空态
 *     引导；稿 parameters.html 左栏对象树=后续功能批不新建）；
 *   - 右栏两页：选中工艺=SolutionCards（点卡 apply 回填+方案驱动来源
 *     上抛）；全厂=JointSolutionCards+联合枚举+分析面入口组（工况对比
 *     →compare 入口；灵敏度/概算/可信度/高程纵断→analysis 入口）；
 *   - 侧栏宽度：左 225/右 250 默认（B1 键名 wp-v4-left-w/right-w 沿承
 *     ——已存宽度记忆不丢）。
 */
import { useState } from "react";
import { Button, Modal } from "antd";

import { AssumptionsPanel } from "../../features/params/components/AssumptionsPanel";
import { ParamForm } from "../../features/params/components/ParamForm";
import { JointSubmitForm } from "../jointSolutions";
import { useProjectId } from "../useProjectId";
import { EnumerateModal } from "./enumerateModal";
import { SolutionCards } from "./solutionCards";
import { JointSolutionCards } from "./jointSolutionCards";
import { BackfillSection } from "./backfillSection";
import { usePaneWidth } from "./usePaneWidth";

/** 左栏空态引导（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";
const NO_UNIT_HINT = "在「工艺」画布中选择单元后，参数在此编辑";

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

export function ParametersZone({
  selectedUnitId,
  onOpenAnalysis,
  onOpenCompare,
}: {
  /** ?node= 对象选中真相（工艺页画布选中——参数/方案/回填随动）。 */
  selectedUnitId: string | null;
  /** 分析面入口组→「分析」入口（shellV4 setNav analysis）。 */
  onOpenAnalysis: () => void;
  /** 分析面入口组「工况对比」→「工况」入口（shellV4 setNav compare）。 */
  onOpenCompare: () => void;
}) {
  const [projectId] = useProjectId();
  const [leftTab, setLeftTab] = useState<"design" | "empirical" | "global">("design");
  const [rightTab, setRightTab] = useState<"unit" | "plant">("unit");
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

  return (
    <section className="wp-v4-design" data-region="parameters-workspace">
      <div className="wp-v4-design-row">
        {/* 语境侧栏：参数三 tab（B1 左栏原件——样式/键名承袭） */}
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
          <div className="wp-v4-ptabs" data-testid="wp-v4-left-tabs">
            <button
              type="button"
              className={`wp-v4-ptab${leftTab === "design" ? " on" : ""}`}
              onClick={() => setLeftTab("design")}
            >
              设计
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${leftTab === "empirical" ? " on" : ""}`}
              onClick={() => setLeftTab("empirical")}
            >
              经验
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${leftTab === "global" ? " on" : ""}`}
              onClick={() => setLeftTab("global")}
            >
              全局
            </button>
          </div>
          <div className="wp-v4-pbody">
            {leftTab === "design" ? (
              projectId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>{NO_PROJECT_HINT}</p>
              ) : selectedUnitId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>{NO_UNIT_HINT}</p>
              ) : (
                <ParamForm
                  projectId={projectId}
                  unitId={selectedUnitId}
                  commitOnBlurAndEnter
                />
              )
            ) : leftTab === "empirical" ? (
              projectId === null ? (
                <p style={{ color: "var(--wp-text-2)", margin: 8 }}>{NO_PROJECT_HINT}</p>
              ) : (
                <AssumptionsPanel projectId={projectId} />
              )
            ) : (
              GLOBAL_CARDS.map((card) => (
                <div className="wp-v4-sec" key={card.key}>
                  <h4>{card.title}</h4>
                  <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
                    {card.hint}
                  </span>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* 主工作区：计算回填（B2 §三.2 件原样——位置自左栏底迁中列） */}
        <section className="wp-v4-center" data-region="parameters-center">
          <BackfillSection
            projectId={projectId}
            unitId={selectedUnitId}
            appliedSource={appliedSource}
          />
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
          <div className="wp-v4-ptabs" data-testid="wp-v4-right-tabs">
            <button
              type="button"
              className={`wp-v4-ptab${rightTab === "unit" ? " on" : ""}`}
              onClick={() => setRightTab("unit")}
            >
              选中工艺
            </button>
            <button
              type="button"
              className={`wp-v4-ptab${rightTab === "plant" ? " on" : ""}`}
              onClick={() => setRightTab("plant")}
            >
              全厂
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
