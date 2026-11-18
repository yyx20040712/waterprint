/**
 * 警告聚合呈现件（T3 前端警告聚合批）：validation 观测 warnings 三分区
 * 渲染（声明级/工况聚合/单工况直通——warning-aggregation.md §3 分区）。
 *
 * 输入:  observation（useValidationQuery 窄化产物——validationView 单源类型）
 * 输出:  纯展示面板：warnings 非空=「警告聚合」块+三分区（空分区不渲染）
 *        ——行=severity 徽标（语义色 token）+message 全文+meta 行（影响面·
 *        code〔mono 小字〕·工况键——中列窄面板紧凑单行）；validation_
 *        available=false=降级提示条与警告行并行呈现（源 A val 件缺席不吞
 *        源 B 聚合面——server services.validation 降级时仍聚合源 B，锁测
 *        test_validation「源 B 面仍在」同口径）；warnings 空且有 val 件=
 *        整体不渲染（null——零警告不打扰）、空且无 val 件=仅降级条；
 *        零交互零取数（错误/pending 态归接线面 analysisPane 副数据分支）
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

/** 降级提示条（源 A val 件缺席=如实提示，禁伪造空警告——与源 B 警告行
 *  并行呈现，不吞聚合面）。 */
function UnavailableBar() {
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

/** 警告聚合面板（纯展示——接线面=analysisPane 全厂指标面 PlantFace）。 */
export function WarningsPanel({ observation }: { observation: ValidationObservation }) {
  if (observation.warnings.length === 0) {
    // 零警告：有 val 件=整体不渲染（不打扰）；无 val 件=仅降级条（源 B
    // 亦零警告——降级事实仍如实提示，无数据行可渲染）
    return observation.validation_available ? null : <UnavailableBar />;
  }
  const zones = partitionWarnings(observation.warnings);
  return (
    <div data-testid="wp-v4-warnings-panel" style={{ marginBottom: 10 }}>
      {/* 降级条与警告行并行（源 A 缺席≠源 B 缺席——降级不吞源 B 聚合面） */}
      {observation.validation_available ? null : <UnavailableBar />}
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
