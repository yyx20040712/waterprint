/**
 * 单元详情面板（M2 批 2026-10-08——Drawer 详情收编 Settings 右窗：选中库
 * 单元即显详情，Drawer 浮层退役——draft-ia-v3 §6 动线③）。
 *
 * 输入:  unitId（App libraryFocusId——受控叶选中同源）+onClose（✕ 解除/
 *        导航后解除）+onNavigateTab（「到工艺画布」——App setTab canvas）；
 *        GET /api/units 目录（useListUnitsApiUnitsGet 生成 hook 直用——
 *        防 useUnitCatalog 薄封装三胞胎，沿 unitLibrary 先例）
 * 输出:  详情面板（data-testid=wp-unit-detail——门二探针锚）：头部=
 *        DomainIcon+name_zh+unit_id（secondary）+KindTag+所属线+✕ 解除钮；
 *        体=参数面五列表+端口面四列表（列定义自 unitLibrary Drawer 段逐字
 *        迁移——展示值直出 entry 字段零业务推导）；底=编辑态「添加到画布」
 *        主钮+「到工艺画布」钮（导航并解除——Drawer 语义沿袭）
 *
 * 规格说明（M2 批预裁决 3/5/6）：
 *   - 不受 projectId 门（目录数据全局，库浏览无项目语境成立；「添加到
 *     画布」自身 editing 守卫只读态不显=已安全）；
 *   - 单元查得=null（目录无此键）→Empty「单元目录中无此单元」+✕ 仍在；
 *   - 画布点击不清 focus（P0-3 裁决保持）：详情与画布选中鎏金通道独立
 *     并存；解除仅三通道=详情✕/组反选/「到工艺画布」；
 *   - 取数三态沿 unitLibrary 先例：pending→Spin 居中；error→Alert+重试
 *     （ErrorBoundary 不捕 query 态——偏差记档先例同）；
 *   - addToCanvas=useAddUnitToCanvas 单源（叶行＋钮/主钮两消费点收敛）。
 */
import { Alert, Button, Empty, Spin, Table, Tag, Typography } from "antd";
import { CloseOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import type { ParamEntry } from "../shared/api/generated/model/paramEntry";
import type { PortEntry } from "../shared/api/generated/model/portEntry";
import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import { useListUnitsApiUnitsGet } from "../shared/api/generated/units/units";
import { domainIconStyle } from "../features/canvas/lib/unitGlyph";
import { BUSINESS_LINE_ZH, libraryGlyph } from "./unitLibraryTree";
import { useAddUnitToCanvas } from "./useAddUnitToCanvas";

/** 图标尺寸/圆角/字号（C2-ALIGN A4 值沿袭——与叶行/画布节点同语言）。 */
const ICON_SIZE = 22;
const ICON_RADIUS = 5;
const ICON_GLYPH_SIZE = 11;

/** 参数面五列（自 unitLibrary Drawer 段逐字迁移。default 空值「—」/range
 * 「min~max」/grid 长度或「—」。C2-ALIGN A5r：参数列显 label_zh 物理意义
 * （?? field_id 回退），field_id 悬浮保留代码名追溯）。 */
const PARAM_COLUMNS: ColumnsType<ParamEntry> = [
  {
    title: "参数",
    dataIndex: "label_zh",
    key: "label_zh",
    render: (value: string | null, entry: ParamEntry) => (
      <span title={entry.field_id}>{value ?? entry.field_id}</span>
    ),
  },
  { title: "量纲", dataIndex: "dim", key: "dim" },
  {
    title: "默认值",
    dataIndex: "default",
    key: "default",
    render: (value: ParamEntry["default"]) => value ?? "—",
  },
  {
    title: "范围",
    dataIndex: "range",
    key: "range",
    render: (value: ParamEntry["range"]) =>
      value ? `${value.min}~${value.max}` : "—",
  },
  {
    title: "网格",
    dataIndex: "grid",
    key: "grid",
    render: (value: ParamEntry["grid"]) => (value ? value.length : "—"),
  },
];

/** 端口面四列（自 unitLibrary Drawer 段逐字迁移——fluid/direction 枚举名
 * 直显；recycle=true→「回流」Tag）。 */
const PORT_COLUMNS: ColumnsType<PortEntry> = [
  { title: "端口", dataIndex: "port_id", key: "port_id" },
  { title: "流体", dataIndex: "fluid", key: "fluid" },
  { title: "方向", dataIndex: "direction", key: "direction" },
  {
    title: "回流",
    dataIndex: "recycle",
    key: "recycle",
    render: (value: boolean) => (value ? <Tag>回流</Tag> : "—"),
  },
];

/** kind 徽标（builtin=「内置」/其余=「单元」——直出枚举面；自 unitLibrary
 * Drawer 段逐字迁移）。 */
function KindTag({ unit }: { unit: UnitMetaEntry }) {
  return <Tag>{unit.kind === "builtin" ? "内置" : "单元"}</Tag>;
}

/** 域色图标框（头部用——22×22 三色组+字形；自 unitLibrary 逐字迁移，
 * domainIconStyle 单源消费与叶行/画布节点恒同值）。 */
function DomainIcon({ unit }: { unit: UnitMetaEntry }) {
  const iconStyle = domainIconStyle(unit.business_line);
  return (
    <span
      aria-hidden
      style={{
        width: ICON_SIZE,
        height: ICON_SIZE,
        flex: "none",
        borderRadius: ICON_RADIUS,
        fontSize: ICON_GLYPH_SIZE,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: iconStyle.bg,
        border: `1px solid ${iconStyle.border}`,
        color: iconStyle.fg,
      }}
    >
      {libraryGlyph(unit)}
    </span>
  );
}

export function UnitDetailPanel({
  unitId,
  onClose,
  onNavigateTab,
}: {
  unitId: string;
  onClose: () => void;
  onNavigateTab: () => void;
}) {
  const { addToCanvas, editing, contextHolder } = useAddUnitToCanvas();
  const catalog = useListUnitsApiUnitsGet();
  // ✕ 解除钮（恒在场——pending/error 早退分支与目录无此键 Empty 态均保留
  // 解除通道：左列同键 error 时组反选不可用，✕ 为唯一出口——R1-c）
  const closeBtn = (
    <Button
      type="text"
      size="small"
      icon={<CloseOutlined />}
      title="解除选中——关闭详情"
      aria-label="解除选中——关闭详情"
      onClick={onClose}
      style={{ marginLeft: "auto", flex: "none" }}
    />
  );

  if (catalog.isPending) {
    return (
      <div data-testid="wp-unit-detail" style={{ minHeight: 0 }}>
        {contextHolder}
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "6px 8px 0" }}>
          {closeBtn}
        </div>
        <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
          <Spin />
        </div>
      </div>
    );
  }
  if (catalog.isError) {
    return (
      <div data-testid="wp-unit-detail" style={{ minHeight: 0 }}>
        {contextHolder}
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "6px 8px 0" }}>
          {closeBtn}
        </div>
        <Alert
          type="error"
          showIcon
          title="单元目录加载失败"
          description="GET /api/units 不可达——请确认服务已启动后重试。"
          action={
            <Button size="small" onClick={() => catalog.refetch()}>
              重试
            </Button>
          }
        />
      </div>
    );
  }

  const unit =
    catalog.data?.units.find((entry) => entry.unit_id === unitId) ?? null;

  return (
    <div
      data-testid="wp-unit-detail"
      style={{ display: "flex", flexDirection: "column", minHeight: 0, height: "100%" }}
    >
      {contextHolder}
      {/* 头部：图标+name_zh+unit_id（secondary）+KindTag+所属线+✕ 解除钮 */}
      {unit === null ? (
        <>
          <div style={{ display: "flex", justifyContent: "flex-end", padding: "6px 8px 0" }}>
            {closeBtn}
          </div>
          <Empty description="单元目录中无此单元" />
        </>
      ) : (
        <>
          <header
            style={{
              flex: "none",
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 12px",
              borderBottom: "1px solid var(--wp-border-2)",
            }}
          >
            <DomainIcon unit={unit} />
            <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--wp-text)" }}>
              {unit.name_zh}
            </span>
            <Typography.Text type="secondary" style={{ fontSize: 11 }}>
              {unit.unit_id}
            </Typography.Text>
            <KindTag unit={unit} />
            <Typography.Text type="secondary" style={{ fontSize: 11 }}>
              {BUSINESS_LINE_ZH[unit.business_line] ?? "其他"}
            </Typography.Text>
            {closeBtn}
          </header>
          {/* 体：参数面五列表+端口面四列表（Drawer 段逐字迁移形态） */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              overflow: "auto",
              padding: "10px 12px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <Typography.Text strong>参数面</Typography.Text>
            {unit.params && unit.params.length > 0 ? (
              <Table<ParamEntry>
                size="small"
                rowKey="field_id"
                columns={PARAM_COLUMNS}
                dataSource={unit.params}
                pagination={false}
              />
            ) : (
              // R 轮 G1-02：空参数文案按 kind 两分（判据=kind 非 params 空）
              <Empty
                description={
                  unit.kind === "builtin" ? "内置节点无参数面" : "该单元无参数面"
                }
              />
            )}
            <Typography.Text strong>端口面</Typography.Text>
            <Table<PortEntry>
              size="small"
              rowKey="port_id"
              columns={PORT_COLUMNS}
              dataSource={unit.ports ?? []}
              pagination={false}
            />
          </div>
          {/* 底：编辑态主钮（block primary——P0-3 呈裁② 甲案沿袭）+导航钮
              （onNavigateTab+onClose——现状 Drawer 语义沿袭：导航并解除） */}
          <footer
            style={{
              flex: "none",
              padding: 10,
              borderTop: "1px solid var(--wp-border-2)",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {editing ? (
              <Button type="primary" block onClick={() => addToCanvas(unit)}>
                添加到画布
              </Button>
            ) : null}
            <Button
              block
              type={editing ? "default" : "primary"}
              onClick={() => {
                onNavigateTab();
                onClose();
              }}
            >
              到工艺画布{editing ? "" : "编辑参数"}
            </Button>
          </footer>
        </>
      )}
    </div>
  );
}
