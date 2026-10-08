/**
 * v4 污水厂设计区（B1 骨架批 2026-10-09——核心域三栏：左三 tab〔设计/
 * 经验/全局〕+计算回填区｜中=页签〔工艺画布｜分析表〕+缩略图画布｜右两页
 * 〔选中工艺/全厂〕+底栏双区 dock 常驻；wireframe-d-v4 屏 1 形）。
 *
 * 输入:  target（zone+subpage——shellV4 受控）+selectedUnitId（?node= 对象
 *        选中真相）+onSelectedUnitChange（画布选中上抛）+onSubpageChange
 *        （中列页签切换→?tab= zone 级投影）+useProjectId
 * 输出:  design-workspace 三栏+dock：左=ParamForm/AssumptionsPanel 复用+
 *        全局骨架卡（B2 扩完整卡）+计算回填空态；中=ThumbnailFlow 缩略
 *        画布（笔3）｜分析表空态（B2 实装）；右=方案区壳（★/Δ 徽标=B2）
 *        +⟳重新枚举 Modal 唯一入口+全厂入口组；底=dockBar（AI 唯一窗+
 *        窄任务条）
 *
 * 规格说明（B1 任务书 §三.3——plan §九.1）：
 *   - 左栏三 tab：设计=选中单元输入参数（ParamForm 复用+三式提交 Enter
 *     补齐）/经验=经验取值（AssumptionsPanel 复用）/全局=项目级输入骨架
 *     卡（进水水质水量/出水标准/工况定义——空态引导微文案白名单内）；
 *     计算回填区=自动值 B1 空态；
 *   - 双向数据流=B2 批（B1 只留结构——右栏方案卡壳与左栏回填区空态）；
 *   - dock 仅本区常驻（其他区收起为状态条内入口——shellV4 状态条）；
 *   - 侧栏宽度：左 225/右 250 默认（wireframe 值），拖宽+localStorage
 *     记忆=B1 全局规则（拖柄 wp-v4-drag）。
 */
import { useEffect, useRef, useState } from "react";

import { AssumptionsPanel } from "../../features/params/components/AssumptionsPanel";
import { ParamForm } from "../../features/params/components/ParamForm";
import { useProjectId } from "../useProjectId";
import type { DesignSubpage, V4ZoneTarget } from "../zoneParam";
import { DockBar } from "./dockBar";

/** 左栏空态引导（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「项目」区打开或新建";
const NO_UNIT_HINT = "在画布中选择单元后，参数在此编辑";

/** 全局骨架卡三段（B1 空态——B2 扩完整卡）。 */
const GLOBAL_CARDS: readonly { key: string; title: string; hint: string }[] = [
  { key: "influent", title: "进水水质水量", hint: "设计进水水质与水量在此定义" },
  { key: "effluent", title: "出水标准", hint: "执行标准与限值在此选择" },
  { key: "conditions", title: "工况定义", hint: "计算工况在此增改" },
];

/** 分析面入口组（全厂页——点击切中列分析表；wireframe 屏 3 同族）。 */
const ANALYSIS_ENTRIES: readonly string[] = [
  "工况对比",
  "灵敏度",
  "概算",
  "可信度",
  "高程纵断（分析视图）",
];

/** 拖宽限界（左 160~420/右 200~520——窄侧保画布可读，宽侧防吞画布）。 */
const LEFT_MIN = 160;
const LEFT_MAX = 420;
const RIGHT_MIN = 200;
const RIGHT_MAX = 520;
const LEFT_DEFAULT = 225;
const RIGHT_DEFAULT = 250;
const LEFT_KEY = "wp-v4-left-w";
const RIGHT_KEY = "wp-v4-right-w";

/** 宽度持久读（localStorage——非法值/越界钳回默认）。 */
function readWidth(key: string, fallback: number, min: number, max: number): number {
  if (typeof window === "undefined") {
    return fallback;
  }
  const raw = window.localStorage.getItem(key);
  const value = raw === null ? NaN : Number(raw);
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return Math.max(min, Math.min(max, value));
}

export function DesignZone({
  target,
  selectedUnitId,
  onSelectedUnitChange,
  onSubpageChange,
}: {
  target: Extract<V4ZoneTarget, { zone: "design" }>;
  /** ?node= 对象选中真相（画布选中→左栏参数随动——B2 批扩右栏方案）。 */
  selectedUnitId: string | null;
  /** 选中写入回调（ThumbnailFlow onNodeClick 上抛——shellV4 单源）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
  /** 中列子页切换（canvas↔analysis——?tab= zone 级投影）。 */
  onSubpageChange: (subpage: DesignSubpage) => void;
}) {
  const [projectId] = useProjectId();
  const [leftTab, setLeftTab] = useState<"design" | "empirical" | "global">("design");
  const [rightTab, setRightTab] = useState<"unit" | "plant">("unit");
  // 侧栏宽度+拖宽（拖柄 pointer 主键拖动——宽度记忆 localStorage）
  const [leftWidth, setLeftWidth] = useState(() =>
    readWidth(LEFT_KEY, LEFT_DEFAULT, LEFT_MIN, LEFT_MAX),
  );
  const [rightWidth, setRightWidth] = useState(() =>
    readWidth(RIGHT_KEY, RIGHT_DEFAULT, RIGHT_MIN, RIGHT_MAX),
  );
  const dragRef = useRef<{
    side: "left" | "right";
    startX: number;
    startWidth: number;
  } | null>(null);

  // 拖拽 document 级监听（pointermove/up/cancel——卸载清理；GP-N 同款纪律）
  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      const drag = dragRef.current;
      if (drag === null) {
        return;
      }
      const delta = event.clientX - drag.startX;
      if (drag.side === "left") {
        setLeftWidth(
          Math.max(LEFT_MIN, Math.min(LEFT_MAX, drag.startWidth + delta)),
        );
      } else {
        setRightWidth(
          Math.max(RIGHT_MIN, Math.min(RIGHT_MAX, drag.startWidth - delta)),
        );
      }
    };
    const onUp = () => {
      const drag = dragRef.current;
      if (drag !== null) {
        dragRef.current = null;
        document.body.style.cursor = "";
        // 宽度记忆：拖放落定持久（localStorage——reload 保持）
        if (drag.side === "left") {
          setLeftWidth((width) => {
            window.localStorage.setItem(LEFT_KEY, String(Math.round(width)));
            return width;
          });
        } else {
          setRightWidth((width) => {
            window.localStorage.setItem(RIGHT_KEY, String(Math.round(width)));
            return width;
          });
        }
      }
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      document.removeEventListener("pointercancel", onUp);
    };
    // 常挂监听（dragRef 空转零开销——挂/卸对称免漏）
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
    document.addEventListener("pointercancel", onUp);
    return () => {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      document.removeEventListener("pointercancel", onUp);
      document.body.style.cursor = "";
    };
  }, []);

  /** 拖柄按下（仅主键——启动会话拖拽）。 */
  const onDragStart = (
    side: "left" | "right",
    event: React.PointerEvent<HTMLDivElement>,
  ) => {
    if (event.button !== 0) {
      return;
    }
    dragRef.current = {
      side,
      startX: event.clientX,
      startWidth: side === "left" ? leftWidth : rightWidth,
    };
    document.body.style.cursor = "col-resize";
  };

  const subpage: DesignSubpage = target.subpage ?? "canvas";

  return (
    <section className="wp-v4-design" data-region="design-workspace">
      <div className="wp-v4-design-row">
        {/* 左栏：三 tab+计算回填 */}
        <aside
          className="wp-v4-left"
          data-region="design-left"
          style={{ width: leftWidth }}
        >
          <div
            className="wp-v4-drag"
            data-testid="wp-v4-drag-left"
            title="拖拽调整宽度"
            onPointerDown={(event) => onDragStart("left", event)}
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
                <ParamForm projectId={projectId} unitId={selectedUnitId} />
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
          {/* 计算回填区（自动值——B1 空态；B2 批方案驱动回填） */}
          <section
            style={{
              flex: "none",
              borderTop: "1px solid var(--wp-border-2)",
              padding: "6px 10px 8px",
              maxHeight: "40%",
              overflow: "auto",
            }}
            data-testid="wp-v4-backfill"
          >
            <h4
              style={{
                fontSize: 11,
                color: "var(--wp-text-2)",
                letterSpacing: 1,
                margin: "2px 0 4px",
              }}
            >
              计算回填 · 自动
            </h4>
            <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
              自动值在计算后回填
            </span>
          </section>
        </aside>

        {/* 中列：视图页签+画布/分析表 */}
        <section className="wp-v4-center">
          <div className="wp-v4-vtabs" data-testid="wp-v4-view-tabs">
            <button
              type="button"
              className={`wp-v4-vt${subpage === "canvas" ? " on" : ""}`}
              data-subpage="canvas"
              onClick={() => onSubpageChange("canvas")}
            >
              工艺画布
            </button>
            <button
              type="button"
              className={`wp-v4-vt${subpage === "analysis" ? " on" : ""}`}
              data-subpage="analysis"
              onClick={() => onSubpageChange("analysis")}
            >
              分析表
            </button>
          </div>
          <div className="wp-v4-canvas" data-region="design-canvas">
            {subpage === "canvas" ? (
              projectId === null ? (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "100%",
                    color: "var(--wp-text-2)",
                  }}
                >
                  {NO_PROJECT_HINT}
                </div>
              ) : null
            ) : (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "100%",
                  color: "var(--wp-text-2)",
                }}
              >
                分析表在完成计算后呈现
              </div>
            )}
          </div>
        </section>

        {/* 右栏：两页（选中工艺/全厂） */}
        <aside
          className="wp-v4-right"
          data-region="design-right"
          style={{ width: rightWidth }}
        >
          <div
            className="wp-v4-drag"
            data-testid="wp-v4-drag-right"
            title="拖拽调整宽度"
            onPointerDown={(event) => onDragStart("right", event)}
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
              <div className="wp-v4-sec">
                <h4>
                  {selectedUnitId === null
                    ? "选中工艺 · 方案"
                    : `${selectedUnitId} · 方案`}
                </h4>
                <div
                  style={{
                    border: "1px dashed var(--wp-border-2)",
                    borderRadius: 6,
                    padding: "10px 8px",
                    color: "var(--wp-text-2)",
                    fontSize: 11,
                  }}
                >
                  方案在枚举计算后呈现
                </div>
              </div>
            ) : (
              <>
                <div className="wp-v4-sec">
                  <h4>全厂 · 联合方案</h4>
                  <span style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
                    联合方案在联合枚举后呈现
                  </span>
                </div>
                <div className="wp-v4-sec">
                  <h4>分析面</h4>
                  {ANALYSIS_ENTRIES.map((label) => (
                    <button
                      key={label}
                      type="button"
                      style={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        border: "none",
                        background: "transparent",
                        color: "var(--wp-text)",
                        fontSize: 11.5,
                        padding: "4px 2px",
                        cursor: "pointer",
                      }}
                      onClick={() => onSubpageChange("analysis")}
                    >
                      {label} ›
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </aside>
      </div>
      <DockBar />
    </section>
  );
}
