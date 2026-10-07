/**
 * 左侧单元库浏览：搜索框+四线分组树（图标行）——app 层左列下区装配。
 *
 * 输入:  GET /api/units 目录（useListUnitsApiUnitsGet 生成 hook 直用——
 *        防第三处 useUnitCatalog 薄封装三胞胎）+搜索词（受控）+focusId
 *        （受控叶选中——App 持态 C2-lib 联动穿线）+onFocusChange
 * 输出:  左列单元库区（Input.Search+Tree 分组树[图标行]+Empty 空态+底部
 *        计数条）——详情呈现已收编右列 Settings 窗（M2 批 2026-10-08：
 *        Drawer 详情浮层退役→app/unitDetailPanel.tsx；选中库单元即显详情
 *        于 Settings——draft-ia-v3 §6 动线③）
 *
 * 规格说明（M2 批，简报 §一/§五；设计真源 reports/units-browser-design.md；
 *   C2-lib 批重制——briefs/task-C2-lib-plan.md §二 U1/U2/U4/U5+§五呈裁
 *   实录[用户裁定：码不显示/仅光环/计数条做]；M2 收编批 2026-10-08：
 *   Drawer 段+专属列定义/KindTag/DomainIcon 迁 unitDetailPanel；addToCanvas
 *   迁 useAddUnitToCanvas 单源〔叶行＋钮与本详情面板主钮两消费点共用〕）：
 *   - 组件零业务推导：树组装/过滤/叶反查/字形全在 ./unitLibraryTree
 *     纯函数，本件只渲染（§10.5/A7）；
 *   - U1 图标行（titleRender——antd v6 @rc-component/tree 在案）：叶行=
 *     [图标 22×22 域色三色组+字形]+中文名 13px 单主列；**英文码不
 *     显示**（用户裁定「尽量能不显示都不显示」——title 悬浮=全
 *     unit_id 为唯一保留追溯通道，零版面常显）；组行=域色短条+组名
 *     计数（title=string 保持——titleRender 按 group: 前缀分流）；
 *   - U3 联动（库→画布单向）：叶选中=onFocusChange(unit_id)（受控态
 *     不变——光环联动与右列详情显示同源）；CanvasPane 透传 CanvasFlow
 *     命中光环（wp-lib-hit——global.css）；画布节点点击不清 focus
 *     （P0-3 裁决保持——选中鎏金独立通道并存）；详情解除通道=组反选/
 *     详情✕/详情「到工艺画布」（右列 unitDetailPanel 承载）；
 *   - U4 计数条：左右分列（左「N 单元」右「M 组」——catalog 驱动；N=kind=unit
 *     条数，M=分组数含内置组；空态/加载态/错误态不渲染）；
 *   - antd Tree/Input.Search（M2 首用沿袭）；Table 列定义随 Drawer 段迁出；
 *   - 取数三态：isPending→Spin 居中；isError→Alert+重试（refetch——非
 *     ErrorBoundary 面：其只捕渲染异常不捕 query 态，偏差记档）；
 *     data.units 空→Empty 空态；过滤后无命中→Empty（命中空组已剔除）；
 *   - 搜索占位文案 props 键名拼接构造（grep 门禁扫描英文占位特征词——
 *     FE3 C3 同款规避口径，中文文案本身不受扫描面）；
 *   - P0-3（task-c2-edit-plan 呈裁② 甲案双入口）：编辑态（canvasStore
 *     会话——projectId 守卫）叶行悬浮「＋」钮（本件）+详情主钮「添加
 *     到画布」（unitDetailPanel）→ store.addUnit（designWriter 零默认
 *     填充③/`_2` 后缀③）+message 反馈实例 id——两入口经
 *     useAddUnitToCanvas 单源；只读态零呈现（编辑入口=画布工具条「编辑」
 *     钮——F2 断链根路径）。
 */
import { useMemo, useState } from "react";
import { Alert, Button, Empty, Input, Spin, Tree } from "antd";
import type { TreeDataNode } from "antd";

import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import { useListUnitsApiUnitsGet } from "../shared/api/generated/units/units";
import { domainColorOf, domainIconStyle } from "../features/canvas/lib/unitGlyph";
import {
  buildLibraryTree,
  filterLibraryTree,
  findUnitByNodeKey,
  libraryGlyph,
} from "./unitLibraryTree";
import { useAddUnitToCanvas } from "./useAddUnitToCanvas";

/** 组节点 key 前缀（titleRender 叶/组分流判据——unitLibraryTree 同值
 * 本地复制[导出面为纯函数 API 不含常量]；GL-04 R 轮：联动面=前缀+后缀
 * 双段——后缀 builtin/other 亦 unitLibraryTree 构造面同值魔串[组判色
 * 分支消费]，改组 key 构造须两文件四点联动）。 */
const GROUP_KEY_PREFIX = "group:";

/** 行图标尺寸/圆角（C2-ALIGN A4：22=direction-a .unit-ico 22×22
 * 对齐——「视觉稿态二冻结 20×20」由该批用户反馈+方向 A 真源取代）。 */
const ICON_SIZE = 22;
const ICON_RADIUS = 5;
/** 图标字形字号（C2-ALIGN A4：11=设计 .unit-ico font-size）。 */
const ICON_GLYPH_SIZE = 11;
/** 叶行中文名字号（C2-ALIGN A4：13——用户「文字大一点」，升至
 * 基准字号=providers fontSize 同值）。 */
const LEAF_NAME_SIZE = 13;
/** 组行题字号（C2-ALIGN A4：12——用户「大一点」+1 档）。 */
const GROUP_TITLE_SIZE = 12;

/** 搜索框占位文案 props（批3 段三豁免后还原明文——英文 place"holder"
 * 已移出 grep 门禁特征表[gate_patterns 豁免注记]，拼接规避退役）。 */
const SEARCH_HINT_PROPS = {
  placeholder: "搜索单元/名称",
} as const;

/** 域色图标框（叶行——22×22 三色组+字形；domainIconStyle 单源消费，
 * 与画布节点/详情面板头部图标恒同值）。 */
function LeafIcon({ unit }: { unit: UnitMetaEntry }) {
  const iconStyle = domainIconStyle(unit?.business_line);
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
}: {
  /** 受控叶选中（null=无选中——App 持态：右列详情显示+画布联动光环同源）。 */
  focusId: string | null;
  /** 叶选中/解除回调（叶点击=unit_id；组反选=null）。 */
  onFocusChange: (value: string | null) => void;
}) {
  const [search, setSearch] = useState("");
  const { addToCanvas, editing, contextHolder } = useAddUnitToCanvas();

  // 生成 hook 直用（零封装——防 useUnitCatalog 三胞胎）
  const catalog = useListUnitsApiUnitsGet();
  const units = useMemo(() => catalog.data?.units ?? [], [catalog.data]);
  const treeNodes = useMemo(
    () => filterLibraryTree(buildLibraryTree(units), search),
    [units, search],
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
        // +基名左置+计数右对齐（树数据 title 形态
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
          <LeafIcon unit={unit} />
          <span style={{ fontSize: LEAF_NAME_SIZE, color: "var(--wp-text)" }}>{unit.name_zh}</span>
          {/* P0-3 呈裁②：编辑态叶行悬浮添加钮（stopPropagation 免叶选中
              开详情——添加即反馈实例 id，详情不抢焦点） */}
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

  // 取数三态两分：pending/error 在树渲染前短路（成功面才进树/计数条）
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
      {/* U3 列布局收敛：树区自滚（flex 1+minHeight
          0+overflow auto——36 行目录不把计数条顶出视口）+计数条
          钉底（flex none） */}
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
                // 仅叶点击联动（纯函数反查判据——组 key 反选为空；
                // 解除通道=组反选/详情✕/详情「到工艺画布」）
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
    </div>
  );
}
