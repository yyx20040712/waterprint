/**
 * 参数表单：选中单元的 manifest 参数面+design 覆盖值→草稿→apply 提交重算。
 *
 * 输入:  projectId+unitId（canvasPane 选中态——D2 props 通道）+useUnitCatalog
 *        声明面+useProjectDesign 覆盖值（组件薄壳唯一数据源 §17.2）
 * 输出:  参数编辑表单（C2-params 工程表单化重制 Q1~Q7——task-C2-params-
 *        plan.md §二+呈裁实录 §四b；glm D④「开发者表单」痛点收口）
 *
 * 规格说明（FE5 D1/D5/D7+FD PD7/PD8 沿袭；C2-params Q1~Q7）：
 *   - Q1 骨架=flex 列三层：head 固定/body 滚动（GR-40 收敛）/foot 固定
 *     （提交+重置常驻）；Q2 头部=眉标+单元名（secondary）+域 badge
 *     +unitId 隐藏（用户裁选——收进 title 悬浮，B2 PD8 追溯链保持）；
 *   - Q3 单行 field：左=label_zh（12.5px secondary——视觉稿 A「数据亮
 *     标签沉」[用户多模态对比裁选]+覆盖蓝点+field_id 悬浮）；右=控件
 *     122px 级（值 mono 白聚焦）；声明面 MetaLine 收敛进控件组 title
 *     悬浮（dim/默认/范围/档位全量——呈裁②已裁「进悬浮」）；
 *   - Q4 单位入控件：单位后缀 span（C2VD V6 addonAfter 弃用迁移——
 *     Space.Compact 包裹；dimUnit 零换算，无量纲/未知→无后缀）；步进钮
 *     antd 内建（93 连续参数 deriveStep 保持——键盘任意值不限 P0-4 沿袭）；
 *   - Q5 grid 档位 chips：行内嵌 chips（Tag 可点——回填 drafts 同通道
 *     [FD formatBackfill 同口径]）；当前显示值命中→蓝 fill 高亮；≤12 档
 *     换行/超 12 横滚；档位外自由值仍可手输（grid 纯展示冻结 §三沿袭）；
 *   - Q6 foot：提交重算（变更计数+disabled 保持）+重置 ghost（清 drafts
 *     ——apply 态不清）；apply 提示收敛 foot 上缘；
 *   - Q7 FD 可行域入口：◈+「可行域」蓝链保持——FeasibilityBar/
 *     Heatmap/回填/请求令牌零触碰（FD 已验收）；
 *   - 行为通道零变：D5 apply 原子提交+invalidate+?task= 回写+wp:task
 *     派发；D7 草稿 normalizeDraftValue/invalidFields 锁提交保持。
 */
import { useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Input, InputNumber, Modal, Select, Space, Tag, Typography } from "antd";

import { useApplySolutionApiCalcSolutionsApplyPost } from "../../../shared/api/generated/calc/calc";
import type { ParamEntry } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { dimLabel, dimUnit } from "../../../shared/dimLabels";
import { TASK_EVENT } from "../../../shared/events";
import { useProjectDesign } from "../api/useProjectDesign";
import { useUnitCatalog } from "../api/useUnitCatalog";
import {
  collectParamChanges,
  indexUnits,
  normalizeDraftValue,
  trimFloatNoise,
} from "../lib/designParams";
import { deriveStep, isContinuousParam } from "../lib/deriveStep";
import { useDesignMap } from "../feasibility/api/useDesignMap";
import { FeasibilityBar } from "../feasibility/components/FeasibilityBar";
import { FeasibilityHeatmap } from "../feasibility/components/FeasibilityHeatmap";
import { formatBackfill } from "../feasibility/lib/feasibility";
import type { DesignMapResponse } from "../../../shared/api/generated/model";

/** 覆盖标记蓝点（design 值存在——非语义色，交互反馈面）。 */
const SELECT_BLUE = "#1668dc";

/** 控件列宽（视觉稿 A num-input 122px 级——flex none 右对齐）。
 * C2-ALIGN A5r 导出共享：AssumptionsPanel（经验取值页）行格式对齐
 * 本面板——同宽控件列=「格式和约束参数面板里一样」的物理面。 */
export const CONTROL_WIDTH = 122;

/** C2VD V6：单位后缀样式（addonAfter→Space.Compact 迁移件——antd 内部
 * 类不依赖[v6 DOM 变体记档制]；取色全走 --wp 变量轴；-1px 左缘叠缝=
 * Compact 邻接共享边框惯例，右圆角 4=small 控件档。文字=--wp-text-2
 * （三段流 ds 建议提亮——text-3 在深底层级过低）。C2-ALIGN A5r 导出
 * 共享：AssumptionsPanel（经验取值页）行格式对齐本面板——同款后缀。 */
export const UNIT_SUFFIX_STYLE: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  width: 34,
  flex: "none",
  fontSize: 11,
  color: "var(--wp-text-2)",
  background: "var(--wp-bg-elevated)",
  border: "1px solid var(--wp-border)",
  borderLeft: "none",
  marginLeft: -1,
  borderTopRightRadius: 4,
  borderBottomRightRadius: 4,
};

/** F8 通道口归一（InputNumber onChange——步进/键入值 trimFloatNoise；
 * 非数值形态[防御]原样走 invalid 诚实拒路径）。 */
const draftValueOf = (value: number | string | null): string =>
  value === null || value === ""
    ? ""
    : typeof value === "number"
      ? trimFloatNoise(value)
      : value;

/** 声明面悬浮全量（Q3：MetaLine 常显收敛进 title——dim/默认/范围/档位）。 */
function metaTooltipText(entry: ParamEntry): string {
  const parts = [dimLabel(entry.dim)];
  if (entry.default !== null && entry.default !== undefined) {
    parts.push(`默认 ${entry.default}`);
  }
  if (entry.range) {
    parts.push(`范围 [${entry.range.min}, ${entry.range.max}]`);
  }
  if (entry.grid) {
    parts.push(`档位 [${entry.grid.join(", ")}]`);
  }
  parts.push(`field_id: ${entry.field_id}`);
  return parts.join(" · ");
}

/** 覆盖标记蓝点（design 值存在——非语义色，交互反馈面）。 */
function OverrideDot() {
  return (
    <span
      title="design 覆盖值（非 manifest 默认）"
      style={{ display: "inline-block", width: 6, height: 6, borderRadius: 3, background: SELECT_BLUE }}
    />
  );
}

export function ParamForm({
  projectId,
  unitId,
}: {
  projectId: string;
  unitId: string;
}) {
  const catalogQuery = useUnitCatalog();
  const designQuery = useProjectDesign(projectId);
  const queryClient = useQueryClient();
  // D7 草稿态：组件内 useState（paramsStore 挂账——单面板无跨组件态）
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const apply = useApplySolutionApiCalcSolutionsApplyPost<WaterprintApiError>({
    mutation: {
      // D5：apply 服务端已 save——失效 read 键驱动 canvas/params/假设刷新
      onSuccess: (outcome) => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
        // FE6 D3-③：?task= 回写（withTaskParam 逻辑内联——分层禁 import
        // app；replaceState 不触发导航，方案页任务态面板经参数联动）
        const search = new URLSearchParams(window.location.search);
        search.set("task", outcome.recalc_task_id);
        window.history.replaceState(
          null,
          "",
          `${window.location.pathname}?${search.toString()}`,
        );
        // R3（yI-1）：通知已挂载的 pane 重读 URL/失效查询键
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: outcome.recalc_task_id }),
        );
      },
    },
  });

  const index = useMemo(
    () => indexUnits(catalogQuery.data?.units ?? []),
    [catalogQuery.data],
  );
  const design = designQuery.data;
  // D1 builtin 通道：值含 kind → 目录查找键=kind 值（inlet→municipal_input）
  const kind = design?.nodeKinds[unitId] ?? null;
  const meta = index.get(kind ?? unitId);
  const values = design?.nodeParams[unitId] ?? {};
  const params = meta?.params ?? [];
  const { changes, invalidFields } = useMemo(
    () => collectParamChanges(params, values, drafts),
    [params, values, drafts],
  );
  const changeCount = Object.keys(changes).length;
  const submitDisabled =
    invalidFields.length > 0 || changeCount === 0 || apply.isPending;

  const loadError = catalogQuery.error ?? designQuery.error;
  const errorText =
    catalogQuery.isError || designQuery.isError
      ? `参数面加载失败：${loadError instanceof Error ? loadError.message : "未知错误"}`
      : null;

  // ── FD 可行域引导（PD7 2026-09-09）：行内 1D+模态 2D（Q7 零触碰） ──
  const [fdField, setFdField] = useState<string | null>(null);
  const [fdSecond, setFdSecond] = useState<string | null>(null);
  const [fdProduct, setFdProduct] = useState<DesignMapResponse | null>(null);
  const designMap = useDesignMap(projectId, unitId);
  const fdLoading = designMap.isPending;
  // R-1（A2-N-04，R 轮）：请求令牌——快速切换轴/第二轴时旧请求晚到
  // 不得覆盖新轴产物（useMutation 无请求身份校验，onSuccess 比对拦截）
  const fdReqId = useRef(0);
  const runFeasibility = (axes: { field_id: string }[]) => {
    const requestId = ++fdReqId.current;
    designMap.mutate(
      { axes },
      {
        onSuccess: (product) => {
          if (requestId === fdReqId.current) {
            setFdProduct(product);
          }
        },
      },
    );
  };
  const openFeasibility = (fieldId: string) => {
    if (fdField === fieldId) {
      return; // 已展开——不重复请求（继续微调面）
    }
    setFdField(fieldId);
    setFdSecond(null);
    setFdProduct(null);
    runFeasibility([{ field_id: fieldId }]);
  };
  const pickSecondAxis = (fieldId: string) => {
    if (fdField === null) {
      return;
    }
    setFdSecond(fieldId);
    setFdProduct(null);
    runFeasibility([{ field_id: fdField }, { field_id: fieldId }]);
  };
  const backfill = (key: string, value: number) => {
    setDrafts((prev) => ({ ...prev, [key]: formatBackfill(value) }));
  };
  const fdSecondOptions = params
    .filter(
      (entry) =>
        isContinuousParam(entry) && entry.field_id !== fdField,
    )
    .map((entry) => ({
      value: entry.field_id,
      label: `${entry.label_zh ?? entry.field_id}（${entry.field_id}）`,
    }));

  const loading = !catalogQuery.data || !design;

  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* C2-ALIGN A5r：Q2 头部（眉标+单元名+badge）外提至 ParamTabs
          ——「AAO 生物池」下方直接接双分页（用户澄清 2026-09-12）；
          本件自此=约束参数页体（body+foot），格式零变（Q1/Q3~Q7 沿袭）。 */}

      {/* Q1 body 滚动域 */}
      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "6px 14px 12px" }}>
        {errorText !== null ? (
          <Typography.Text type="danger">{errorText}</Typography.Text>
        ) : loading ? (
          <Typography.Text type="secondary">参数面加载中…</Typography.Text>
        ) : !meta ? (
          <Typography.Text type="warning">
            单元 {kind ?? unitId} 未在单元目录登记（GET /api/units）——无法编辑参数。
          </Typography.Text>
        ) : params.length === 0 ? (
          <Typography.Text type="secondary">该单元无声明参数面。</Typography.Text>
        ) : (
          params.map((entry) => {
            const fieldId = entry.field_id;
            const overridden = fieldId in values;
            const draftText = drafts[fieldId];
            const invalid =
              draftText !== undefined && invalidFields.includes(fieldId);
            // PD7 入口精确条件：仅连续区间参数（grid 缺席且 range 在场）
            const continuous = isContinuousParam(entry);
            const range = entry.range ?? null;
            // 显示值（chips 高亮判定源：草稿优先→design 覆盖→空；F8：
            // 覆盖值经 trimFloatNoise 归一——18 位浮点尾差根除）
            const overriddenValue =
              overridden && values[fieldId] !== undefined
                ? trimFloatNoise(values[fieldId])
                : null;
            const shownValue = draftText ?? overriddenValue ?? "";
            const shownStr = shownValue === "" ? null : shownValue;
            return (
              <label
                key={fieldId}
                style={{ display: "block", padding: "7px 0", borderBottom: "1px solid rgba(27,44,73,.55)" }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                  {/* Q3 标签列：label_zh secondary+蓝点+field_id 悬浮+FD 链 */}
                  <span style={{ minWidth: 0, flex: 1 }}>
                    <span
                      title={fieldId}
                      style={{ fontSize: 12.5, color: "var(--wp-text-2)", display: "inline-flex", alignItems: "center", gap: 6 }}
                    >
                      {entry.label_zh ?? fieldId}
                      {overridden ? <OverrideDot /> : null}
                    </span>
                    {continuous ? (
                      <Button size="small" type="link"
                        style={{ padding: 0, marginLeft: 8, height: "auto", fontSize: 11.5 }}
                        data-testid={`fd-entry-${fieldId}`}
                        loading={fdLoading && fdField === fieldId}
                        onClick={() => openFeasibility(fieldId)}
                      >
                        ◈ 可行域
                      </Button>
                    ) : null}
                  </span>
                  {/* Q4 控件列：值 mono 白+单位后缀+步进（C2VD V6 迁移注记）。 */}
                  {continuous && range !== null ? (
                    <Space.Compact style={{ flex: "none" }}>
                      <InputNumber size="small" status={invalid ? "error" : undefined}
                        // F8：步长经 trimFloatNoise 归一后再喂（deriveStep
                        // 黄金锁不动——噪声步长会被 antd 放大 18 位精度，消费点收口）
                        step={Number(trimFloatNoise(deriveStep(range)))}
                        style={{ width: CONTROL_WIDTH }}
                        title={metaTooltipText(entry)}
                        value={shownValue === "" ? "" : shownValue}
                        onChange={(value) =>
                          setDrafts((prev) => ({ ...prev, [fieldId]: draftValueOf(value) }))
                        }
                      />
                      {dimUnit(entry.dim) ? (
                        <span data-testid={`param-unit-${fieldId}`} style={UNIT_SUFFIX_STYLE}>
                          {dimUnit(entry.dim)}
                        </span>
                      ) : null}
                    </Space.Compact>
                  ) : (
                    <Space.Compact style={{ flex: "none" }}>
                      <Input
                        size="small"
                        status={invalid ? "error" : undefined}
                        style={{ width: CONTROL_WIDTH, flex: "none" }}
                        title={metaTooltipText(entry)}
                        value={shownValue}
                        onChange={(event) =>
                          setDrafts((prev) => ({ ...prev, [fieldId]: event.target.value }))
                        }
                        onBlur={(event) => {
                          // F8：失焦归一（可解析→trimFloatNoise；非数/空原样拒路径）
                          const parsed = normalizeDraftValue(event.target.value);
                          if (parsed !== null) {
                            setDrafts((prev) => ({ ...prev, [fieldId]: trimFloatNoise(parsed) }));
                          }
                        }}
                      />
                      {/* 参数面单位批（2026-09-12 用户裁定「入批处理」）：grid
                          档/自由值参数同获单位后缀——此前仅连续区间参数分支
                          有后缀（C2VD V6 Space.Compact 同制补齐）。 */}
                      {dimUnit(entry.dim) ? (
                        <span data-testid={`param-unit-${fieldId}`} style={UNIT_SUFFIX_STYLE}>
                          {dimUnit(entry.dim)}
                        </span>
                      ) : null}
                    </Space.Compact>
                  )}
                </div>
                {/* Q5 grid 档位 chips：点击回填+当前值高亮（≤12 换行/超 12 横滚） */}
                {entry.grid && entry.grid.length > 0 ? (
                  <span
                    style={{ display: "flex", flexWrap: entry.grid.length <= 12 ? "wrap" : "nowrap", overflowX: entry.grid.length <= 12 ? undefined : "auto", gap: 4, paddingTop: 5, justifyContent: "flex-end" }}
                  >
                    {entry.grid.map((option) => (
                      <Tag
                        key={String(option)}
                        style={{
                          marginInlineEnd: 0, fontSize: 10.5, lineHeight: "17px",
                          paddingInline: 8, borderRadius: 9, cursor: "pointer",
                          flex: "none", fontFamily: "var(--wp-font-mono)",
                          ...(shownStr !== null && shownStr === String(option)
                            ? { background: "rgba(61,139,253,.18)", color: "#7ab2ff", borderColor: "rgba(61,139,253,.45)" }
                            : {}),
                        }}
                        onClick={() => setDrafts((prev) => ({ ...prev, [fieldId]: String(option) }))}
                      >
                        {String(option)}
                      </Tag>
                    ))}
                  </span>
                ) : null}
                {invalid ? (
                  <Typography.Text type="danger" style={{ fontSize: 11 }}>
                    非数值或空——修正后才能提交
                  </Typography.Text>
                ) : null}
                {fdField === fieldId ? (
                  <div data-testid={`fd-panel-${fieldId}`}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                      <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                        第二轴（2D 热力图）
                      </Typography.Text>
                      <Select size="small" style={{ minWidth: 180 }} value={fdSecond ?? undefined}
                        options={fdSecondOptions} onChange={pickSecondAxis} data-testid="fd-second-axis"
                      />
                    </div>
                    {designMap.isError ? (
                      <Typography.Text type="danger" style={{ fontSize: 11 }}>
                        可行域求值失败：
                        {designMap.error instanceof Error
                          ? designMap.error.message
                          : "未知错误"}
                      </Typography.Text>
                    ) : fdProduct !== null && fdProduct.stats.total > 0 && fdSecond === null ? (
                      <FeasibilityBar
                        product={fdProduct}
                        onPick={(value) => backfill(fieldId, value)}
                      />
                    ) : fdLoading ? (
                      <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                        可行域求值中…
                      </Typography.Text>
                    ) : null}
                  </div>
                ) : null}
              </label>
            );
          })
        )}
      </div>

      {/* Q6 foot：apply 提示行+提交/重置常驻 */}
      <footer style={{ flex: "none", borderTop: "1px solid var(--wp-border-2)" }}>
        {apply.isSuccess ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-success)" }}>
            ✓ 已提交重算（任务 {(apply.data?.recalc_task_id ?? "").slice(0, 8)}…）——方案页可看进度
          </div>
        ) : null}
        {apply.isError ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-error)" }}>
            提交失败：{apply.error instanceof Error ? apply.error.message : "未知错误"}
          </div>
        ) : null}
        <div style={{ padding: 10, display: "flex", gap: 8, alignItems: "center" }}>
          <Button
            size="small"
            type="primary"
            loading={apply.isPending}
            disabled={submitDisabled}
            style={{ flex: 1 }}
            onClick={() =>
              apply.mutate({ data: { project_id: projectId, unit_id: unitId, params: changes } })
            }
          >
            提交重算{changeCount > 0 ? `（${changeCount} 项）` : ""}
          </Button>
          <Button
            size="small"
            ghost
            disabled={apply.isPending}
            onClick={() => setDrafts({})}
            title="清空全部草稿（恢复 design 值显示）"
          >
            ↺ 重置
          </Button>
        </div>
      </footer>

      {/* PD7 呈裁④：2D 模态热力图（手动关；回填后不自动关闭可微调）。
          R-1（G1-02）：关闭清产物并重取 1D——残留 2D 产物会使行内条死灰 */}
      <Modal
        open={fdSecond !== null}
        title={`可行域热力图——${fdProduct?.axes[0]?.label_zh ?? fdField ?? ""} × ${fdProduct?.axes[1]?.label_zh ?? fdSecond ?? ""}`}
        footer={null}
        onCancel={() => {
          setFdSecond(null);
          setFdProduct(null);
          if (fdField !== null) {
            runFeasibility([{ field_id: fdField }]);
          }
        }}
        width={720}
      >
        {designMap.isError ? (
          <Typography.Text type="danger">
            可行域求值失败：
            {designMap.error instanceof Error ? designMap.error.message : "未知错误"}
          </Typography.Text>
        ) : fdProduct !== null && fdProduct.mask !== null && fdField !== null && fdSecond !== null ? (
          <>
            <FeasibilityHeatmap
              product={fdProduct}
              onPick={(valueA, valueB) => {
                backfill(fdField, valueA);
                backfill(fdSecond, valueB);
              }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 11 }}>
              点击可行格（绿）回填两参数；点击不可行格（灰）吸附最近可行格。
              可行 {fdProduct.stats.feasible}/{fdProduct.stats.total}（
              {(fdProduct.stats.feasible_ratio * 100).toFixed(1)}%）。
            </Typography.Text>
          </>
        ) : (
          <Typography.Text type="secondary">可行域求值中…</Typography.Text>
        )}
      </Modal>
    </section>
  );
}
