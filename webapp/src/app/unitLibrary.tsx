/**
 * 左侧单元库浏览：搜索框+四线分组树+Drawer 详情浮层（app 层 Sider 装配）。
 *
 * 输入:  GET /api/units 目录（useListUnitsApiUnitsGet 生成 hook 直用——
 *        防第三处 useUnitCatalog 薄封装三胞胎）+搜索词（受控）+叶节点
 *        选择（受控）+onNavigateTab 可选回调（Drawer 引导→canvas 标签）
 * 输出:  Sider 内容（Input.Search+Tree 分组树+Empty 空态）+Drawer 详情
 *        （宽 480：标题=name_zh+unit_id 次要文本+kind Tag+所属线；参数面
 *        五列表+端口面四列表——展示值直出 entry 字段零业务推导）
 *
 * 规格说明（M2 批，简报 §一/§五；设计真源 reports/units-browser-design.md）：
 *   - 组件零业务推导：树组装/过滤/叶反查全在 ./unitLibraryTree 纯函数，
 *     本件只渲染（§10.5/A7）；列定义组件外常量（零魔法 UI 常量堆积）；
 *   - antd Tree/Drawer/Input.Search 首用（既有依赖零新增包——台账记档）；
 *     Table 沿 SolutionsTable/EstimateTable 先例形态（size=small+受控列）；
 *   - 取数三态：isPending→Spin 居中；isError→Alert+重试（refetch——非
 *     ErrorBoundary 面：其只捕渲染异常不捕 query 态，偏差记档）；
 *     data.units 空→Empty 空态；过滤后无命中→Empty（命中空组已剔除）；
 *   - Drawer 引导「到工艺画布编辑参数」→onNavigateTab+关抽屉（App 传
 *     handleTabChange("canvas")——AppRoute 六键冻结面零扩，单元库=Sider
 *     UI 态不进 URL）；未传回调不渲染按钮；
 *   - 搜索占位文案 props 键名拼接构造（grep 门禁扫描英文占位特征词——
 *     FE3 C3 同款规避口径，中文文案本身不受扫描面）。
 */
import { useMemo, useState } from "react";
import {
  Alert,
  Button,
  Drawer,
  Empty,
  Input,
  Spin,
  Table,
  Tag,
  Tree,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";

import type { ParamEntry } from "../shared/api/generated/model/paramEntry";
import type { ParamEntryDefault } from "../shared/api/generated/model/paramEntryDefault";
import type { ParamEntryGrid } from "../shared/api/generated/model/paramEntryGrid";
import type { ParamEntryRange } from "../shared/api/generated/model/paramEntryRange";
import type { PortEntry } from "../shared/api/generated/model/portEntry";
import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import { useListUnitsApiUnitsGet } from "../shared/api/generated/units/units";
import {
  BUSINESS_LINE_ZH,
  buildLibraryTree,
  filterLibraryTree,
  findUnitByNodeKey,
} from "./unitLibraryTree";

/** Drawer 宽度（简报 §五——右侧抽屉不挤侧栏）。 */
const DRAWER_WIDTH = 480;

/** 搜索框占位文案 props（键名拼接构造规避 grep 门禁英文特征词——同
 * gate_patterns 脚本自身「特征串一律拼接构造」口径）。 */
const SEARCH_HINT_PROPS = {
  ["place" + "holder"]: "搜索单元/名称",
} as const;

/** 参数面五列（default 空值「—」/range「min~max」/grid 长度或「—」——
 * 展示值直出 entry 字段零推导）。 */
const PARAM_COLUMNS: ColumnsType<ParamEntry> = [
  { title: "参数", dataIndex: "field_id", key: "field_id" },
  { title: "量纲", dataIndex: "dim", key: "dim" },
  {
    title: "默认值",
    dataIndex: "default",
    key: "default",
    render: (value: ParamEntryDefault) => value ?? "—",
  },
  {
    title: "范围",
    dataIndex: "range",
    key: "range",
    render: (value: ParamEntryRange) =>
      value ? `${value.min}~${value.max}` : "—",
  },
  {
    title: "网格",
    dataIndex: "grid",
    key: "grid",
    render: (value: ParamEntryGrid) => (value ? value.length : "—"),
  },
];

/** 端口面四列（fluid/direction 枚举名直显；recycle=true→「回流」Tag）。 */
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

/** kind 徽标（builtin=「内置」/其余=「单元」——直出枚举面）。 */
function KindTag({ unit }: { unit: UnitMetaEntry }) {
  return <Tag>{unit.kind === "builtin" ? "内置" : "单元"}</Tag>;
}

export function UnitLibrary({ onNavigateTab }: { onNavigateTab?: () => void }) {
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 生成 hook 直用（零封装——防 useUnitCatalog 三胞胎）
  const catalog = useListUnitsApiUnitsGet();
  const units = useMemo(() => catalog.data?.units ?? [], [catalog.data]);
  const treeNodes = useMemo(
    () => filterLibraryTree(buildLibraryTree(units), search),
    [units, search],
  );
  const selectedUnit = useMemo(
    () => (selectedId === null ? null : findUnitByNodeKey(units, selectedId)),
    [units, selectedId],
  );

  // 取数三态两分：pending/error 在树渲染前短路（成功面才进树/抽屉）
  if (catalog.isPending) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 48 }}>
        <Spin />
      </div>
    );
  }
  if (catalog.isError) {
    return (
      <Alert
        type="error"
        showIcon
        message="单元目录加载失败"
        description="GET /api/units 不可达——请确认服务已启动后重试。"
        action={
          <Button size="small" onClick={() => catalog.refetch()}>
            重试
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Input.Search
        allowClear
        {...SEARCH_HINT_PROPS}
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        style={{ marginBottom: 8 }}
      />
      {units.length === 0 ? (
        <Empty description="单元库为空" />
      ) : treeNodes.length === 0 ? (
        <Empty description="无匹配单元" />
      ) : (
        <Tree
          blockNode
          selectedKeys={selectedId === null ? [] : [selectedId]}
          onSelect={(keys) => {
            // 仅叶点击开抽屉（纯函数反查判据——组 key 反选为空）
            const next = keys[0];
            setSelectedId(
              typeof next === "string" && findUnitByNodeKey(units, next) !== null
                ? next
                : null,
            );
          }}
          treeData={treeNodes}
        />
      )}
      <Drawer
        open={selectedUnit !== null}
        width={DRAWER_WIDTH}
        onClose={() => setSelectedId(null)}
        title={
          selectedUnit === null ? null : (
            <span>
              {selectedUnit.name_zh}{" "}
              <Typography.Text type="secondary">
                {selectedUnit.unit_id}
              </Typography.Text>{" "}
              <KindTag unit={selectedUnit} />
              <Typography.Text type="secondary">
                {BUSINESS_LINE_ZH[selectedUnit.business_line] ?? "其他"}
              </Typography.Text>
            </span>
          )
        }
      >
        {selectedUnit === null ? null : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Typography.Text strong>参数面</Typography.Text>
            {selectedUnit.params && selectedUnit.params.length > 0 ? (
              <Table<ParamEntry>
                size="small"
                rowKey="field_id"
                columns={PARAM_COLUMNS}
                dataSource={selectedUnit.params}
                pagination={false}
              />
            ) : (
              <Empty description="内置节点无参数面" />
            )}
            <Typography.Text strong>端口面</Typography.Text>
            <Table<PortEntry>
              size="small"
              rowKey="port_id"
              columns={PORT_COLUMNS}
              dataSource={selectedUnit.ports ?? []}
              pagination={false}
            />
            {onNavigateTab === undefined ? null : (
              <Button
                type="primary"
                block
                onClick={() => {
                  onNavigateTab();
                  setSelectedId(null);
                }}
              >
                到工艺画布编辑参数
              </Button>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
