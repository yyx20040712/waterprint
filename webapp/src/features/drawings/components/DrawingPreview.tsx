/**
 * 图纸预览卡：元数据卡（FE9 保留面）+DXF 线稿渲染区（B 批 D7 重写
 * ——Ruling B 落地：导出 blob 经投影层渲染线稿）。
 *
 * 输入:  SheetRow | null（drawingsView 行模型——SheetList 选中行）
 *        +scene: SvgScene | null（导出 blob 解析投影产物——绑定导出
 *        动作非行选中）+sceneError: string | null（解析失败降级消息）
 * 输出:  元数据卡（三元组摘要/engine/data 版本/stale 标注/文件名——
 *        四行逐字保留）+三态渲染区（scene→DxfSvg 线稿；sceneError→
 *        降级注记；皆空→绑定导出动作引导注记）；row=null=空态引导
 *
 * 规格说明（B 批 D7；FE9 元数据面冻结维持）：
 *   - 线稿渲染绑定导出动作（Ruling B 唯一零契约路径——E 冻结 §四：
 *     无按文件 GET 端点，行选中重取需契约扩展出局记档）；渲染区独立
 *     于 row 选中态呈现（导出成功即可见）；
 *   - sceneError 降级=I-3 分级（预览是增强非门禁：解析失败不扰下载
 *     成功——文件已落盘，注记引导 CAD 工具查看）；
 *   - v1 全实线（dxf-parser 线型表 DASHED 缺失=解析器局限，E 冻结
 *     §三——引导注记诚实呈现不遮蔽）；文字尺寸=投影层按图幅可读性
 *     放大（显示层裁量，lib/dxfScene 头注记档）；
 *   - 薄壳不测（投影层 dxfScene.test 承担契约面——先例维持）。
 */
import { Card, Descriptions, Empty, Tag, Typography } from "antd";

import type { SheetRow } from "../lib/drawingsView";
import type { SvgScene } from "../lib/dxfScene";
import { DxfSvg } from "./DxfSvg";

/** 未导出引导（RENDER_NOTE 翻转——B 批实装后口径：绑定导出动作）。 */
const RENDER_NOTE =
  "线稿渲染绑定导出动作：经上方「导出图纸」成功后，此处渲染该图纸线稿（v1 全实线——轴线虚线差异不呈现）。";

/** 线稿容器高度（显示层常量——px，overflow 滚动兜底大图）。 */
const PREVIEW_HEIGHT = 420;

/** 线稿容器浅底（显示层常量——CAD 图面惯例浅灰）。 */
const PREVIEW_BACKGROUND = "#fafafa";

/** 图纸预览卡（元数据+线稿渲染区三态）。 */
export function DrawingPreview({
  row,
  scene,
  sceneError,
}: {
  row: SheetRow | null;
  scene: SvgScene | null;
  sceneError: string | null;
}) {
  return (
    <Card size="small" title="图纸预览">
      {row === null ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <Typography.Text type="secondary">
              尚未选择图纸——在上方的图纸目录中点选一行查看元数据
            </Typography.Text>
          }
        />
      ) : (
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
      )}
      <div style={{ marginTop: 8 }}>
        {scene !== null ? (
          <div
            style={{
              height: PREVIEW_HEIGHT,
              overflow: "auto",
              background: PREVIEW_BACKGROUND,
            }}
          >
            <DxfSvg scene={scene} />
          </div>
        ) : sceneError !== null ? (
          <Typography.Text type="warning">
            线稿解析失败：{sceneError}——文件已下载，请用 CAD 工具查看
          </Typography.Text>
        ) : (
          <Typography.Text type="secondary">{RENDER_NOTE}</Typography.Text>
        )}
      </div>
    </Card>
  );
}
