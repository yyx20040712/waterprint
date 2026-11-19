/**
 * v4 工况区（b2 壳重组批独立入口→b4 功能面重涂 II 批 2026-11-19 稿
 * compare.html 两栏重制：左=工况与基准〔活动工况清单+锁定基准+视图操作
 * 说明〕+右=指标矩阵面板〔页头+单元筛选+CompareMatrix〕；沿革
 * compare=AnalysisPane 全厂面内嵌段〔B2〕→b2 独立入口〔全幅裸矩阵〕
 * →b4 信息组织重造〔分析页内嵌矩阵保持不动〕）。
 *
 * 输入:  useProjectId+useCompareQuery（compare 查询——CompareReport
 *        condition_keys/metrics/warnings）+TASK_EVENT（事件桥——apply
 *        重算后失效）+StaleBanner（analysisPane 导出件复用）+
 *        conditionLabel/unitNameIndex（工况/单元中文名单源）
 * 输出:  工况对比面：空态三态（无项目/无结果/取数失败）+stale 横幅+
 *        左栏（活动工况行〔纳入/移出矩阵列——客户端视图过滤〕+锁定
 *        基准区〔锁定/重锁/解除+过期/失效态〕）+指标矩阵面板（单元
 *        筛选+CompareMatrix filtered report+pinned）
 *
 * 规格说明（b4 批准稿 compare.html——信息组织重造，数据流零变）：
 *   - 锁定基准=视图操作（稿注「锁定是视图操作，不触发重算」）：zone
 *     级 useState 承载 PinState〔compareView 既有三件 pinOf/isPinStale/
 *     filterLivePins 消费面接线——pinned_hash=报告 design_hash，重算后
 *     过期判定同稿语义〕；无持久化 API 不虚造——入口切换即复位（本
 *     会话视图态）；
 *   - 活动工况行=列纳入开关（客户端过滤 condition_keys——矩阵/极值
 *     标注随可见列集重算〔rowExtremes 消费过滤后键集〕，全量数据仍在
 *     内存零请求）；
 *   - 单元筛选=metrics unit_id 集数据驱动（全量默认——缺省零过滤）；
 *   - 错误面=domainGate 领域码固定摘要+重算引导（GATE_TEXT 同口径）；
 *     TASK_EVENT 失效键=compare 生成键（精确域）。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useCompareQuery } from "../../features/compare/api/useCompareQuery";
import { CompareMatrix } from "../../features/compare/components/CompareMatrix";
import {
  filterLivePins,
  isPinStale,
  type CompareReport,
  type PinState,
} from "../../features/compare/lib/compareView";
import { useProjectId } from "../useProjectId";
import { TASK_EVENT } from "../../shared/events";
import { domainGate } from "../../shared/api/sourceGate";
import { conditionLabel, unitNameIndex } from "../../shared/conditionLabels";
import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import { StaleBanner } from "./analysisPane";

/** 空态引导文案（白名单：空态引导——analysisPane 同口径）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";
const NO_RESULT_HINT = "尚无计算结果——点顶栏「全项目计算」钮提交后回看";
/** 领域 404 固定摘要（analysisPane GATE_TEXT.compare 同文案单源口径）。 */
const GATE_COMPARE_TEXT = "项目暂无完成的计算结果";
/** 锁定区说明（稿 compare.html 左栏 notice——视图操作语义）。 */
const PIN_NOTICE = "锁定是视图操作，不触发重算。基准过期与结果 stale 分开提示。";
/** 未锁定空态（白名单：空态引导）。 */
const PIN_EMPTY_HINT = "未锁定——点「锁定为基准」以当前可见工况为基准标注 ★";

export function CompareZone() {
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();
  const query = useCompareQuery(projectId);
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};

  // 视图态三件（b4——稿左栏信息组织；均为客户端呈现过滤零数据流变更）
  const [offKeys, setOffKeys] = useState<readonly string[]>([]);
  const [unitFilter, setUnitFilter] = useState<string>("");
  const [pin, setPin] = useState<PinState | null>(null);

  // TASK_EVENT 事件桥（analysisPane 根级同制——apply 重算后失效本面）
  useEffect(() => {
    if (projectId === null) {
      return;
    }
    const onTaskParam = () => {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/compare/${projectId}`],
      });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  if (projectId === null) {
    return (
      <section
        data-region="compare-matrix"
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--wp-text-2)",
          fontSize: 12,
        }}
      >
        {NO_PROJECT_HINT}
      </section>
    );
  }
  if (query.isError) {
    // 领域 404=固定摘要+重算引导；网络/窄化错=raw 透出（错误提示白名单）
    const gate = domainGate(query.error, "CompareSourceNotFoundError", GATE_COMPARE_TEXT);
    return (
      <section
        data-region="compare-matrix"
        data-testid="wp-v4-compare-error"
        style={{ flex: 1, padding: 24, color: "var(--wp-text-2)", fontSize: 12, overflow: "auto" }}
      >
        {gate.domain ? `${gate.text}——${NO_RESULT_HINT}` : `取数失败：${gate.text}`}
      </section>
    );
  }
  if (query.data === undefined || query.data === null) {
    return (
      <section
        data-region="compare-matrix"
        style={{ flex: 1, padding: 24, color: "var(--wp-text-2)", fontSize: 12 }}
      >
        正在加载工况对比…
      </section>
    );
  }
  return (
    <section
      data-region="compare-matrix"
      data-testid="wp-v4-compare-plant"
      style={{ flex: 1, minWidth: 0, display: "flex" }}
    >
      <CompareFace
        report={query.data}
        projectId={projectId}
        unitNames={unitNames}
        offKeys={offKeys}
        onOffKeysChange={setOffKeys}
        unitFilter={unitFilter}
        onUnitFilterChange={setUnitFilter}
        pin={pin}
        onPinChange={setPin}
      />
    </section>
  );
}

/** 有数据面（两栏——左工况与基准/右矩阵面板；props 面=视图态上提）。 */
function CompareFace({
  report,
  projectId,
  unitNames,
  offKeys,
  onOffKeysChange,
  unitFilter,
  onUnitFilterChange,
  pin,
  onPinChange,
}: {
  report: CompareReport;
  projectId: string;
  unitNames: Record<string, string>;
  offKeys: readonly string[];
  onOffKeysChange: (keys: readonly string[]) => void;
  unitFilter: string;
  onUnitFilterChange: (unit: string) => void;
  pin: PinState | null;
  onPinChange: (pin: PinState | null) => void;
}) {
  // 可见工况列集（客户端过滤——全量减移出键；视图面缺省全量）
  const activeKeys = useMemo(
    () => report.condition_keys.filter((key) => !offKeys.includes(key)),
    [report.condition_keys, offKeys],
  );
  // 矩阵报告（列集过滤投影——rowExtremes 随可见列重算；metrics 全量内存零请求）
  const filteredReport = useMemo<CompareReport>(
    () => ({ ...report, condition_keys: activeKeys }),
    [report, activeKeys],
  );
  // 单元筛选选项（metrics unit_id 集数据驱动+中文名）
  const unitOptions = useMemo(() => {
    const ids = [...new Set(report.metrics.map((metric) => metric.unit_id))];
    return ids.sort((a, b) =>
      (unitNames[a] ?? a).localeCompare(unitNames[b] ?? b, "zh-Hans-CN"),
    );
  }, [report.metrics, unitNames]);
  const visibleMetrics = useMemo(
    () =>
      unitFilter === ""
        ? report.metrics
        : report.metrics.filter((metric) => metric.unit_id === unitFilter),
    [report.metrics, unitFilter],
  );
  const matrixReport = useMemo<CompareReport>(
    () => ({ ...filteredReport, metrics: visibleMetrics }),
    [filteredReport, visibleMetrics],
  );

  // 锁定基准派生面（compareView 三件——过期/存活/失效语义单源）
  const pinStale = isPinStale(pin, report);
  const { live, expired } = filterLivePins(pin?.pinned ?? [], report.condition_keys);

  /** 工况行开关（移出/纳入矩阵列——客户端视图过滤）。 */
  const toggleKey = (key: string) => {
    onOffKeysChange(
      offKeys.includes(key)
        ? offKeys.filter((item) => item !== key)
        : [...offKeys, key],
    );
  };

  return (
    <>
      <aside className="wp-v4-pane left" data-region="compare-conditions">
        <div className="wp-v4-pane-head">
          <h3>工况与基准</h3>
          <span className="wp-v4-badge">{report.condition_keys.length} 工况</span>
        </div>
        <div className="wp-v4-pane-body">
          <div className="wp-v4-insp-sec">
            <h4>活动工况</h4>
            {report.condition_keys.map((key) => {
              const on = activeKeys.includes(key);
              const pinned = pin?.pinned.includes(key) ?? false;
              return (
                <button
                  key={key}
                  type="button"
                  data-testid={`wp-v4-compare-cond-${key}`}
                  aria-pressed={on}
                  title={key}
                  onClick={() => toggleKey(key)}
                  className="wp-v4-row"
                  style={{ minHeight: 32, gap: 7, fontSize: 11.5 }}
                >
                  <span
                    aria-hidden
                    style={{
                      width: 13,
                      height: 13,
                      flex: "none",
                      display: "inline-grid",
                      placeItems: "center",
                      border: `1px solid ${on ? "var(--wp-accent)" : "var(--wp-border)"}`,
                      borderRadius: 3,
                      background: on ? "var(--wp-accent)" : "transparent",
                      color: "var(--wp-on-accent)",
                      fontSize: 10,
                      lineHeight: 1,
                    }}
                  >
                    {on ? "✓" : ""}
                  </span>
                  <span
                    style={{
                      minWidth: 0,
                      flex: 1,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {conditionLabel(key, unitNames)}
                  </span>
                  {pinned ? (
                    <span style={{ color: "var(--wp-accent)", flex: "none" }}>★</span>
                  ) : null}
                  <span
                    style={{
                      color: "var(--wp-text-3)",
                      fontFamily: "var(--wp-font-mono)",
                      fontSize: 10,
                      flex: "none",
                    }}
                  >
                    {key}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="wp-v4-insp-sec">
            <h4
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 6,
              }}
            >
              锁定基准
              {pinStale ? (
                <span className="wp-v4-badge warn">基准已过期</span>
              ) : expired.length > 0 ? (
                <span className="wp-v4-badge warn">{expired.length} 项失效</span>
              ) : pin !== null ? (
                <span className="wp-v4-badge ok">已锁定</span>
              ) : null}
            </h4>
            {pin === null ? (
              <p data-testid="wp-v4-compare-pin-empty" style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
                {PIN_EMPTY_HINT}
              </p>
            ) : (
              <div className="wp-v4-list">
                {live.map((key) => (
                  <div key={key} className="wp-v4-row" style={{ minHeight: 32 }}>
                    <span style={{ color: "var(--wp-accent)", flex: "none" }}>★</span>
                    <span className="main">
                      <span className="t">{conditionLabel(key, unitNames)}</span>
                      <span className="s">
                        {key} · hash {pin.pinned_hash.slice(0, 8)}
                        {pinStale ? "，已过期" : "，仍有效"}
                      </span>
                    </span>
                  </div>
                ))}
                {expired.map((key) => (
                  <div
                    key={key}
                    className="wp-v4-row"
                    style={{ minHeight: 32, opacity: 0.65 }}
                  >
                    <span style={{ color: "var(--wp-text-3)", flex: "none" }}>★</span>
                    <span className="main">
                      <span className="t">{conditionLabel(key, unitNames)}</span>
                      <span className="s">{key} · 已移除，重新锁定可清理</span>
                    </span>
                  </div>
                ))}
              </div>
            )}
            <button
              type="button"
              data-testid="wp-v4-compare-pin-set"
              disabled={activeKeys.length === 0}
              onClick={() =>
                onPinChange({ pinned: [...activeKeys], pinned_hash: report.design_hash })
              }
              style={{
                width: "100%",
                marginTop: 10,
                border: "1px solid var(--wp-accent)",
                borderRadius: 4,
                background: activeKeys.length === 0 ? "var(--wp-bg-deep)" : "var(--wp-accent)",
                color: activeKeys.length === 0 ? "var(--wp-text-3)" : "var(--wp-on-accent)",
                fontSize: 11,
                padding: "3px 8px",
                cursor: activeKeys.length === 0 ? "default" : "pointer",
              }}
            >
              {pin === null ? "锁定为基准" : "重新锁定当前工况"}
            </button>
            {pin !== null ? (
              <button
                type="button"
                data-testid="wp-v4-compare-pin-clear"
                onClick={() => onPinChange(null)}
                style={{
                  width: "100%",
                  marginTop: 6,
                  border: "1px solid var(--wp-border)",
                  borderRadius: 4,
                  background: "transparent",
                  color: "var(--wp-text-2)",
                  fontSize: 11,
                  padding: "3px 8px",
                  cursor: "pointer",
                }}
              >
                解除锁定
              </button>
            ) : null}
          </div>
          <div className="wp-v4-pane-foot">{PIN_NOTICE}</div>
        </div>
      </aside>
      <div
        style={{
          flex: 1,
          minWidth: 0,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
          padding: "14px 16px",
        }}
        data-region="compare-panel"
      >
        {report.stale ? <StaleBanner projectId={projectId} /> : null}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 12,
            flexWrap: "wrap",
            marginBottom: 12,
          }}
        >
          <div>
            <h2 style={{ fontSize: 17 }}>多工况对比</h2>
            <p style={{ marginTop: 3, color: "var(--wp-text-2)", fontSize: 11.5 }}>
              指标按单元与输出字段排列，行内最大值加粗、最小值加下划线；全等行零标注。
            </p>
          </div>
        </div>
        <section className="wp-wb-panel" data-testid="wp-v4-compare-matrix-panel">
          <div className="wp-wb-panel-head">
            <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
              <h3>指标矩阵</h3>
              <span className="wp-v4-badge" title={report.task_id}>
                最近完成计算 t{report.task_id.slice(0, 8)}
              </span>
            </div>
            <div className="aux">
              <label
                htmlFor="wp-v4-compare-unit-filter"
                style={{ color: "var(--wp-text-2)", fontSize: 11 }}
              >
                筛选单元
              </label>
              <select
                id="wp-v4-compare-unit-filter"
                data-testid="wp-v4-compare-unit-filter"
                value={unitFilter}
                onChange={(event) => onUnitFilterChange(event.target.value)}
                style={{
                  border: "1px solid var(--wp-border)",
                  borderRadius: 4,
                  background: "var(--wp-bg-elevated)",
                  color: "var(--wp-text)",
                  fontSize: 11,
                  padding: "2px 6px",
                }}
              >
                <option value="">全部单元</option>
                {unitOptions.map((unitId) => (
                  <option key={unitId} value={unitId}>
                    {unitNames[unitId] ?? unitId}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ padding: "8px 12px 12px" }}>
            <CompareMatrix report={matrixReport} pinned={pin?.pinned ?? null} />
          </div>
        </section>
      </div>
    </>
  );
}
