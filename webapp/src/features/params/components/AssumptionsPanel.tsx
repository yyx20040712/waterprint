/**
 * 经验取值页体（原设计假设面板——C2-ALIGN A5r 升位重构）：registry 全量
 * 假设清单+行内编辑，行格式对齐约束参数面板（ParamForm）+左侧展开钮。
 *
 * 输入:  projectId（useAssumptionCatalog 声明面+useProjectDesign 覆盖面+
 *        useReadProjectApiProjectsProjectIdGet 原始 GET 体——同键缓存共享）
 * 输出:  假设清单（行=左展开钮+中文物理意义标签[assumptionLabel]+覆盖蓝点
 *        +InputNumber 控件列[122px+dim 单位后缀——ParamForm 同款]+展开态
 *        「默认值 · 出处」小字+恢复默认链接）+页脚「提交修改」一次 PUT
 *        /api/projects/{id}→invalidate read 键→自动 POST calc/run
 *
 * 规格说明（FE5 只读实装；UX2 2026-08-30 编辑面 D1-D4；C2-ALIGN A5r
 *   2026-09-12 用户澄清重构——「右边是原本在设计假设里的变量，格式和
 *   约束参数面板里一样只不过左侧加了展开按钮，展开后会在下方用小字
 *   标注默认取值和出处」「所有参数都要显示物理意义而不是代码名称」）：
 *   - 升位：独立 section 退役——本件=ParamTabs 经验取值页体（标题/分页
 *     在容器层）；假设与单元无关恒全量（22 条 registry 序）；
 *   - 行格式=ParamForm 同构：标签列 12.5px text-2（label=assumptionLabel
 *     中文物理意义，key 悬浮=代码名追溯通道）+控件列 Space.Compact
 *     [InputNumber 122+单位后缀 dimUnit——共享导出常量]；差异仅左侧
 *     ▸/▾ 展开钮+展开态小字行；
 *   - 展开态=「默认 X · 出处」（用户口径最小集）+覆盖行「恢复默认」
 *     文字链接（UX2 D1 reset=删覆盖键回落 DEFAULTS——未覆盖行 no-op
 *     不渲染链接）；调节向/说明=固定格式后定（用户「后面再加」挂账）；
 *   - 折叠态=行仅标签+控件（覆盖蓝点标记）——与参数行完全同貌；
 *   - D1-D4 编辑链路零变：collectAssumptionEdits 收集（draft/reset
 *     互斥最新意图胜）/PUT 载荷 withAssumptionOverrides/409 保守呈现/
 *     invalidate+自动重算+?task= 回写；
 *   - 错误/加载薄壳（D3b 零回退——Error.message 透出）。
 */
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { DownOutlined, RightOutlined } from "@ant-design/icons";
import { Button, InputNumber, Space, Typography } from "antd";

import { useRunCalculationApiCalcRunPost } from "../../../shared/api/generated/calc/calc";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
} from "../../../shared/api/generated/projects/projects";
import { LOCK_HINT, WaterprintApiError, isLockConflict } from "../../../shared/api/http";
import { dimUnit } from "../../../shared/dimLabels";
import { TASK_EVENT } from "../../../shared/events";
import { useAssumptionCatalog } from "../api/useUnitCatalog";
import { useProjectDesign } from "../api/useProjectDesign";
import {
  buildAssumptionRows,
  collectAssumptionEdits,
  rawCheckedUnits,
  trimFloatNoise,
  withAssumptionOverrides,
  type AssumptionRow,
} from "../lib/designParams";
import { assumptionLabel } from "../lib/assumptionLabels";
import { CONTROL_WIDTH, UNIT_SUFFIX_STYLE } from "./ParamForm";

const SELECT_BLUE = "#1668dc";
/* GRAY_SMALL #8c8c8c=原假设面板存量灰（UX2 沿袭——antd 灰非 --wp 轴
 * 色；轴化 var(--wp-text-3)=#5d7290 观感变暗→视觉终裁已过的观感面
 * 不动；AL-N-03 R2 注记存量例外）。 */
const GRAY_SMALL = { color: "#8c8c8c", fontSize: 11 };

/** 展开钮（左侧——用户口径；约束参数面板行无此钮=两页唯一形态差）。 */
function ExpandToggle({
  expanded,
  onToggle,
}: {
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <Button
      type="text"
      size="small"
      aria-label={expanded ? "收起" : "展开"}
      aria-expanded={expanded}
      onClick={onToggle}
      style={{ flex: "none", width: 18, height: 18, minWidth: 18, padding: 0, color: GRAY_SMALL.color }}
    >
      {expanded ? (
        <DownOutlined style={{ fontSize: 9 }} />
      ) : (
        <RightOutlined style={{ fontSize: 9 }} />
      )}
    </Button>
  );
}

/** 单行假设：折叠=标签+控件（参数行同貌）；展开=默认/出处小字+恢复默认。 */
function AssumptionLine({
  row,
  draft,
  reset,
  invalid,
  expanded,
  onDraft,
  onReset,
  onToggleExpand,
}: {
  row: AssumptionRow;
  draft: number | null | undefined;
  reset: boolean;
  invalid: boolean;
  expanded: boolean;
  onDraft: (value: number | null) => void;
  onReset: () => void;
  onToggleExpand: () => void;
}) {
  // 编辑态显草稿；恢复默认态显默认值（目录外键 defaultValue=null=清空态）
  const effective =
    draft !== undefined ? draft : reset ? row.defaultValue : row.value;
  return (
    // 行分隔 rgba(27,44,73,.55)=--wp-border-2 #1b2c49 的 55% alpha 浅化
    // 派生——ParamForm 参数行存量同值（格式对齐复制；AL-N-02 R2 注记）
    <div
      data-testid={`assumption-row-${row.key}`}
      style={{ display: "flex", gap: 4, padding: "7px 0", borderBottom: "1px solid rgba(27,44,73,.55)" }}
    >
      <div style={{ flex: "none", paddingTop: 3 }}>
        <ExpandToggle expanded={expanded} onToggle={onToggleExpand} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
          {/* 标签列=ParamForm Q3 同构（中文物理意义 12.5 text-2+蓝点+
              key 悬浮追溯） */}
          <span
            title={row.key}
            style={{ fontSize: 12.5, color: "var(--wp-text-2)", display: "inline-flex", alignItems: "center", gap: 6, minWidth: 0 }}
          >
            {assumptionLabel(row.key)}
            {row.overridden ? (
              <span
                title="项目覆盖值（design.assumption_overrides）"
                style={{ display: "inline-block", width: 6, height: 6, borderRadius: 3, background: SELECT_BLUE }}
              />
            ) : null}
          </span>
          {/* 控件列=ParamForm Q4 同构（Space.Compact+122px+单位后缀） */}
          <Space.Compact style={{ flex: "none" }}>
            <InputNumber
              size="small"
              status={invalid ? "error" : undefined}
              value={effective}
              onChange={(value) => onDraft(value)}
              style={{ width: CONTROL_WIDTH }}
            />
            {dimUnit(row.dim) ? (
              <span data-testid={`assumption-unit-${row.key}`} style={UNIT_SUFFIX_STYLE}>
                {dimUnit(row.dim)}
              </span>
            ) : null}
          </Space.Compact>
        </div>
        {invalid ? (
          <Typography.Text type="danger" style={{ fontSize: 11 }}>
            非数值或空——修正后才能提交
          </Typography.Text>
        ) : null}
        {/* 展开态：默认值+出处（用户口径最小集——说明固定格式后定挂账）
            +覆盖行恢复默认链接（UX2 D1=删覆盖键；未覆盖行 no-op 不渲染） */}
        {expanded ? (
          <div style={{ ...GRAY_SMALL, paddingTop: 3, wordBreak: "break-all" }}>
            默认{" "}
            {row.defaultValue === null
              ? "—（目录外键）"
              : trimFloatNoise(row.defaultValue)}
            {row.source ? ` · ${row.source}` : ""}
            {row.overridden ? (
              <Button
                type="link"
                size="small"
                style={{ padding: 0, marginLeft: 8, height: "auto", fontSize: 11 }}
                onClick={onReset}
              >
                恢复默认
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function AssumptionsPanel({ projectId }: { projectId: string }) {
  const catalogQuery = useAssumptionCatalog();
  const designQuery = useProjectDesign(projectId);
  // UX2 D2：原始 GET 体（同键 ['/api/projects/${id}'] 不带 select——raw
  // 缓存自动共享；PUT 载荷唯一数据源，窄化产物禁当 body）
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId);
  const queryClient = useQueryClient();
  // 行内编辑态（跨分页/跨展开保持——ParamTabs display 切换恒挂载）
  const [drafts, setDrafts] = useState<Record<string, number | null>>({});
  const [resets, setResets] = useState<Record<string, true>>({});
  const [expandedKeys, setExpandedKeys] = useState<ReadonlySet<string>>(
    () => new Set(),
  );

  // D4 自动重算（两步非原子的第二步——失败仅提示不回滚保存）
  const run = useRunCalculationApiCalcRunPost<WaterprintApiError>({
    mutation: {
      // 成功后 ?task= 回写（ParamForm D3-③ 同构——分层禁 import app，
      // replaceState 不触发导航；TASK_EVENT 通知已挂载 pane 重读 URL）
      onSuccess: (outcome) => {
        const search = new URLSearchParams(window.location.search);
        search.set("task", outcome.task_id);
        window.history.replaceState(
          null,
          "",
          `${window.location.pathname}?${search.toString()}`,
        );
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: outcome.task_id }),
        );
      },
    },
  });
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        // 保存成功即清编辑态（invalidate 后清单随 refetch 回显新覆盖面）
        setDrafts({});
        setResets({});
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
        // D4：conditions=GET 原始 design.checked_units 数组原样透传
        const conditions = rawCheckedUnits(rawQuery.data);
        run.mutate({
          data: {
            project_id: projectId,
            ...(conditions !== undefined ? { conditions } : {}),
          },
        });
      },
    },
  });

  // AL-03（D 一审 R 轮）：useMemo 恢复——原面板纪律沿袭（query data
  // 引用已稳+22 行规模无实害，但纪律面零回退）
  const rows = useMemo(
    () =>
      buildAssumptionRows(
        catalogQuery.data?.assumptions ?? [],
        designQuery.data?.assumptionOverrides ?? {},
      ),
    [catalogQuery.data, designQuery.data],
  );
  const edits = useMemo(
    () => collectAssumptionEdits(rows, drafts, resets),
    [rows, drafts, resets],
  );

  if (catalogQuery.isError || designQuery.isError) {
    const error = catalogQuery.error ?? designQuery.error;
    return (
      <section style={{ padding: "0 14px 12px" }}>
        <Typography.Text type="danger">
          假设清单加载失败：
          {error instanceof Error ? error.message : "未知错误"}
        </Typography.Text>
      </section>
    );
  }
  if (!catalogQuery.data || !designQuery.data) {
    return (
      <section style={{ padding: "0 14px 12px" }}>
        <Typography.Text type="secondary">假设清单加载中…</Typography.Text>
      </section>
    );
  }
  const submitDisabled =
    edits.invalidKeys.length > 0 ||
    !edits.changed ||
    save.isPending ||
    rawQuery.data === undefined;
  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* body 滚动域（ParamForm Q1 同构） */}
      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "6px 14px 12px" }}>
        {rows.map((row) => (
          <AssumptionLine
            key={row.key}
            row={row}
            draft={drafts[row.key]}
            reset={resets[row.key] === true}
            invalid={edits.invalidKeys.includes(row.key)}
            expanded={expandedKeys.has(row.key)}
            // R1（DS-01 显示/收集优先级倒置修复 2026-08-30）：
            // onDraft 清 resets[key]/onReset 清 drafts[key]——互斥，
            // 最新用户意图胜（此前 reset 后再输入：显示 draft 值而
            // 收集 reset 优先=提交删键≠所见——倒置实锤）
            onDraft={(value) => {
              setDrafts((prev) => ({ ...prev, [row.key]: value }));
              setResets((prev) => {
                if (!(row.key in prev)) {
                  return prev;
                }
                const next = { ...prev };
                delete next[row.key];
                return next;
              });
            }}
            onReset={() => {
              setResets((prev) => ({ ...prev, [row.key]: true }));
              setDrafts((prev) => {
                if (!(row.key in prev)) {
                  return prev;
                }
                const next = { ...prev };
                delete next[row.key];
                return next;
              });
            }}
            onToggleExpand={() =>
              setExpandedKeys((prev) => {
                const next = new Set(prev);
                if (prev.has(row.key)) {
                  next.delete(row.key);
                } else {
                  next.add(row.key);
                }
                return next;
              })
            }
          />
        ))}
      </div>
      {/* foot（ParamForm Q6 同构形态——提交+状态行） */}
      <footer style={{ flex: "none", borderTop: "1px solid var(--wp-border-2)" }}>
        {save.isError ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-error)" }}>
            {isLockConflict(save.error)
              ? LOCK_HINT
              : `假设保存失败：${save.error instanceof Error ? save.error.message : "未知错误"}`}
          </div>
        ) : null}
        {save.isSuccess && run.isPending ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-text-3)" }}>
            假设已保存——重算提交中…
          </div>
        ) : null}
        {run.isSuccess ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-success)" }}>
            ✓ 已提交重算（任务 {(run.data?.task_id ?? "").slice(0, 8)}…）——方案页可看进度
          </div>
        ) : null}
        {save.isSuccess && run.isError ? (
          <div style={{ padding: "0 14px", paddingTop: 8, fontSize: 11, color: "var(--wp-error)" }}>
            假设已保存，但重算提交失败：
            {run.error instanceof Error ? run.error.message : "未知错误"}
            （保存不回滚——重新提交计算即可）
          </div>
        ) : null}
        <div style={{ padding: 10, display: "flex", gap: 8, alignItems: "center" }}>
          <Button
            size="small"
            type="primary"
            data-testid="assumption-submit"
            style={{ flex: 1 }}
            loading={save.isPending}
            disabled={submitDisabled}
            onClick={() => {
              const raw = rawQuery.data;
              if (raw === undefined) {
                return; // 原始体未就绪（同键缓存随清单同步——防御面）
              }
              save.mutate({
                projectId,
                data: withAssumptionOverrides(raw, edits.overrides),
              });
            }}
          >
            提交修改
          </Button>
        </div>
      </footer>
    </section>
  );
}
