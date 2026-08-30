/**
 * 图纸元数据卡（D1 保守预裁——下载/元数据轻量面，DXF 线稿渲染挂账）。
 *
 * 输入:  SheetRow | null（drawingsView 行模型——SheetList 选中行）
 * 输出:  选中图纸元数据卡（三元组摘要/engine/data 版本/stale 标注/文件名
 *        +诚实注记「DXF 线稿渲染未实装」）；null=空态引导（先从目录选择）
 *
 * 规格说明（FE9 批 6b 段七，D1/D7；骨架冻结规格「纯投影渲染」维持
 *   冻结不删——本卡为过渡形态记档）：
 *   - DXF 前端渲染库（three-dxf/dxf-parser 族）与服务端位图渲染=新
 *     依赖红线（宪法 §2 零新依赖沿册先例），挂账待用户 Ruling，本批
 *     禁引入——轻量预览=元数据+导出下载通道（CAD 工具查看产物）；
 *   - 禁止前端重建制图逻辑（骨架冻结规格——渲染形态 Ruling 后仍由
 *     服务端 DXF 纯投影，前端只渲染投影结果）；
 *   - 薄壳不测（投影层 drawingsView.test 承担字段面契约）。
 */
import { Card, Descriptions, Empty, Tag, Typography } from "antd";

import type { SheetRow } from "../lib/drawingsView";

/** 诚实注记（渲染形态待 Ruling——禁伪装成已完成预览）。 */
const RENDER_NOTE =
  "DXF 线稿渲染未实装——渲染形态待 Ruling（渲染库属新依赖红线，挂账）；本卡为元数据轻量预览，图纸内容请经「导出图纸」下载后用 CAD 工具查看。";

/** 图纸元数据卡（D1：选中行的三元组/版本/stale 标注呈现）。 */
export function DrawingPreview({ row }: { row: SheetRow | null }) {
  if (row === null) {
    return (
      <Card size="small" title="图纸预览">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <Typography.Text type="secondary">
              尚未选择图纸——在上方的图纸目录中点选一行查看元数据
            </Typography.Text>
          }
        />
      </Card>
    );
  }
  return (
    <Card size="small" title="图纸预览（元数据）">
      <Descriptions
        size="small"
        column={1}
        items={[
          { key: "fileName", label: "文件名", children: row.fileName },
          {
            key: "kind",
            label: "类型",
            children: `${row.kind}（工况 ${row.conditionKey}）`,
          },
          {
            key: "repro",
            label: "可复算三元组",
            children: (
              <span style={{ fontVariantNumeric: "tabular-nums" }}>
                {row.designDigest} | {row.engineVersion} | {row.dataVersion}
              </span>
            ),
          },
          {
            key: "stale",
            label: "标注",
            children: row.stale ? (
              <Tag color="orange">stale（基于旧 design 导出——force 显式标注）</Tag>
            ) : (
              <Tag color="green">当前（与最新 design 一致）</Tag>
            ),
          },
        ]}
      />
      <Typography.Text type="secondary">{RENDER_NOTE}</Typography.Text>
    </Card>
  );
}
