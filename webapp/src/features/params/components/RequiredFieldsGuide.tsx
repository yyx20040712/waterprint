/**
 * 必填缺失引导条（E2E 审计 F5 批 2026-11-20）：进水必填项缺失时的空态
 * 引导——明确告知缺哪些字段与可选指标口径，替代 422 撞墙（提交门锁在
 * ParamForm，本件纯呈现）。
 *
 * 输入:  missing（必填缺失 ParamEntry 清单——lib/paramFormView
 *        missingRequiredFields 产物；非空才由消费面渲染）
 * 输出:  引导条（缺项中文名清单+项目基础资料口径说明+可选指标缺项语义）
 */

import type { ParamEntry } from "../../../shared/api/generated/model";

/**
 * 引导条样式（C2-params 表单面同源：--wp 变量轴取色，warning 级信息条
 * 非错误条——缺项是待办不是违例）。
 */
const GUIDE_STYLE: React.CSSProperties = {
  margin: "8px 0 2px",
  padding: "8px 10px",
  fontSize: 11.5,
  lineHeight: 1.7,
  borderRadius: 6,
  border: "1px solid var(--wp-border)",
  background: "var(--wp-bg-elevated)",
  color: "var(--wp-text)",
};

/** 缺项名清单（label_zh 真源——缺席键回退 field_id）。 */
const GUIDE_NAMES_STYLE: React.CSSProperties = {
  color: "var(--wp-error)",
  fontWeight: 600,
};

/** 口径说明行（secondary——项目基础资料/缺项透传语义）。 */
const GUIDE_NOTE_STYLE: React.CSSProperties = {
  color: "var(--wp-text-2)",
  fontSize: 10.5,
};

/**
 * 必填引导条（现行唯一 required 面=municipal_input 进水——文案按进水
 * 面校准：流量两键必填、指标可选）。
 */
export function RequiredFieldsGuide({ missing }: { missing: ParamEntry[] }) {
  const names = missing
    .map((entry) => entry.label_zh ?? entry.field_id)
    .join("、");
  return (
    <div data-testid="wp-required-guide" role="status" style={GUIDE_STYLE}>
      <div>
        进水参数为项目基础资料（无默认值）——必填项补齐后才能提交计算
      </div>
      <div>
        还缺：
        <span data-testid="wp-required-guide-names" style={GUIDE_NAMES_STYLE}>
          {names}
        </span>
      </div>
      <div style={GUIDE_NOTE_STYLE}>
        水质指标可选：未填指标按「缺项透传」向下游传播——依赖该指标的
        计算将明确报错（不会默认为 0）。
      </div>
    </div>
  );
}
