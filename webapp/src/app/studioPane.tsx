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
 *        保持——切走不卸载防丢状态；五内容子面=注入 LazyPane 懒装载
 *        study/drawings/cost/compare/trust 五 pane 原件——study=M6 批
 *        2026-10-07 实装接入〔占位空态容器退役〕）
 *
 * 规格说明（draft-ia-v3 B-1 L44-45+mapping-2b4 M1 行；D3 装配纪律）：
 *   - 子面条仅 studio 槽渲染（本组件只挂 studio 槽 children——其余槽
 *     零渲染由 App 装配保证）；
 *   - mount-on-first-activation：activated 集合随 subface 到访增长，
 *     未到访子面零挂载（懒装载语义）；已挂载子面 display 切换保持
 *     （antd Tabs 行为等价——R1 状态保持泛化）；
 *   - study=studyPane 懒装载（M6 批 2026-10-07 实装——方案表段+联合
 *     结果段内容面；沿革：M1 立占位空态容器，M6 占位退役五子面全懒
 *     装载统一；?project= 空态前置提示归 studyPane 自持——D1）；
 *   - 本件零业务逻辑（纯装配——五 pane 内容/取数/门控全在各自 pane 内）。
 */
import { useEffect, useState, type ComponentType, type ReactNode } from "react";
import { Segmented } from "antd";

import { lazyPaneLoader } from "./lazyPaneLoader";
import type { StudioSubface } from "./router";

/** 五内容子面懒装载器（FE-2 形态——named export 选件；UF-66 批起=
 *  lazyPaneLoader 工厂形——chunk 失败重试经 cache-bust 恢复；回炉
 *  R1/R2：冷却窗限速+chunkHint=specifier 基名归因）。 */
const studyLoader = lazyPaneLoader(() => import("./studyPane"), "studyPane", (m) => m.StudyPane as ComponentType);
const drawingsLoader = lazyPaneLoader(() => import("./drawingsPane"), "drawingsPane", (m) => m.DrawingsPane as ComponentType);
const costLoader = lazyPaneLoader(() => import("./costPane"), "costPane", (m) => m.CostPane as ComponentType);
const compareLoader = lazyPaneLoader(() => import("./comparePane"), "comparePane", (m) => m.ComparePane as ComponentType);
const trustLoader = lazyPaneLoader(() => import("./trustPane"), "trustPane", (m) => m.TrustPane as ComponentType);

/** 子面条五项（受控 Segmented——值域=STUDIO_SUBFACES 单源面）。 */
const SUBFACE_OPTIONS: { label: string; value: StudioSubface }[] = [
  { label: "研究", value: "study" },
  { label: "图纸", value: "drawings" },
  { label: "概算", value: "cost" },
  { label: "对比", value: "compare" },
  { label: "可信度", value: "trust" },
];

/** 内容子面装载面（label 承 App 旧槽条页签名——pane 标题单源；M6 起
 *  study 头插=五子面全懒装载统一，首位与 SUBFACE_OPTIONS「研究」对齐）。 */
const CONTENT_FACES: { face: StudioSubface; label: string; load: () => Promise<{ default: ComponentType }> }[] = [
  { face: "study", label: "方案研究", load: studyLoader },
  { face: "drawings", label: "图纸预览", load: drawingsLoader },
  { face: "cost", label: "概算", load: costLoader },
  { face: "compare", label: "工况对比", load: compareLoader },
  { face: "trust", label: "可信度", load: trustLoader },
];

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
