/**
 * v4 分析表态（B2 结果与方案批 2026-10-09——wireframe-d-v4 屏 3 形；任务书
 * §一.2/§二.③）：中列「分析表」子页——未选单元=全厂指标面〔出水指标
 * 行+全厂对比矩阵〕；选中单元（?node= 生效）=逐单元结果明细满行。
 *
 * 输入:  projectId（useProjectId 单一真相）+selectedUnitId（?node= 对象选中
 *        真相——shellV4 受控）+useCompareQuery/useTrustQuery（全厂面双现行
 *        端点：compare=关键容积行矩阵〔CompareMatrix 呈现件复用〕+trust
 *        effluent=出水指标限值判定行——数据源定形落批档）+unit_detail 新
 *        端点 hook（选中单元满行）+TASK_EVENT 事件桥（apply 重算后失效）
 * 输出:  分析表面板：空态三态（无项目/无结果——引导顶带「全项目计算」钮/
 *        无选中单元=全厂面默认非空态）+stale 横幅（原因微文案+重算入口）
 *        +effluent 指标表+CompareMatrix｜选中单元 rows 满行+端口流量水质段
 *        +warnings 行（formula_ids 数据面不渲染——公式呈现=B6 批）
 *
 * 规格说明（B2 任务书 §二.③/§二.⑤）：
 *   - 只读呈现（无编辑模式——分析表数据面零回写）；
 *   - 行模型=服务端联表满行直渲染（行集==载荷 rows——对账断言在测试面）；
 *   - 空态/错误文案白名单：空态引导/错误提示/stale 原因——零教学性文字；
 *   - stale=提示性（不阻断阅读）；重算入口=POST /api/calc/run 直发
 *     （分析态无画布草稿面——apply 已落盘；zoneBand 顶带钮同链另一入口）。
 */
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useCompareQuery } from "../../features/compare/api/useCompareQuery";
import { CompareMatrix } from "../../features/compare/components/CompareMatrix";
import { useTrustQuery } from "../../features/trust/api/useTrustQuery";
import { formatSolutionValue } from "../../features/solutions/lib/solutionsView";
import {
  useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet,
  useRunCalculationApiCalcRunPost,
} from "../../shared/api/generated/calc/calc";
import { domainGate } from "../../shared/api/sourceGate";
import { TASK_EVENT } from "../../shared/events";
import { analysisFacesPredicate, effluentRows } from "./analysisView";
import { writeTaskParam } from "../solutionsUrlState";

/** 空态引导文案（白名单：空态引导）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「项目」区打开或新建";
const NO_RESULT_HINT = "尚无计算结果——点顶带「全项目计算」钮提交后回看";
const STALE_TEXT = "结果已过期（参数已变更）——重算后本表更新";

/** 错误体码→用户面文案（domainGate 同口径：领域码固定摘要）。 */
const GATE_TEXT = {
  compare: "项目暂无完成的计算结果",
  unitSource: "项目暂无完成的计算结果",
  unitEntry: "该单元不在当前结果快照（未计算或已移除）",
} as const;

/** 出水指标表（effluent 聚合行——指标×工况值+限值+判定；R1 W-effluent：
 *  列集=全行 keys 并集〔非首行截断〕+缺值「—」占位禁伪 0）。 */
function EffluentTable({ effluent }: { effluent: Parameters<typeof effluentRows>[0] }) {
  const rows = effluentRows(effluent);
  // R1 W-effluent：列集=全行并集（首见序——行间工况覆盖面不一不丢列）
  const keySet = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row.values)) {
      keySet.add(key);
    }
  }
  const conditionKeys = [...keySet];
  if (rows.length === 0) {
    return (
      <div style={{ fontSize: 11, color: "var(--wp-text-2)", marginBottom: 10 }}>
        无出水指标数据（诊断缺席或纯提升类项目）
      </div>
    );
  }
  return (
    <table
      className="wp-v4-rt"
      data-testid="wp-v4-effluent-table"
      style={{ marginBottom: 10 }}
    >
      <thead>
        <tr>
          <th>指标</th>
          {conditionKeys.map((key) => (
            <th key={key}>{key === "avg" ? "基准 avg" : key === "design" ? "设计 design" : key}</th>
          ))}
          <th>限值</th>
          <th>判定</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.indicator}>
            <td style={{ textAlign: "left" }}>{row.indicator}</td>
            {conditionKeys.map((key) => {
              const value = row.values[key];
              return (
                <td key={key}>
                  {value === undefined ? (
                    <span style={{ color: "var(--wp-text-2)" }}>—</span>
                  ) : (
                    <span style={{ fontVariantNumeric: "tabular-nums" }}>
                      {formatSolutionValue(value)}
                    </span>
                  )}
                </td>
              );
            })}
            <td>{formatSolutionValue(row.limit)}</td>
            <td>
              <span
                style={{
                  fontSize: 10,
                  borderRadius: 3,
                  padding: "0 5px",
                  color: row.compliant ? "var(--wpv4-ok)" : "var(--wp-error)",
                  background: row.compliant ? "var(--wpv4-ok-bg)" : "#fdeceb",
                }}
              >
                {row.compliant ? "达" : "超"}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** 全厂指标面（未选单元=默认态——非空态）。 */
function PlantFace({ projectId }: { projectId: string }) {
  const query = useCompareQuery(projectId);
  const trustQuery = useTrustQuery(projectId);
  const report = query.data ?? null;
  const trust = trustQuery.data ?? null;

  if (query.isError) {
    // 领域 404=固定摘要+重算引导；网络/窄化错=raw 透出（错误提示白名单）
    const gate = domainGate(query.error, "CompareSourceNotFoundError", GATE_TEXT.compare);
    return (
      <div
        data-testid="wp-v4-analysis-empty"
        style={{ padding: 24, color: "var(--wp-text-2)", fontSize: 12 }}
      >
        {gate.domain ? `${gate.text}——${NO_RESULT_HINT}` : `取数失败：${gate.text}`}
      </div>
    );
  }
  if (report === null) {
    return (
      <div style={{ padding: 24, color: "var(--wp-text-2)", fontSize: 12 }}>
        正在加载分析表…
      </div>
    );
  }
  return (
    <div data-testid="wp-v4-analysis-plant" style={{ padding: "10px 12px", overflow: "auto" }}>
      {report.stale ? <StaleBanner projectId={projectId} /> : null}
      {/* R1 W-trust：取数失败=错误提示（白名单）+加载静默——矩阵面仍在不阻断 */}
      {trustQuery.isError ? (
        <div style={{ fontSize: 11, color: "var(--wp-error)", marginBottom: 8 }}>
          出水指标读取失败：
          {trustQuery.error instanceof Error ? trustQuery.error.message : "未知错误"}
        </div>
      ) : trustQuery.isPending ? null : (
        <EffluentTable effluent={trust?.effluent ?? []} />
      )}
      <CompareMatrix report={report} pinned={null} />
    </div>
  );
}

/** 选中单元明细面（?node= 生效——unit_detail 满行+端口段+warnings）。 */
function UnitFace({
  projectId,
  unitId,
}: {
  projectId: string;
  unitId: string;
}) {
  const query = useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet(
    projectId,
    unitId,
  );
  const detail = query.data ?? null;

  if (query.isError) {
    const error = query.error;
    const sourceGate = domainGate(error, "UnitDetailSourceNotFoundError", GATE_TEXT.unitSource);
    const entryGate = domainGate(error, "UnitDetailEntryNotFoundError", "");
    return (
      <div
        data-testid="wp-v4-analysis-error"
        style={{ padding: 24, fontSize: 12, color: "var(--wp-error)" }}
      >
        {sourceGate.domain
          ? `${sourceGate.text}——${NO_RESULT_HINT}`
          : entryGate.domain
            ? // 单元/工况缺席=服务端消息精确（错误提示白名单——raw 透出）
              error instanceof Error
              ? error.message
              : GATE_TEXT.unitEntry
            : `取数失败：${error instanceof Error ? error.message : "未知错误"}`}
      </div>
    );
  }
  if (detail === null) {
    return (
      <div style={{ padding: 24, color: "var(--wp-text-2)", fontSize: 12 }}>
        正在加载单元结果…
      </div>
    );
  }
  return (
    <div style={{ padding: "10px 12px", overflow: "auto" }}>
      {detail.stale ? <StaleBanner projectId={projectId} /> : null}
      <table className="wp-v4-rt" data-testid="wp-v4-unit-rows">
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>指标</th>
            <th>值</th>
            <th>单位</th>
          </tr>
        </thead>
        <tbody>
          {detail.rows.map((row) => (
            <tr key={row.field_id} data-testid="wp-v4-unit-row">
              <td style={{ textAlign: "left" }}>
                <span title={row.field_id}>{row.label_zh ?? row.field_id}</span>
              </td>
              <td>
                {row.value === null ? (
                  <span style={{ color: "var(--wp-text-2)" }}>—</span>
                ) : (
                  <span style={{ fontVariantNumeric: "tabular-nums" }}>
                    {formatSolutionValue(row.value)}
                  </span>
                )}
              </td>
              <td style={{ color: "var(--wp-text-2)" }}>{row.dim}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* 端口流量水质段（键=投影面直出——unit.port.component 形） */}
      <div
        data-testid="wp-v4-unit-ports"
        style={{ marginTop: 10, fontSize: 11, lineHeight: 1.8 }}
      >
        <div style={{ color: "var(--wp-text-2)", letterSpacing: 1 }}>端口流量 / 水质</div>
        {Object.entries(detail.outflows).map(([key, value]) => (
          <div key={key} style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontFamily: "var(--wp-font-mono)" }}>{key}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>
              {formatSolutionValue(value)}
            </span>
          </div>
        ))}
        {Object.entries(detail.outqualities).map(([key, value]) => (
          <div key={key} style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontFamily: "var(--wp-font-mono)" }}>{key}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>
              {formatSolutionValue(value)}
            </span>
          </div>
        ))}
        {Object.keys(detail.outflows).length === 0 &&
        Object.keys(detail.outqualities).length === 0 ? (
          <span style={{ color: "var(--wp-text-2)" }}>—（无端口数据）</span>
        ) : null}
      </div>
      {/* warnings 行（空则不呈现——§二.③）；formula_ids 数据面不渲染（B6 批） */}
      {detail.warnings.length > 0 ? (
        <div data-testid="wp-v4-unit-warnings" style={{ marginTop: 10 }}>
          <div style={{ fontSize: 11, color: "var(--wp-text-2)", letterSpacing: 1 }}>
            警告 {detail.warnings.length}
          </div>
          {detail.warnings.map((warning, index) => (
            <div
              key={`${warning.source}-${index}`}
              style={{ fontSize: 11, color: "var(--wpv4-warn)", lineHeight: 1.7 }}
            >
              {warning.message}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** stale 横幅（原因微文案+重算入口——分析态直发 run）。 */
function StaleBanner({ projectId }: { projectId: string }) {
  const run = useRunCalculationApiCalcRunPost();
  return (
    <div
      data-testid="wp-v4-analysis-stale"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        fontSize: 11,
        color: "var(--wpv4-warn)",
        background: "var(--wpv4-warn-bg, rgba(138, 97, 0, 0.08))",
        border: "1px solid var(--wp-border-2)",
        borderRadius: 6,
        padding: "4px 10px",
        marginBottom: 8,
      }}
    >
      <span>{STALE_TEXT}</span>
      <button
        type="button"
        data-testid="wp-v4-analysis-rerun"
        disabled={run.isPending}
        onClick={() =>
          run.mutate(
            { data: { project_id: projectId, conditions: [] } },
            {
              onSuccess: (outcome) => {
                writeTaskParam(outcome.task_id);
                window.dispatchEvent(
                  new CustomEvent(TASK_EVENT, { detail: outcome.task_id }),
                );
              },
            },
          )
        }
        style={{
          border: "1px solid var(--wp-border)",
          borderRadius: 4,
          background: "var(--wp-bg-container, #ffffff)",
          color: "var(--wpv4-ac)",
          fontSize: 11,
          padding: "1px 8px",
          cursor: run.isPending ? "default" : "pointer",
        }}
      >
        重算
      </button>
    </div>
  );
}

export function AnalysisPane({
  projectId,
  selectedUnitId,
}: {
  projectId: string | null;
  /** ?node= 对象选中真相（null=全厂面默认态——§二.⑤ 非空态注记）。 */
  selectedUnitId: string | null;
}) {
  // R1a/d1-N6：TASK_EVENT 事件桥自挂（analysisPane 根级——两态〔全厂/
  // 选中单元〕均生效，不依赖 backfillSection 旁路）；失效键=生成键
  // predicate（analysisFacesPredicate 单源——前缀字符串死键根治）。
  const queryClient = useQueryClient();
  useEffect(() => {
    if (projectId === null) {
      return;
    }
    const onTaskParam = () => {
      void queryClient.invalidateQueries({
        predicate: analysisFacesPredicate(projectId),
      });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  if (projectId === null) {
    return (
      <div
        data-testid="wp-v4-analysis-empty"
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
    );
  }
  if (selectedUnitId === null) {
    return <PlantFace projectId={projectId} />;
  }
  return <UnitFace projectId={projectId} unitId={selectedUnitId} />;
}
