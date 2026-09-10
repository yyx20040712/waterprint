/**
 * 枚举提交条（P0-2 行数预算修抽取自 solutionsPane——app 组合层件：
 * ConstraintPicker[features/params] 与 unitOptionLabel[features/solutions]
 * 跨 feature 组合归本层，分层红线不破）：单元下拉+约束勾选+「提交枚举」
 * 钮+提交/清单两错误回显（纯展示——提交载荷逻辑归 pane）。
 *
 * 输入:  units/nameById（下拉选项源）+unitId/onUnitChange+约束三参
 *        （entries/selectedKeys/onChange）+enumeratePending/onEnumerate/
 *        enumerateError+unitsLoading/unitsError
 * 输出:  提交条（flex 行）+两错误行
 *
 * 规格说明（FE6 D8/CP1/CP2 沿革——逻辑零变更纯抽取）：
 *   - 下拉 label=unitOptionLabel（B2 扩面：manifest 中文名/builtin 后缀/
 *     英文 id 诚实回退；value=node id 零漂移）；
 *   - 单元切换不清空勾选（CP2 D4——持久全集∩供选面）；
 *   - 提交钮 disabled=unitId null；载荷（R-3 本组投影空回 null）归 pane
 *     onEnumerate 回调——组件零业务逻辑；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useMemo } from "react";
import { Button, Select, Typography } from "antd";

import { useUnitCatalog } from "../features/params/api/useUnitCatalog";

import { ConstraintPicker } from "../features/params/components/ConstraintPicker";
import type { ConstraintEntryView } from "../features/params/lib/constraintPicker";
import { unitOptionLabel } from "../features/solutions/lib/solutionsFields";
import type { UnitOptionRef } from "../features/solutions/lib/solutionsFields";

export function EnumerateBar({
  units,
  unitId,
  onUnitChange,
  constraintEntries,
  constraintKeys,
  onConstraintChange,
  enumeratePending,
  onEnumerate,
  enumerateError,
  unitsLoading,
  unitsError,
}: {
  units: readonly UnitOptionRef[];
  unitId: string | null;
  onUnitChange: (value: string) => void;
  constraintEntries: readonly ConstraintEntryView[];
  constraintKeys: readonly string[];
  onConstraintChange: (nextKeys: string[]) => void;
  enumeratePending: boolean;
  onEnumerate: () => void;
  enumerateError: string | null;
  unitsLoading: boolean;
  unitsError: string | null;
}) {
  // B2 扩面：目录中文名查询面（未就绪/键缺席=英文 id 诚实回退不阻断）
  // ——自 pane 移入（行数预算修+内聚：label 构建归提交条）
  const catalogQuery = useUnitCatalog();
  const nameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const entry of catalogQuery.data?.units ?? []) {
      map.set(entry.unit_id, entry.name_zh);
    }
    return map;
  }, [catalogQuery.data]);
  return (
    <>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Select
          style={{ minWidth: 260 }}
          value={unitId ?? undefined}
          loading={unitsLoading}
          status={unitsError !== null ? "error" : undefined}
          options={units.map((unit) => ({
            // B2 扩面：label 形态收口 solutionsFields.unitOptionLabel
            // （manifest 纯中文/builtin 中文名+（node_id）后缀/缺席英文
            // id 诚实回退；value 仍 node id 零漂移）
            value: unit.unitId,
            label: unitOptionLabel(unit, nameById),
          }))}
          onChange={(value) => {
            onUnitChange(value);
            // CP2 D4：单元切换不清空勾选（持久全集∩供选面——切回再现）
          }}
        />
        <ConstraintPicker
          entries={[...constraintEntries]}
          selectedKeys={[...constraintKeys]}
          onChange={onConstraintChange}
        />
        <Button
          type="primary"
          loading={enumeratePending}
          disabled={unitId === null}
          onClick={onEnumerate}
        >
          提交枚举
        </Button>
        {enumerateError !== null ? (
          <Typography.Text type="danger">提交失败：{enumerateError}</Typography.Text>
        ) : null}
      </div>
      {unitsError !== null ? (
        <Typography.Paragraph type="danger">单元清单加载失败：{unitsError}</Typography.Paragraph>
      ) : null}
    </>
  );
}
