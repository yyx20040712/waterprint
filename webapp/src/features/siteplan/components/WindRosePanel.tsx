/**
 * 风玫瑰值编辑面板（B5 D5——右侧栏常驻[无选中时显示区]：固定八方位
 * InputNumber 编辑+未知键合并保留写回+清空确认门）。
 *
 * 输入:  value（draft.options.wind_rose——Record<string,number>|null 受控）
 *        +onChange（合并写回值上行——mergeWindRose 单源派生）+onClear
 *        （清空确认门确认后上行 null——全量丢弃唯此显式通路）
 * 输出:  aside 侧栏（标题+四行两列八方位 InputNumber[min=0 输入即禁负]
 *        +数值口径提示语+清空 Popconfirm 确认门）
 *
 * 规格说明（简报 D5/D7——2026-09-06 批量任务体验批）：
 *   - 键集=固定八方位（WIND_DIRS 单源——windRoseGeometry 同源渲染面）；
 *     未知键（如 NNW）不在编辑面但经 mergeWindRose 合并保留不丢；
 *   - 受控零本地态：InputNumber 值直投影 value[dir]，编辑=以「全量表单值
 *     （其余方位取 value 投影+本方位新值）」上行 onChange（copy-on-write
 *     由 SiteplanPane 落 draft——B4 boundary 三回调同构）；
 *   - 数值口径：各方位相对频率，按峰值自动归一显示，仅相对大小有意义，
 *     无需合计为 1 或 100（core site_plan.py 纯相对峰值口径对口）；
 *   - 清空=danger+Popconfirm「将清除全部方位数据」（B4 删除确认先例——
 *     仓内无 undo；确认=onClear() 上行 null，取消/外点=零动作）；value
 *     为 null 时按钮 disabled（无数据可清）；逐方位清空至全空亦归 null
 *     （受控表单自然语义——B5 R5 钉口径：全量丢弃非唯确认门一条通路）；
 *   - antd 组件 node 不可直调（LineSidebar 先例）——纯逻辑归 lib/
 *     windRoseForm 直测，本件薄壳不测（B 面探针覆盖交互面）。
 */
import { Button, InputNumber, Popconfirm, Typography } from "antd";

import { WIND_DIRS } from "../lib/windRoseGeometry";
import { mergeWindRose, type WindDir, type WindRoseFormValues } from "../lib/windRoseForm";

/** 侧栏宽度（像素——显示层定值，对齐 StructureSidebar 220）。 */
const WIND_SIDE_WIDTH = 220;

export type WindRosePanelProps = {
  value: Record<string, number> | null;
  onChange: (next: Record<string, number> | null) => void;
  onClear: () => void;
};

export function WindRosePanel({ value, onChange, onClear }: WindRosePanelProps) {
  // 编辑上行：全量表单值（其余方位=value 投影，本方位=新值）经合并语义单源
  const handle = (dir: WindDir, next: number | null) => {
    const values: WindRoseFormValues = {};
    for (const entry of WIND_DIRS) {
      values[entry] = entry === dir ? next : (value?.[entry] ?? null);
    }
    onChange(mergeWindRose(value, values));
  };
  return (
    <aside style={{ width: WIND_SIDE_WIDTH, flexShrink: 0, padding: "8px 12px", borderLeft: "1px solid #434343" }}>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        风玫瑰（八方位频率）
      </Typography.Text>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "4px 8px", marginTop: 8 }}>
        {WIND_DIRS.map((dir) => (
          <label key={dir} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <Typography.Text style={{ width: 22, fontSize: 12 }}>{dir}</Typography.Text>
            <InputNumber
              size="small"
              min={0}
              style={{ width: "100%" }}
              value={value?.[dir] ?? null}
              onChange={(next) => handle(dir, next)}
            />
          </label>
        ))}
      </div>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8, marginBottom: 8 }}>
        各方位相对频率，按峰值自动归一显示，仅相对大小有意义，无需合计为 1 或 100。
      </Typography.Paragraph>
      <Popconfirm
        title="清空风玫瑰"
        description="将清除全部方位数据（含八方位外键——不可撤销）"
        okText="确认清空"
        cancelText="取消"
        onConfirm={onClear}
      >
        <Button size="small" danger disabled={value === null}>
          清空
        </Button>
      </Popconfirm>
    </aside>
  );
}
