/**
 * 单位造价指标对照卡：带内/偏离状态（语义色）+未校核灰面。
 *
 * 输入:  CostView.indicators（readings 五键+checked——窄化门保证 status 域）
 * 输出:  指标校核卡片（OK=绿合格/WARN=橙警告/checked=false=灰「未校核」）
 *
 * 规格说明（FE8 批 6b 段六，D6；骨架实装替换）：
 *   - 语义色纪律（§19.3「绿合格/橙警告」）：OK→green/WARN→orange——
 *     WARN 是诚实读数（偏离经验带非阻塞，core indicators R2），如实
 *     橙警不美化成绿；value+band+reason 逐字段呈现（禁只报结论）；
 *   - checked=false=灰「未校核」显式呈现（core R4 禁静默通过——空带
 *     属数据包缺该工程类型条目，消费方禁当通过）；
 *   - value/band 显示层格式化（千分位两位小数）；薄壳不测（投影层
 *     estimateView.test 承担 status 域/checked 面契约）。
 */
import { Card, Descriptions, Empty, Tag, Typography } from "antd";

import type { CostView } from "../lib/estimateView";

/** 数值显示格式（千分位两位小数——与 EstimateTable 金额面同款）。 */
function formatValue(value: number): string {
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** 指标对照卡（D6：语义色+未校核灰面）。 */
export function IndicatorsCard({ view }: { view: CostView }) {
  const indicators = view.indicators;
  if (!indicators.checked) {
    return (
      <Card size="small" title="单位造价指标校核">
        {/* core R4：空带=显式未校核（灰面呈现，禁静默通过） */}
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <Typography.Text type="secondary">
              未校核——数据包缺该工程类型指标带（checked=false 显式呈现）
            </Typography.Text>
          }
        />
      </Card>
    );
  }
  return (
    <Card size="small" title="单位造价指标校核">
      <Descriptions
        size="small"
        column={1}
        items={indicators.readings.map((reading) => ({
          key: reading.indicator_key,
          label: (
            <span>
              {reading.indicator_key}
              <Tag
                color={reading.status === "OK" ? "green" : "orange"}
                style={{ marginLeft: 8 }}
              >
                {reading.status === "OK" ? "合格" : "警告"}
              </Tag>
            </span>
          ),
          children: (
            <span>
              实测 {formatValue(reading.value)}（经验带{" "}
              {formatValue(reading.band.min)}~{formatValue(reading.band.max)}
              ）——{reading.reason}
            </span>
          ),
        }))}
      />
    </Card>
  );
}
