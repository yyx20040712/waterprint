/**
 * 参数表单：选中单元的 manifest 参数面+design 覆盖值→草稿→apply 提交重算。
 *
 * 输入:  projectId+unitId（canvasPane 选中态——D2 props 通道）+useUnitCatalog
 *        声明面+useProjectDesign 覆盖值（组件薄壳唯一数据源 §17.2）
 * 输出:  参数编辑表单（灰阶小字声明面/蓝点覆盖标记/草稿态/提交按钮+
 *        apply mutation 成功失效 read 键/错误 WaterprintApiError 透出）
 *
 * 规格说明（FE5 批 6b 段三，D1/D5/D7 实装——骨架期「错误消息来自 core/
 *   禁前端复制校验规则/单位换算在边界」三约沿袭：本表单零校验规则复制，
 *   range/grid 纯展示（range 无执行点=UI 展示数据——冻结 §三），语义校验
 *   经 calc 任务 failed 回流挂账 solutions 批）：
 *   - D1 声明面=UnitMetaEntry.params（default/dim/range/grid 灰阶小字）+
 *     design.nodes[unit_id] 覆盖值（有覆盖标蓝点）；builtin 条目（值含
 *     kind——nodeKinds 面换目录键，如 inlet→municipal_input）=META1 builtin
 *     投影 params（default 全 null：字段清单无默认值+design 值可编辑）；
 *   - D5 提交通道=POST /api/calc/solutions/apply（服务端原子样板：
 *     merged.update→save→自动 submit_calculation→失败回滚——借用语义+
 *     「params 专属端点归 server 批裁量」挂账）；成功后 invalidateQueries
 *     ['/api/projects/${projectId}']（read 键——canvas/params/假设三面同步
 *     刷新）；提交提示「已提交重算」（任务进度/failed 回显挂账 solutions 批）；
 *   - D7 草稿态=组件内 useState（单面板无跨组件态——paramsStore 挂账）：
 *     输入串经 normalizeDraftValue 归一，null（空/非数/非有限）=禁提交态
 *     （invalidFields 锁提交）；提交 payload=collectParamChanges 差异面
 *     （等值不产空写），值全 number（JSON 天然浮点形态）；
 *   - 错误呈现=Error.message 透出（WaterprintApiError message 归一——
 *     422/404/409 全走此面；窄化 DesignParamsError 同 Error 面）；
 *   - FE6 D3-③（挂账③收口）：apply onSuccess 回写 URL ?task=
 *     recalc_task_id（app/projectParam withTaskParam 逻辑内联四行——分层
 *     禁 import app；replaceState 不触发导航）——方案浏览标签的任务态
 *     面板经 ?task= 联动呈现重算进度与失败回显（消息文案同幅改）；
 *     R3（yI-1）回写后 dispatchEvent("wp:task")（事件名常量与
 *     solutionsPane 侧各自内联——分层禁 import app 双处注记对齐）：已
 *     挂载的方案 pane 经事件重读 URL 更新任务态（Tabs 保活下 useState
 *     初始化器仅首挂载执行+replaceState 无 popstate 的双局限收口）。
 */
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Input, Typography } from "antd";

import { useApplySolutionApiCalcSolutionsApplyPost } from "../../../shared/api/generated/calc/calc";
import type { ParamEntry } from "../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../shared/api/http";
import { useProjectDesign } from "../api/useProjectDesign";
import { useUnitCatalog } from "../api/useUnitCatalog";
import { collectParamChanges, indexUnits } from "../lib/designParams";

/** 侧栏宽度常量（canvasPane D4 组合面同款）。 */
const SELECT_BLUE = "#1668dc";
const GRAY_SMALL = { color: "#8c8c8c", fontSize: 11 };

/** 覆盖标记蓝点（design 值存在——非语义色，交互反馈面）。 */
function OverrideDot() {
  return (
    <span
      title="design 覆盖值（非 manifest 默认）"
      style={{
        display: "inline-block",
        width: 6,
        height: 6,
        margin: "0 0 0 6px",
        borderRadius: 3,
        background: SELECT_BLUE,
      }}
    />
  );
}

/** 灰阶小字声明面（dim/默认/范围/档位——展示数据不参与校验；覆盖行默认
 *  与 design 值并列显示——R2 修复（一审 M1），AssumptionsPanel 双显同构）。 */
function MetaLine({ entry }: { entry: ParamEntry }) {
  const parts: string[] = [entry.dim];
  if (entry.default !== null && entry.default !== undefined) {
    parts.push(`默认 ${entry.default}`);
  }
  if (entry.range) {
    parts.push(`范围 [${entry.range.min}, ${entry.range.max}]`);
  }
  if (entry.grid) {
    parts.push(`档位 [${entry.grid.join(", ")}]`);
  }
  return <div style={GRAY_SMALL}>{parts.join(" · ")}</div>;
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
        // R3（yI-1）：通知已挂载的方案 pane 重读 URL（"wp:task" 事件名
        // 与 solutionsPane 监听侧各自内联——分层禁 import app）
        window.dispatchEvent(
          new CustomEvent("wp:task", { detail: outcome.recalc_task_id }),
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
      ? `参数面加载失败：${
          loadError instanceof Error ? loadError.message : "未知错误"
        }`
      : null;

  return (
    <section>
      <Typography.Title level={5} style={{ marginTop: 0 }}>
        参数面板
      </Typography.Title>
      <div style={{ fontFamily: "monospace", fontSize: 12, wordBreak: "break-all" }}>
        {unitId}
        {meta ? `（${meta.name_zh}·${meta.kind === "builtin" ? "内置节点" : meta.business_line}）` : null}
        {kind !== null && kind !== unitId ? ` ← ${kind}` : null}
      </div>
      {errorText !== null ? (
        <Typography.Text type="danger">{errorText}</Typography.Text>
      ) : !catalogQuery.data || !design ? (
        <Typography.Text type="secondary">参数面加载中…</Typography.Text>
      ) : !meta ? (
        <Typography.Text type="warning">
          单元 {kind ?? unitId} 未在单元目录登记（GET /api/units）——无法编辑参数。
        </Typography.Text>
      ) : params.length === 0 ? (
        <Typography.Text type="secondary">该单元无声明参数面。</Typography.Text>
      ) : (
        <div style={{ display: "grid", rowGap: 8, marginTop: 8 }}>
          {params.map((entry) => {
            const fieldId = entry.field_id;
            const overridden = fieldId in values;
            const draftText = drafts[fieldId];
            const invalid =
              draftText !== undefined && invalidFields.includes(fieldId);
            return (
              <label key={fieldId} style={{ display: "block" }}>
                <span style={{ fontFamily: "monospace", fontSize: 12 }}>
                  {fieldId}
                  {overridden ? <OverrideDot /> : null}
                </span>
                <Input
                  size="small"
                  status={invalid ? "error" : undefined}
                  value={
                    draftText !== undefined
                      ? draftText
                      : overridden
                        ? String(values[fieldId])
                        : ""
                  }
                  onChange={(event) => {
                    setDrafts((prev) => ({
                      ...prev,
                      [fieldId]: event.target.value,
                    }));
                  }}
                />
                <MetaLine entry={entry} />
                {invalid ? (
                  <Typography.Text type="danger" style={{ fontSize: 11 }}>
                    非数值或空——修正后才能提交
                  </Typography.Text>
                ) : null}
              </label>
            );
          })}
          <div>
            <Button
              size="small"
              type="primary"
              loading={apply.isPending}
              disabled={submitDisabled}
              onClick={() => {
                apply.mutate({
                  data: { project_id: projectId, unit_id: unitId, params: changes },
                });
              }}
            >
              提交重算{changeCount > 0 ? `（${changeCount} 项）` : ""}
            </Button>
          </div>
          {apply.isSuccess ? (
            <Typography.Text type="success">
              已提交重算（任务 {(apply.data?.recalc_task_id ?? "").slice(0, 8)}…）——
              方案页可看进度与失败回显。
            </Typography.Text>
          ) : null}
          {apply.isError ? (
            <Typography.Text type="danger">
              提交失败：{apply.error instanceof Error ? apply.error.message : "未知错误"}
            </Typography.Text>
          ) : null}
        </div>
      )}
    </section>
  );
}
