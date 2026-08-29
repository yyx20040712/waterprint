/**
 * 排序键选择：响应 columns 白名单 Select（D9 服务端分页排序面）。
 *
 * 输入:  columns（solutions 响应列名集——选项白名单）+当前 sort 值
 * 输出:  排序下拉（选项=buildSortOptions(columns)；切换回调 onChange）
 *
 * 规格说明（FE6 批 6b 段四，D9——替换 M0.5 骨架）：
 *   - 选项=响应 columns（服务端白名单 columns∪{cost}——前端只出 columns
 *     内选项；cost 列现状无列不加，概算注入挂账）；
 *   - 服务端恒降序（ascending=False 默认——UI 不提供方向切换，附注文案
 *     呈现）；sort 切换→page 重置 1（solutionsPane 组合面）；
 *   - 排序确定性：sort+page/size 全量进 solutions queryKey（§17.2 前端
 *     缓存规则——输入变自动失效）。
 */
import { Select, Typography } from "antd";

import { buildSortOptions } from "../lib/solutionsView";

export function RankingControls({
  columns,
  value,
  onChange,
}: {
  columns: string[];
  value: string;
  onChange: (sort: string) => void;
}) {
  return (
    <span>
      <Typography.Text type="secondary" style={{ marginRight: 8 }}>
        排序（降序）：
      </Typography.Text>
      <Select
        size="small"
        style={{ minWidth: 180 }}
        value={value}
        options={buildSortOptions(columns)}
        onChange={(next) => onChange(next)}
      />
    </span>
  );
}
