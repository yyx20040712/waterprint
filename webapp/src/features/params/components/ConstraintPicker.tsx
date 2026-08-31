/**
 * 约束勾选：constraint_kb 条目勾选集（CP1 实装——枚举 options.constraints 通道）。
 *
 * 输入:  ConstraintEntryView[]（shared 目录窄化产物——solutionsPane 注入
 *        供选子集）+当前选中 key 集+变更回调
 * 输出:  勾选集变更（提交给方案过滤——枚举请求 options.constraints 三键载荷）
 *
 * 规格说明（CP1 D6 2026-08-31；骨架头注规格兑现：「条目按引用键显示
 *   （限值出处可见）」）：
 *   - 纯展示组件（数据/过滤归 lib/constraintPicker 纯函数+挂载方）：
 *     Checkbox.Group 受控；每条 label=kb label+Tooltip（source 出处+
 *     value_basis 数值溯源——限值出处可见规格）；
 *   - 选中集=key 集（payload 投影归挂载方 toPayloadItems——severity
 *     不入载荷面在彼处收口）；空目录渲染 null（无供选条目不占位）；
 *   - kb 1.0.0 起草态：条目出处含「待追认」注记原样透出（醒目标注
 *     纪律——UI 不遮蔽数据面状态）。
 */
import { Checkbox, Tooltip } from "antd";

import type { ConstraintEntryView } from "../lib/constraintPicker";

export function ConstraintPicker({
  entries,
  selectedKeys,
  onChange,
}: {
  entries: ConstraintEntryView[];
  selectedKeys: string[];
  onChange: (next: string[]) => void;
}) {
  if (entries.length === 0) {
    return null; // 无供选条目（单元未选/kb 无适配条目）不占位
  }
  return (
    <Checkbox.Group
      value={selectedKeys}
      onChange={(values) => onChange(values.map(String))}
      options={entries.map((entry) => ({
        value: entry.key,
        label: (
          <Tooltip title={`${entry.source}｜数值溯源：${entry.value_basis}`}>
            <span>{entry.label}</span>
          </Tooltip>
        ),
      }))}
    />
  );
}
