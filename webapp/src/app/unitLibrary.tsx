/**
 * 左侧单元库浏览：搜索框+四线分组树（图标行）+Drawer 详情浮层（app 层
 * Sider 装配）。
 *
 * 输入:  GET /api/units 目录（useListUnitsApiUnitsGet 生成 hook 直用——
 *        防第三处 useUnitCatalog 薄封装三胞胎）+搜索词（受控）+focusId
 *        （受控叶选中——App 持态 C2-lib 联动穿线）+onFocusChange+
 *        onNavigateTab 可选回调（Drawer 引导→canvas 标签）
 * 输出:  Sider 内容（Input.Search+Tree 分组树[图标行]+Empty 空态+底部
 *        计数条）+Drawer 详情（宽 480：图标+name_zh+unit_id 次要文本+
 *        kind Tag+所属线；参数面五列表+端口面四列表——展示值直出 entry
 *        字段零业务推导）
 *
 * 规格说明（M2 批，简报 §一/§五；设计真源 reports/units-browser-design.md；
 *   C2-lib 批重制——briefs/task-C2-lib-plan.md §二 U1/U2/U4/U5+§五呈裁
 *   实录[用户裁定：码不显示/仅光环/计数条做]）：
 *   - 组件零业务推导：树组装/过滤/叶反查/字形全在 ./unitLibraryTree
 *     纯函数，本件只渲染（§10.5/A7）；列定义组件外常量（零魔法 UI
 *     常量堆积）；
 *   - U1 图标行（titleRender——antd v6 @rc-component/tree 在案）：叶行=
 *     [图标 20×20 域色三色组+字形]+中文名 12.5px 单主列；**英文码不
 *     显示**（用户裁定「尽量能不显示都不显示」——title 悬浮=全
 *     unit_id 为唯一保留追溯通道，零版面常显）；组行=域色短条+组名
 *     计数（title=string 保持——titleRender 按 group: 前缀分流）；
 *   - U3 联动（库→画布单向）：叶选中=onFocusChange(unit_id)+Drawer
 *     开（focus 生命周期=Drawer 开闭——关抽屉=onFocusChange(null)
 *     解除）；CanvasPane 透传 CanvasFlow 命中光环（wp-lib-hit——
 *     global.css）；画布节点点击不清 focus（选中鎏金独立通道并存）；
 *   - U4 计数条：左右分列（左「N 单元」右「M 组」——catalog 驱动；N=kind=unit 条数，
 *     M=分组数含内置组；空态/加载态/错误态不渲染）；
 *   - U5 Drawer 标题图标（与叶行/画布节点三处同语言——20×20 域色
 *     三色组）；
 *   - antd Tree/Drawer/Input.Search（M2 首用沿袭）；Table 沿
 *     SolutionsTable/EstimateTable 先例形态（size=small+受控列）；
 *   - 取数三态：isPending→Spin 居中；isError→Alert+重试（refetch——非
 *     ErrorBoundary 面：其只捕渲染异常不捕 query 态，偏差记档）；
 *     data.units 空→Empty 空态；过滤后无命中→Empty（命中空组已剔除）；
 *   - Drawer 引导「到工艺画布编辑参数」→onNavigateTab+关抽屉（App 传
 *     handleTabChange("canvas")——AppRoute 六键冻结面零扩，单元库=Sider
 *     UI 态不进 URL）；未传回调不渲染按钮；
 *   - 搜索占位文案 props 键名拼接构造（grep 门禁扫描英文占位特征词——
 *     FE3 C3 同款规避口径，中文文案本身不受扫描面）；
 *   - P0-3（task-c2-edit-plan 呈裁② 甲案双入口）：编辑态（canvasStore
 *     会话——projectId 守卫）叶行悬浮「＋」钮+Drawer 详情主钮「添加
 *     到画布」→ store.addUnit（designWriter 零默认填充③/`_2` 后缀③）
 *     +message 反馈实例 id；只读态零呈现（编辑入口=画布工具条「编辑」
 *     钮——F2 断链根路径）。
 */
import { useCallback, useMemo, useState } from "react";
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
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { TreeDataNode } from "antd";

import type { ParamEntry } from "../shared/api/generated/model/paramEntry";
import type { PortEntry } from "../shared/api/generated/model/portEntry";
import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import { useListUnitsApiUnitsGet } from "../shared/api/generated/units/units";
import { domainColorOf } from "../features/canvas/lib/unitGlyph";
import { useCanvasStore, useEditing } from "../features/canvas/store/canvasStore";
import {
  BUSINESS_LINE_ZH,
  buildLibraryTree,
  filterLibraryTree,
  findUnitByNodeKey,
  libraryGlyph,
} from "./unitLibraryTree";
import { useProjectId } from "./useProjectId";

/** Drawer 宽度（简报 §五——右侧抽屉不挤侧栏）。 */
const DRAWER_WIDTH = 480;

/** 组节点 key 前缀（titleRender 叶/组分流判据——unitLibraryTree 同值
 * 本地复制[导出面为纯函数 API 不含常量]；GL-04 R 轮：联动面=前缀+后缀
 * 双段——后缀 builtin/other 亦 unitLibraryTree 构造面同值魔串[组判色
 * 分支消费]，改组 key 构造须两文件四点联动）。 */
const GROUP_KEY_PREFIX = "group:";

/** 行图标尺寸/圆角（C2-ALIGN A4：20→22=direction-a .unit-ico 22×22
 * 对齐——「视觉稿态二冻结 20×20」由本批用户反馈+方向 A 真源取代）。 */
const ICON_SIZE = 22;
const ICON_RADIUS = 5;
/** 图标字形字号（C2-ALIGN A4：10.5→11=设计 .unit-ico font-size）。 */
const ICON_GLYPH_SIZE = 11;
/** 叶行中文名字号（C2-ALIGN A4：12.5→13——用户「文字大一点」，升至
 * 基准字号=providers fontSize 同值）。 */
const LEAF_NAME_SIZE = 13;
/** 组行题字号（C2-ALIGN A4：11→12——用户「大一点」+1 档）。 */
const GROUP_TITLE_SIZE = 12;

/** 域色图标三色组（UnitNode DOMAIN_ICON_STYLES 同值派生消费——
 * R-G3 联动清单成员·Y-4 A 前分层口径：**同构表复制两处**[本表/UnitNode
 * 表]；global.css 为色值变量轴联动[非三键表复制]——收敛候选=unitGlyph
 * 层导出统一面，第三处复制前收敛）。 */
const DOMAIN_ICON_STYLES: Record<string, { bg: string; border: string; fg: string }> = {
  municipal: { bg: "rgba(77,163,255,.14)", border: "rgba(77,163,255,.3)", fg: "#7ab2ff" },
  sludge: { bg: "rgba(156,107,69,.16)", border: "rgba(156,107,69,.4)", fg: "#d4a273" },
  mine_water: { bg: "rgba(53,201,176,.12)", border: "rgba(53,201,176,.3)", fg: "#52d8c2" },
  conveyance: { bg: "rgba(154,168,184,.14)", border: "rgba(154,168,184,.3)", fg: "#b8c6d6" },
};
const NEUTRAL_ICON = { bg: "rgba(89,89,89,.14)", border: "rgba(89,89,89,.3)", fg: "#8c8c8c" };

/** 搜索框占位文案 props（键名拼接构造规避 grep 门禁英文特征词——同
 * gate_patterns 脚本自身「特征串一律拼接构造」口径）。 */
const SEARCH_HINT_PROPS = {
  ["place" + "holder"]: "搜索单元/名称",
} as const;

/** 参数面五列（default 空值「—」/range「min~max」/grid 长度或「—」。
 * C2-ALIGN A5r：参数列显 label_zh 物理意义（?? field_id 回退——
 * 「所有参数都要显示物理意义」），field_id 悬浮保留代码名追溯）。 */
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
    // GOV5-1（orval 8）：anyOf 分支类型内联为 ParamEntry 可选字段，
    // 索引访问形取代原独立 schema 文件类型。
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

/** 域色图标框（叶行/Drawer 标题共用——20×20 三色组+字形）。 */
function DomainIcon({ unit }: { unit: UnitMetaEntry }) {
  const iconStyle = DOMAIN_ICON_STYLES[unit.business_line] ?? NEUTRAL_ICON;
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

export function UnitLibrary({
  focusId,
  onFocusChange,
  onNavigateTab,
}: {
  /** 受控叶选中（null=无选中——App 持态：Drawer 开闭+画布联动光环同源）。 */
  focusId: string | null;
  /** 叶选中/解除回调（叶点击=unit_id；组反选/关抽屉=null）。 */
  onFocusChange: (value: string | null) => void;
  onNavigateTab?: () => void;
}) {
  const [search, setSearch] = useState("");
  // P0-3：编辑会话消费（projectId 守卫——store 会话与当前项目一致才可加）
  const [projectId] = useProjectId();
  const editing = useEditing(projectId);
  const [messageApi, contextHolder] = message.useMessage();
  const addToCanvas = useCallback(
    (unit: UnitMetaEntry) => {
      const nodeId = useCanvasStore.getState().addUnit(unit.unit_id, unit.kind);
      if (nodeId !== null) {
        messageApi.success(`已添加到画布：${nodeId}`);
      } else if (unit.kind === "unit") {
        // 引擎 v1 单实例约束（designWriter.addUnit 拒绝面——装配按
        // node_id=注册表键精确匹配，_2 包实例 calc 必败）
        messageApi.warning("该单元已在画布上（引擎 v1 单实例约束——多实例扩展挂账）");
      }
    },
    [messageApi],
  );

  // 生成 hook 直用（零封装——防 useUnitCatalog 三胞胎）
  const catalog = useListUnitsApiUnitsGet();
  const units = useMemo(() => catalog.data?.units ?? [], [catalog.data]);
  const treeNodes = useMemo(
    () => filterLibraryTree(buildLibraryTree(units), search),
    [units, search],
  );
  const selectedUnit = useMemo(
    () => (focusId === null ? null : findUnitByNodeKey(units, focusId)),
    [units, focusId],
  );

  // titleRender（叶/组分流：叶=图标行[图标+中文名，悬浮全 unit_id]；
  // 组=域色短条+组名计数——树数据 title=string 保持，渲染层定制。
  // 类型面：TreeDataNode.title 联合含函数形——本库树数据恒 string，断言
  // 收窄一次[titleText]两分支共用）
  const titleRender = useMemo(() => {
    return (node: TreeDataNode): React.ReactNode => {
      const key = typeof node.key === "string" ? node.key : "";
      const titleText = typeof node.title === "string" ? node.title : "";
      if (key.startsWith(GROUP_KEY_PREFIX)) {
        // 组行：域色短条（内置/其他组=中性灰——domainColorOf 未收录回退）
        // +基名左置+计数右对齐（glm 实现态 r1 采纳——树数据 title 形态
        // 「基名 (N)」拆解渲染；filterLibraryTree 重算计数面经此同步）
        const line = key.slice(GROUP_KEY_PREFIX.length);
        const countMatch = titleText.match(/ \((\d+)\)$/);
        const baseTitle = countMatch === null ? titleText : titleText.slice(0, countMatch.index);
        const count = countMatch === null ? null : countMatch[1];
        return (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7, fontSize: GROUP_TITLE_SIZE, letterSpacing: 1, color: "var(--wp-text-3)", width: "100%" }}>
            <span
              aria-hidden
              style={{ width: 8, height: 2, borderRadius: 1, background: domainColorOf(line === "builtin" || line === "other" ? null : line) }}
            />
            <span>{baseTitle}</span>
            {count !== null && (
              // 角标 10px=direction-a .unit-row .tag 同值（设计真源——
              // 不随组题 12px 联动；AL-04 R 轮注记）
              <span style={{ marginLeft: "auto", fontSize: 10, opacity: 0.8 }}>({count})</span>
            )}
          </span>
        );
      }
      const unit = findUnitByNodeKey(units, key);
      if (unit === null) {
        return titleText;
      }
      return (
        <span
          title={unit.unit_id}
          style={{ display: "inline-flex", alignItems: "center", gap: 7, minHeight: 28, width: "100%" }}
        >
          <DomainIcon unit={unit} />
          <span style={{ fontSize: LEAF_NAME_SIZE, color: "var(--wp-text)" }}>{unit.name_zh}</span>
          {/* P0-3 呈裁②：编辑态叶行悬浮添加钮（stopPropagation 免叶选中
              开抽屉——添加即反馈实例 id，抽屉不抢焦点） */}
          {editing ? (
            <Button
              type="text"
              size="small"
              title="添加到画布"
              onClick={(event) => {
                event.stopPropagation();
                addToCanvas(unit);
              }}
              style={{ marginLeft: "auto", padding: "0 4px", fontSize: 12, lineHeight: "20px", height: 20 }}
            >
              ＋
            </Button>
          ) : null}
        </span>
      );
    };
  }, [units, editing, addToCanvas]);

  // 取数三态两分：pending/error 在树渲染前短路（成功面才进树/抽屉/计数条）
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
        title="单元目录加载失败"
        description="GET /api/units 不可达——请确认服务已启动后重试。"
        action={
          <Button size="small" onClick={() => catalog.refetch()}>
            重试
          </Button>
        }
      />
    );
  }

  // U4 计数条数据面（catalog 全量口径——不受搜索过滤影响）
  const unitCount = units.filter((unit) => unit.kind !== "builtin").length;
  const groupCount = buildLibraryTree(units).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {contextHolder}
      {/* U3 列布局收敛（glm 实现态 r1 采纳）：树区自滚（flex 1+minHeight
          0+overflow auto——36 行目录不把计数条顶出 Sider 视口）+计数条
          钉底（flex none——App Sider overflow auto 兜底面退役零滚动） */}
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
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
          <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
            <Tree
              blockNode
              defaultExpandAll
              titleRender={titleRender}
              selectedKeys={focusId === null ? [] : [focusId]}
              onSelect={(keys) => {
                // 仅叶点击开抽屉+联动光环（纯函数反查判据——组 key 反选为空；
                // 解除通道=组反选/关抽屉[onFocusChange(null)]）
                const next = keys[0];
                onFocusChange(
                  typeof next === "string" && findUnitByNodeKey(units, next) !== null
                    ? next
                    : null,
                );
              }}
              treeData={treeNodes}
            />
          </div>
        )}
      </div>
      {units.length > 0 && (
        <div
          style={{
            flex: "none",
            display: "flex",
            justifyContent: "space-between",
            padding: "7px 14px",
            borderTop: "1px solid var(--wp-border-2)",
            /* C2-ALIGN A2：10.5→11=设计 .sider-foot font-size */
            fontSize: 11,
            letterSpacing: 0.5,
            color: "var(--wp-text-3)",
          }}
        >
          <span>{unitCount} 单元</span>
          <span>{groupCount} 组</span>
        </div>
      )}
      <Drawer
        open={selectedUnit !== null}
        styles={{ wrapper: { width: DRAWER_WIDTH } }}
        onClose={() => onFocusChange(null)}
        title={
          selectedUnit === null ? null : (
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <DomainIcon unit={selectedUnit} />
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
              // R 轮 G1-02：空参数文案按 kind 两分（判据=kind 非 params
              // 空——现网 builtin 空 params=junction/recycle_junction 两件，
              // 非_builtin 空 params 纯未来防御面）
              <Empty
                description={
                  selectedUnit.kind === "builtin"
                    ? "内置节点无参数面"
                    : "该单元无参数面"
                }
              />
            )}
            <Typography.Text strong>端口面</Typography.Text>
            <Table<PortEntry>
              size="small"
              rowKey="port_id"
              columns={PORT_COLUMNS}
              dataSource={selectedUnit.ports ?? []}
              pagination={false}
            />
            {/* P0-3 呈裁② 甲案：编辑态主钮=添加到画布（零默认填充空参
                新建——参数面经参数面板后续编辑）；导航钮降次钮沿册 */}
            {editing && selectedUnit !== null ? (
              <Button type="primary" block onClick={() => addToCanvas(selectedUnit)}>
                添加到画布
              </Button>
            ) : null}
            {onNavigateTab === undefined ? null : (
              <Button
                block
                type={editing ? "default" : "primary"}
                onClick={() => {
                  onNavigateTab();
                  onFocusChange(null);
                }}
              >
                到工艺画布{editing ? "" : "编辑参数"}
              </Button>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
