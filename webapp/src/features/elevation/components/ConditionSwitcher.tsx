/**
 * 工况切换器：工况键下拉（D9——只读另一索引，未算工况按需触发）。
 *
 * 输入:  conditions（服务端工况键清单）+当前值+切换回调+catalog name_zh
 *        （工况键中文名——工况面 UX 反馈批件 1 接线）
 * 输出:  AntD Select（选项=conditions 序——服务端 sorted 序透传；label=
 *        conditionLabel 工程全称+悬浮原始键）
 *
 * 规格说明（FE7 批 6b 段五，D9；工况面 UX 反馈批件 1）：
 *   - 切换语义=按需触发（§17.1）：onChange 后查询键含 conditionKey
 *     全量进（useElevationQuery queryKey 面）——未算工况首次切换才取数；
 *   - ADR-007 并排对比不在本组件面（单图切换=纵断数据通道现状；
 *     双图并排挂账 UX 批）；
 *   - 件 1（2026-09-12）：选项中文化=conditionLabel 词典（catalog
 *     name_zh select——查询非 UI 态，「受控组件零内部态」口径不破）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop 名
 *     ——FE3 C3 规避先例）；受控组件零内部态。
 */
import { Select, Typography } from "antd";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { conditionLabel, unitNameIndex } from "../../../shared/conditionLabels";

export function ConditionSwitcher({
  conditions,
  value,
  onChange,
}: {
  conditions: string[];
  value: string;
  onChange: (next: string) => void;
}) {
  // 件 1：工况键中文名（catalog name_zh 真源——offline 键拆段消费）
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Typography.Text type="secondary">工况：</Typography.Text>
      <Select
        style={{ minWidth: 200 }}
        value={value}
        options={conditions.map((key) => ({
          value: key,
          label: conditionLabel(key, unitNames),
          title: key,
        }))}
        onChange={(next) => onChange(next)}
      />
    </div>
  );
}
