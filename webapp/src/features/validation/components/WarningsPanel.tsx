/**
 * 警告聚合呈现件（T3 前端警告聚合批）：validation 观测 warnings 三分区
 * 渲染（声明级/工况聚合/单工况直通——warning-aggregation.md §3 分区）。
 *
 * 输入:  observation（useValidationQuery 窄化产物——validationView 单源类型）
 * 输出:  纯展示面板三态：validation_available=false →旧结果降级提示条
 *        （无数据行）；warnings 空=整体不渲染（null——零警告不打扰）；
 *        非空=「警告聚合」块+三分区（空分区不渲染）——行=severity 徽标
 *        （语义色 token）+message 全文+meta 行（影响面·code〔mono 小字〕
 *        ·工况键——中列窄面板紧凑单行）；零交互零取数（错误/pending 态
 *        归接线面 analysisPane 副数据分支）
 */
import {
  conditionKeysText,
  partitionWarnings,
  scopeLabel,
  severityLabel,
  severityTone,
  type AggregatedWarningRow,
  type ValidationObservation,
} from "../lib/validationView";

/** 分区小节（标题+行数——空分区由调用方不渲染）。 */
function WarningZone({
  title,
  rows,
  testId,
}: {
  title: string;
  rows: readonly AggregatedWarningRow[];
  testId: string;
}) {
  return (
    <div data-testid={testId} style={{ marginTop: 6 }}>
      <div style={{ fontSize: 10, color: "var(--wp-text-2)", letterSpacing: 1 }}>
        {title} {rows.length}
      </div>
      {rows.map((row) => {
        const tone = severityTone(row.severity);
        // 行 key=去重键三元组（§2 同键不双现——服务端聚合单源）
        const conditions = conditionKeysText(row.condition_keys);
        return (
          <div
            key={`${row.scope}:${row.code}:${row.param_key}`}
            data-testid="wp-v4-warning-row"
            style={{ marginTop: 4 }}
          >
            <div style={{ display: "flex", gap: 6, alignItems: "baseline" }}>
              <span
                style={{
                  flexShrink: 0,
                  fontSize: 10,
                  borderRadius: 3,
                  padding: "0 5px",
                  color: tone.color,
                  background: tone.background,
                }}
              >
                {severityLabel(row.severity)}
              </span>
              <span style={{ fontSize: 11, lineHeight: 1.6 }}>{row.message}</span>
            </div>
            <div
              style={{
                fontSize: 10,
                color: "var(--wp-text-2)",
                fontFamily: "var(--wp-font-mono)",
                marginTop: 1,
              }}
            >
              {scopeLabel(row.scope)} · {row.code}
              {conditions === "" ? "" : ` · ${conditions}`}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** 警告聚合面板（纯展示——接线面=analysisPane 全厂指标面 PlantFace）。 */
export function WarningsPanel({ observation }: { observation: ValidationObservation }) {
  if (!observation.validation_available) {
    // 降级（ADR-012 R1 同精神）：旧结果无 val 件=如实提示，禁伪造空警告
    return (
      <div
        data-testid="wp-v4-validation-unavailable"
        style={{
          fontSize: 11,
          color: "var(--wp-text-2)",
          border: "1px solid var(--wp-border-2)",
          borderRadius: 6,
          padding: "4px 10px",
          marginBottom: 8,
        }}
      >
        结果集无校验观测（旧版本结果）——重算后生成
      </div>
    );
  }
  if (observation.warnings.length === 0) {
    return null; // 零警告不打扰（区块整体不渲染）
  }
  const zones = partitionWarnings(observation.warnings);
  return (
    <div data-testid="wp-v4-warnings-panel" style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: "var(--wp-text-2)", letterSpacing: 1 }}>
        警告聚合 {observation.warnings.length}
      </div>
      {zones.declaration.length > 0 ? (
        <WarningZone
          title="声明级"
          rows={zones.declaration}
          testId="wp-v4-warnings-declaration"
        />
      ) : null}
      {zones.aggregated.length > 0 ? (
        <WarningZone
          title="工况聚合"
          rows={zones.aggregated}
          testId="wp-v4-warnings-aggregated"
        />
      ) : null}
      {zones.single.length > 0 ? (
        <WarningZone
          title="单工况"
          rows={zones.single}
          testId="wp-v4-warnings-single"
        />
      ) : null}
    </div>
  );
}
