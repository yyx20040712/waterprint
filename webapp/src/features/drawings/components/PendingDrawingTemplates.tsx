/**
 * 挂起位③载体：studio.drawings 管网图纸模板位展示（M4 批 D4 2026-10-07
 * ——v3 B-3 管网线挂起位③「studio.drawings 管网图纸模板位（平面布置图+
 * 纵剖面图）展示——演示至此止，不实现」逐字口径；M3 批 LineSidebar 载体
 * 块同构纯展示子件）。
 *
 * 输入:  无（纯展示——挂起位展示语义非选中态函数，恒在场零条件渲染）
 * 输出:  容器 div（data-testid="wp-pending-drawing-templates"——门二探针
 *        消费面，与 wp-pending-network 命名族对齐）：antd Tag「管网图纸
 *        · 规划中」（回炉 R8——诚实短文案，default 色，style 沿树徽标
 *        同形 fontSize 11/lineHeight "16px"）+Typography.Text secondary
 *        （fontSize 12）说明行全文
 *
 * 规格说明（M4 brief D4；mapping-2b4 §A M4 行「管网图纸模板位=挂起位③」）：
 *   - 「纵断面图」用词（B-3 原文「纵剖面图」vs elevation 面既有中文词
 *     「纵断面」——从后者对齐全库术语单源，申报见任务书 §7）；
 *   - 零业务逻辑零条件渲染（恒在场——挂起展示非选中态函数；管网定线/
 *     水力计算/平纵图纸功能面随后续管网批，本件纯展示）。
 */
import { Tag, Typography } from "antd";

/** 挂起位③载体（纯展示——无 props 无推导）。 */
export function PendingDrawingTemplates() {
  return (
    <div data-testid="wp-pending-drawing-templates" style={{ marginTop: 8 }}>
      {/* 回炉 R8：诚实短文案（内部口径语「挂起展示，不实现」退场——
          「管网图纸 · 规划中」级白名单内） */}
      <Tag style={{ fontSize: 11, lineHeight: "16px" }}>管网图纸 · 规划中</Tag>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        管网平面布置图·纵断面图将随后续管网批加入图纸目录
      </Typography.Text>
    </div>
  );
}
