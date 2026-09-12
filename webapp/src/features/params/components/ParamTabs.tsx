/**
 * 参数面板双分页容器（C2-ALIGN A5r）：单元标题+Segmented 双页——
 * 约束参数（选中单元 manifest 参数面=ParamForm 体，格式零变）/
 * 经验取值（原设计假设清单=AssumptionsPanel 体，行格式对齐参数面板）。
 *
 * 输入:  projectId+unitId 可空（null=未选中——约束页=提示文案，经验页
 *        恒可用：全局假设与单元无关）+catalog（标题单元名/badge+
 *        约束页计数）
 * 输出:  header（眉标+单元名+域 badge——ParamForm Q2 头部升位件）+
 *        Segmented 双选项（带计数）+双页体（display 切换恒挂载——
 *        两页草稿态跨页切换零丢失）
 *
 * 规格说明（用户澄清 2026-09-12——「约束参数和经验取值整体上移，
 *   以 AAO 为例『AAO 生物池』下方直接接两个分 tab」）：
 *   - 约束参数=「原本显示在上方的变量」（ParamForm 参数面）——格式
 *     与以前一样（Q1~Q7 全零变）；经验取值=「原本在设计假设里的变量」
 *     （registry 22 条全局假设）——格式和约束参数面板一样，左侧加
 *     展开钮（展开=默认取值+出处小字；说明固定格式后定[用户口径]）；
 *   - 分页=antd Segmented（嵌套 antd Tabs 属禁用面 global.css GC-08
 *     ——.ant-tabs 后代选择器会被 wp-scroll-tabs 拉满高破侧栏布局）；
 *   - 双页体恒挂载+display 切换（非条件卸载）：ParamForm 草稿/
 *     AssumptionsPanel 草稿跨页切换保留——卸载重挂即丢用户半成品；
 *   - 重挂载键：ParamForm 保持 `${projectId}:${unitId}`（R 轮 I1 沿袭
 *     ——切单元/切项目草稿不串）；AssumptionsPanel key=projectId
 *     （DS-05⑥ 沿袭）；容器键=projectId（切项目全复位）；
 *   - 未选中态：约束页=原 UNSELECTED_HINT 提示（canvasPane 迁入）；
 *     标题=「未选中单元」占位——经验页恒可达（假设编辑不依赖单元）。
 */
import { useState } from "react";
import { Segmented, Typography } from "antd";

import { useAssumptionCatalog, useUnitCatalog } from "../api/useUnitCatalog";
import { indexUnits } from "../lib/designParams";
import { useProjectDesign } from "../api/useProjectDesign";
import { AssumptionsPanel } from "./AssumptionsPanel";
import { ParamForm } from "./ParamForm";

/** business_line 中文词（badge——ParamForm Q2 头部升位沿袭；展示层
 * 翻译非业务复制）。 */
const LINE_LABELS: Record<string, string> = {
  municipal: "市政污水",
  conveyance: "输送提升",
  mine_water: "矿井水",
  sludge: "污泥处理",
};

/** 未选中提示（canvasPane UNSELECTED_HINT 迁入——A5r 假设区上移后
 * 提示归约束页空态）。 */
const UNSELECTED_HINT =
  "在画布中点击构筑物节点，即可在此编辑其参数并提交重算。";

export function ParamTabs({
  projectId,
  unitId,
}: {
  projectId: string;
  unitId: string | null;
}) {
  const [tab, setTab] = useState<"constraint" | "empirical">("constraint");
  const catalogQuery = useUnitCatalog();
  const assumptionsQuery = useAssumptionCatalog();
  const designQuery = useProjectDesign(projectId);
  // 标题面：单元名/badge（ParamForm Q2 同源——kind 通道 D1 沿袭）
  const index = indexUnits(catalogQuery.data?.units ?? []);
  const kind = designQuery.data?.nodeKinds[unitId ?? ""] ?? null;
  const meta = unitId === null ? undefined : index.get(kind ?? unitId);
  const paramCount = meta?.params?.length ?? 0;
  const assumptionCount = assumptionsQuery.data?.assumptions.length ?? 0;

  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* Q2 头部（ParamForm 升位件——眉标+单元名+域 badge，unitId 悬浮） */}
      <header
        style={{
          flex: "none",
          padding: "11px 14px 10px",
          borderBottom: "1px solid var(--wp-border-2)",
        }}
      >
        <div style={{ fontSize: 10, letterSpacing: 1.5, color: "var(--wp-text-3)" }}>
          参数面板
        </div>
        <div
          style={{ fontSize: 13.5, fontWeight: 600, color: "var(--wp-text-2)", marginTop: 2, display: "flex", alignItems: "center", gap: 8 }}
          title={unitId === null ? undefined : unitId + (kind !== null && kind !== unitId ? ` ← ${kind}` : "")}
        >
          {meta?.name_zh ?? (unitId === null ? "未选中单元" : unitId)}
          {meta ? (
            <span
              style={{ fontSize: 10, padding: "1px 7px", borderRadius: 8, background: "rgba(61,139,253,.16)", color: "#7ab2ff", border: "1px solid rgba(61,139,253,.35)" }}
            >
              {meta.kind === "builtin" ? "内置节点" : LINE_LABELS[meta.business_line] ?? meta.business_line}
            </span>
          ) : null}
        </div>
      </header>
      {/* A5r 双分页（Segmented——嵌套 Tabs 禁用面 GC-08；计数=目录驱动）；
          GOV5 视觉验收 V1 批注（2026-09-12 用户）：双选项等宽——block
          平分容器宽，取代按内容自适应（计数位数致两选项宽窄不一） */}
      <Segmented
        block
        value={tab}
        onChange={(value) => setTab(value as typeof tab)}
        style={{ flex: "none", margin: "0 14px 8px" }}
        options={[
          {
            value: "constraint",
            label: (
              <span>
                约束参数
                <span style={{ marginLeft: 4, fontSize: 11, color: "var(--wp-text-3)" }}>
                  {/* AL-06（A 二审 R2）：两页计数口径统一——目录未就绪
                      （0）与未选中同不显数字（经验页同式） */}
                  {unitId !== null && paramCount > 0 ? paramCount : ""}
                </span>
              </span>
            ),
          },
          {
            value: "empirical",
            label: (
              <span>
                经验取值
                <span style={{ marginLeft: 4, fontSize: 11, color: "var(--wp-text-3)" }}>
                  {assumptionCount > 0 ? assumptionCount : ""}
                </span>
              </span>
            ),
          },
        ]}
      />
      {/* 双页体恒挂载+display 切换（草稿跨页保留——见头注） */}
      <div
        data-testid="param-tab-constraint"
        style={{ flex: 1, minHeight: 0, display: tab === "constraint" ? "flex" : "none", flexDirection: "column" }}
      >
        {unitId === null ? (
          <div style={{ padding: "0 12px", flex: 1, overflow: "auto" }}>
            <Typography.Paragraph type="secondary">
              {UNSELECTED_HINT}
            </Typography.Paragraph>
          </div>
        ) : (
          <ParamForm
            key={`${projectId}:${unitId}`}
            projectId={projectId}
            unitId={unitId}
          />
        )}
      </div>
      <div
        data-testid="param-tab-empirical"
        style={{ flex: 1, minHeight: 0, display: tab === "empirical" ? "flex" : "none", flexDirection: "column" }}
      >
        <AssumptionsPanel key={projectId} projectId={projectId} />
      </div>
    </section>
  );
}
