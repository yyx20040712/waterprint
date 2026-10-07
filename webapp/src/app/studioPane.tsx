/**
 * studio 槽装配件（M1 批 2026-10-06——二级子面条+五子面内容装配）。
 *
 * 输入:  subface（受控当前子面——App activeTarget 归一恒带）+
 *        onSubfaceChange（子面切换回调——App setTab 写 ?tab=studio.X）+
 *        renderLazyPane（懒装载壳注入——App LazyPane〔FE-2 先例泛化件〕
 *        经 prop 下穿，避免 studioPane→App 反向 import 环）
 * 输出:  studio 槽内容：Segmented 子面条五项（study|drawings|cost|compare|
 *        trust——嵌套 antd Tabs 属禁用面 global.css GC-08，ParamTabs
 *        Segmented 先例）+子面体（mount-on-first-activation+display 切换
 *        保持——切走不卸载防丢状态；四内容子面=注入 LazyPane 懒装载
 *        drawings/cost/compare/trust 四 pane 原件；study=占位空态容器）
 *
 * 规格说明（draft-ia-v3 B-1 L44-45+mapping-2b4 M1 行；D3 装配纪律）：
 *   - 子面条仅 studio 槽渲染（本组件只挂 studio 槽 children——其余槽
 *     零渲染由 App 装配保证）；
 *   - mount-on-first-activation：activated 集合随 subface 到访增长，
 *     未到访子面零挂载（懒装载语义）；已挂载子面 display 切换保持
 *     （antd Tabs 行为等价——R1 状态保持泛化）；
 *   - study 占位空态容器：M6 批实装方案研究面（方案表/敏感性/联合
 *     结果）；?project= 空态前置提示沿各 pane 现状惯例；
 *   - 本件零业务逻辑（纯装配——四 pane 内容/取数/门控全在各自 pane 内）。
 */
import { useEffect, useState, type ComponentType, type ReactNode } from "react";
import { Segmented, Typography } from "antd";

import { lazyPaneLoader } from "./lazyPaneLoader";
import type { StudioSubface } from "./router";
import { useProjectId } from "./useProjectId";

/** 四内容子面懒装载器（FE-2 形态——then 包装取 named export）。 */
const drawingsLoader = lazyPaneLoader(() => import("./drawingsPane"), (m) => m.DrawingsPane as ComponentType);
const costLoader = lazyPaneLoader(() => import("./costPane"), (m) => m.CostPane as ComponentType);
const compareLoader = lazyPaneLoader(() => import("./comparePane"), (m) => m.ComparePane as ComponentType);
const trustLoader = lazyPaneLoader(() => import("./trustPane"), (m) => m.TrustPane as ComponentType);

/** 子面条五项（受控 Segmented——值域=STUDIO_SUBFACES 单源面）。 */
const SUBFACE_OPTIONS: { label: string; value: StudioSubface }[] = [
  { label: "研究", value: "study" },
  { label: "图纸", value: "drawings" },
  { label: "概算", value: "cost" },
  { label: "对比", value: "compare" },
  { label: "可信度", value: "trust" },
];

/** 内容子面装载面（label 承 App 旧槽条页签名——pane 标题单源）。 */
const CONTENT_FACES: { face: StudioSubface; label: string; load: () => Promise<{ default: ComponentType }> }[] = [
  { face: "drawings", label: "图纸预览", load: drawingsLoader },
  { face: "cost", label: "概算", load: costLoader },
  { face: "compare", label: "工况对比", load: compareLoader },
  { face: "trust", label: "可信度", load: trustLoader },
];

/** study 占位文案（M6 批实装——brief D3 逐字）。 */
const STUDY_PLACEHOLDER =
  "方案研究（方案表/敏感性/联合结果）随 M6 批实装——枚举提交入口已在顶部「提交计算」命令带。";

/** ?project= 空态前置提示（各 pane 现状惯例同款——D7 措辞单源）。 */
const NO_PROJECT_HINT = "尚未选择项目——请先在画布槽选择项目";

export function StudioPane({
  subface,
  onSubfaceChange,
  renderLazyPane,
}: {
  subface: StudioSubface;
  onSubfaceChange: (next: StudioSubface) => void;
  renderLazyPane: (
    label: string,
    load: () => Promise<{ default: ComponentType }>,
  ) => ReactNode;
}) {
  // mount-on-first-activation：到访集合只增不减（display 切换保持态）
  const [activated, setActivated] = useState<ReadonlySet<StudioSubface>>(
    () => new Set([subface]),
  );
  useEffect(() => {
    setActivated((prev) => (prev.has(subface) ? prev : new Set(prev).add(subface)));
  }, [subface]);
  const [projectId] = useProjectId();

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: 0, height: "100%" }}>
      <div
        data-testid="wp-studio-subface"
        style={{
          flex: "none",
          display: "flex",
          alignItems: "center",
          padding: "6px 12px",
          background: "var(--wp-bg-container)",
          borderBottom: "1px solid var(--wp-border-2)",
        }}
      >
        <Segmented
          size="small"
          value={subface}
          options={SUBFACE_OPTIONS}
          onChange={(value) => onSubfaceChange(value as StudioSubface)}
        />
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        {activated.has("study") ? (
          <div style={subface === "study" ? undefined : { display: "none" }}>
            {projectId === null ? (
              <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
                {NO_PROJECT_HINT}
              </Typography.Paragraph>
            ) : null}
            <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
              {STUDY_PLACEHOLDER}
            </Typography.Paragraph>
          </div>
        ) : null}
        {CONTENT_FACES.map(({ face, label, load }) =>
          activated.has(face) ? (
            <div key={face} style={subface === face ? undefined : { display: "none" }}>
              {renderLazyPane(label, load)}
            </div>
          ) : null,
        )}
      </div>
    </div>
  );
}
