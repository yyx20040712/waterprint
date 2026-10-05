/**
 * 检修观测卡（UF-61① FE 观测面——2A1 消费批）：maint.* 三面逐节点×逐工况
 * 纯展示（kb 条目 pass/fail/ratio 分化键/fixgeom 裕度）。
 *
 * 输入:  ValidationObservation 窄化产物（useValidationQuery select 通道）+
 *        catalog name_zh（节点头中文名——工况行 label 取数为 catalog 查询
 *        非业务态，纯展示口径不破）
 * 输出:  纯展示组件（无取数无路由——trustPane 装配壳消费）
 *
 * 规格说明（2A1 消费批 D5；TrustReportView 展示先例同构）：
 *   - **只渲染观测面（nodes/kb_injected/validation_available/stale）——
 *     不渲染 warnings 聚合行**（T3 批面——UF-18 登记册口径，禁搭车扩面）；
 *   - 降级态三面：kb_injected=false→「kb 未注入」注记（观测 kb 面为空
 *     的根因呈现）；validation_available=false→降级蓝条（旧结果无校验件
 *     ——ADR-012 R1「已算但无数据」与「未算」显式区分同族）；stale→黄条
 *     重算提示（trust 状态条同款语义）；
 *   - 空态：nodes 无 faces 且 kb_injected→「无可观测检修工况」（受检
 *     单元集为空/无 maint 键的自然态）；
 *   - 节点头：catalog name_zh+any_fail 故障灯（nodeFailed 纯逻辑）；
 *     逐工况行：kb 条目 pass/fail Tag（正绿负红——marginTone 同纪律；
 *     severity 语义色映射归 T3 聚合行面）+ratio 分化键 field→值+fixgeom
 *     归一裕度（<0=固定几何超载深度）。
 */
import { Alert, Card, Descriptions, Empty, Table, Tag, Typography } from "antd";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { conditionLabel, unitNameIndex } from "../../../shared/conditionLabels";
import {
  formatFixgeom,
  formatRatio,
  nodeFailed,
  observationDegradation,
  type NodeObservation,
  type ValidationObservation,
} from "../lib/maintenanceView";

/** 节点头中文名索引（catalog name_zh 真源——TrustReportView 同 hook 共缓存）。 */
function useUnitNames(): Record<string, string> {
  return (
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {}
  );
}

function NodeSection({
  node,
  unitNames,
}: {
  node: NodeObservation;
  unitNames: Record<string, string>;
}) {
  const rows = node.faces.flatMap((face) => [
    {
      key: `${face.condition_key}:summary`,
      condition_key: face.condition_key,
      kbEntries: Object.entries(face.kb),
      ratioEntries: Object.entries(face.ratio),
      fixgeom_min: face.fixgeom_min,
    },
  ]);
  return (
    <Card
      size="small"
      title={
        <span>
          {unitNames[node.node_id] ?? node.node_id}
          <Tag
            color={nodeFailed(node) ? "red" : "green"}
            style={{ marginLeft: 8 }}
          >
            {nodeFailed(node) ? "检修越门" : "检修通过"}
          </Tag>
        </span>
      }
      style={{ marginBottom: 12 }}
      data-testid="wp-maintenance-node"
    >
      {rows.length === 0 ? (
        <Typography.Text type="secondary">本节点无可观测检修工况。</Typography.Text>
      ) : (
        <Table
          size="small"
          rowKey="key"
          pagination={false}
          dataSource={rows}
          columns={[
            {
              title: "工况",
              dataIndex: "condition_key",
              render: (key: string) => (
                <span title={key}>{conditionLabel(key, unitNames)}</span>
              ),
            },
            {
              title: "kb 条目（通过/越门）",
              dataIndex: "kbEntries",
              render: (entries: [string, boolean][]) =>
                entries.length === 0 ? (
                  <Typography.Text type="secondary">—</Typography.Text>
                ) : (
                  entries.map(([key, passed]) => (
                    <Tag key={key} color={passed ? "green" : "red"} title={key}>
                      {passed ? "通过" : "越门"} {key}
                    </Tag>
                  ))
                ),
            },
            {
              title: "分化字段（offline/design）",
              dataIndex: "ratioEntries",
              render: (entries: [string, number][]) =>
                entries.length === 0 ? (
                  <Typography.Text type="secondary">—</Typography.Text>
                ) : (
                  <Descriptions
                    size="small"
                    column={1}
                    items={entries.map(([field, value]) => ({
                      key: field,
                      label: field,
                      children: formatRatio(value),
                    }))}
                  />
                ),
            },
            {
              title: "固定几何裕度",
              dataIndex: "fixgeom_min",
              align: "right",
              render: (value: number | null) =>
                value === null ? (
                  <Typography.Text type="secondary">—</Typography.Text>
                ) : (
                  <Tag color={value >= 0 ? "green" : "red"}>
                    {formatFixgeom(value)}
                  </Tag>
                ),
            },
          ]}
        />
      )}
    </Card>
  );
}

/** 检修观测卡主体（纯展示——数据/路由/取数均在 trustPane 装配壳）。 */
export function MaintenanceObservationView({
  observation,
}: {
  observation: ValidationObservation;
}) {
  const unitNames = useUnitNames();
  const degradation = observationDegradation(observation);
  return (
    <div data-testid="wp-maintenance-observation" style={{ marginTop: 12 }}>
      <Typography.Title level={5} style={{ marginTop: 0 }}>
        检修观测（kb 执法面 / 参数分化 / 固定几何裕度）
      </Typography.Title>
      {degradation.valMissing && (
        <Alert
          type="info"
          showIcon
          data-testid="wp-maintenance-val-missing"
          title="本结果无校验件（旧版本计算或校验件缺失/损坏）——重新提交计算后可获取。"
          style={{ marginBottom: 12 }}
        />
      )}
      {degradation.kbMissing && (
        <Alert
          type="warning"
          showIcon
          data-testid="wp-maintenance-kb-missing"
          title="kb 未注入：本结果计算时约束知识库未参与（kb 执法面为空）——重算后可获取。"
          style={{ marginBottom: 12 }}
        />
      )}
      {degradation.kbUnknown && (
        <Alert
          type="info"
          showIcon
          data-testid="wp-maintenance-kb-unknown"
          title="kb 注入状态不可知（诊断件缺失或损坏）。"
          style={{ marginBottom: 12 }}
        />
      )}
      {observation.stale && (
        <Alert
          type="warning"
          showIcon
          title="结果已过期：计算后设计有变更——建议重新提交计算获取最新检修观测。"
          style={{ marginBottom: 12 }}
        />
      )}
      {degradation.noObservableFaces ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="无可观测检修工况（未声明受检单元或该单元无 maint 键）"
        />
      ) : (
        observation.nodes.map((node) => (
          <NodeSection key={node.node_id} node={node} unitNames={unitNames} />
        ))
      )}
    </div>
  );
}
