/**
 * 无解诊断面板：done+feasible_count=0 合法终态的只读诊断呈现（D8）。
 *
 * 输入:  diagnosis（任务 result 载荷弱类型字段——{minimal_conflicts,
 *        fail_counts, suggestions} 形状，worker.py:314-321）
 * 输出:  三段只读呈现（最小冲突集/失败计数/调参建议——非法项宽容跳过）
 *
 * 规格说明（FE6 批 6b 段四，D8——替换 M0.5 骨架；无解=done+
 *   feasible_count=0 合法终态非 failed——test_enumeration.py:88-103 实证）：
 *   - 弱类型三段窄化只读呈现（组件内联——薄壳不测面，FE5 先例）：
 *     minimal_conflicts=[[键,...],...]（极小冲突集）/fail_counts={键:行数}/
 *     suggestions=[{param_key,direction,magnitude,basis,affected_conflicts,
 *     expected_effect}]（core Suggestion dataclass asdict 形）；
 *   - 「建议条目点击跳转参数面板」不建——跨标签联动挂账 UX 批（简报
 *     白名单 9 注记；参数面板编辑经 canvas 标签手动路径）；
 *   - 持久可追溯（§19.3 反馈三通道——只读呈现不清失，随任务态常驻）。
 */
import { Card, Descriptions, Typography } from "antd";

/** 建议条目（core/waterprint/solution/diagnose.py Suggestion asdict 形）。 */
type SuggestionItem = {
  paramKey: string;
  direction: string;
  magnitude: number | null;
  basis: string;
  affectedConflicts: string[];
  expectedEffect: string;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 三段窄化（宽容：形状异常段跳过呈现，不整面板崩）。 */
function narrowDiagnosis(diagnosis: unknown): {
  conflicts: string[][];
  failCounts: [string, number][];
  suggestions: SuggestionItem[];
} {
  const raw = isRecord(diagnosis) ? diagnosis : {};
  const conflicts: string[][] = [];
  const conflictsRaw = raw["minimal_conflicts"];
  if (Array.isArray(conflictsRaw)) {
    for (const group of conflictsRaw) {
      if (
        Array.isArray(group) &&
        group.every((key) => typeof key === "string")
      ) {
        conflicts.push(group as string[]);
      }
    }
  }
  const failCounts: [string, number][] = [];
  const countsRaw = raw["fail_counts"];
  if (isRecord(countsRaw)) {
    for (const [key, count] of Object.entries(countsRaw)) {
      if (typeof count === "number" && Number.isFinite(count)) {
        failCounts.push([key, count]);
      }
    }
  }
  const suggestions: SuggestionItem[] = [];
  const suggestionsRaw = raw["suggestions"];
  if (Array.isArray(suggestionsRaw)) {
    for (const item of suggestionsRaw) {
      if (!isRecord(item)) {
        continue;
      }
      const paramKey = item["param_key"];
      const direction = item["direction"];
      if (typeof paramKey !== "string" || typeof direction !== "string") {
        continue;
      }
      const magnitude = item["magnitude"];
      const affected = item["affected_conflicts"];
      suggestions.push({
        paramKey,
        direction,
        magnitude: typeof magnitude === "number" ? magnitude : null,
        basis: typeof item["basis"] === "string" ? item["basis"] : "",
        affectedConflicts:
          Array.isArray(affected) &&
          affected.every((key) => typeof key === "string")
            ? (affected as string[])
            : [],
        expectedEffect:
          typeof item["expected_effect"] === "string"
            ? item["expected_effect"]
            : "",
      });
    }
  }
  return { conflicts, failCounts, suggestions };
}

export function DiagnosisPanel({ diagnosis }: { diagnosis: unknown }) {
  const { conflicts, failCounts, suggestions } = narrowDiagnosis(diagnosis);
  return (
    <Card size="small" title="无解诊断（枚举完成但可行方案数为 0）">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="最小冲突集">
          {conflicts.length === 0 ? (
            <Typography.Text type="secondary">（载荷缺失）</Typography.Text>
          ) : (
            conflicts.map((group, index) => (
              <div key={index}>
                {index + 1}. 冲突 {group.join("、")}
              </div>
            ))
          )}
        </Descriptions.Item>
        <Descriptions.Item label="失败计数">
          {failCounts.length === 0 ? (
            <Typography.Text type="secondary">（载荷缺失）</Typography.Text>
          ) : (
            failCounts.map(([key, count]) => (
              <div key={key}>
                {key}：{count} 行不可行
              </div>
            ))
          )}
        </Descriptions.Item>
        <Descriptions.Item label="调参建议">
          {suggestions.length === 0 ? (
            <Typography.Text type="secondary">（载荷缺失）</Typography.Text>
          ) : (
            suggestions.map((item, index) => (
              <div key={`${item.paramKey}:${index}`}>
                {item.paramKey}：{item.direction}
                {item.magnitude !== null ? `（幅度 ${item.magnitude}）` : ""}
                ——{item.expectedEffect}
                {item.affectedConflicts.length > 0
                  ? `（关联冲突 ${item.affectedConflicts.join("、")}）`
                  : ""}
                <Typography.Paragraph
                  type="secondary"
                  style={{ fontSize: 11, marginBottom: 0 }}
                >
                  依据：{item.basis}
                </Typography.Paragraph>
              </div>
            ))
          )}
        </Descriptions.Item>
      </Descriptions>
      <Typography.Paragraph type="secondary" style={{ fontSize: 11, marginBottom: 0 }}>
        建议条目点击跳转参数面板挂账 UX 批——请经「工艺画布」标签编辑参数后重新提交枚举。
      </Typography.Paragraph>
    </Card>
  );
}
