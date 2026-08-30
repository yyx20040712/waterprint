/**
 * 设计假设面板：默认值显性化清单+行内编辑（§3 保证 7——DEFAULTS∪覆盖合成）。
 *
 * 输入:  projectId（useAssumptionCatalog 声明面+useProjectDesign 覆盖面+
 *        useReadProjectApiProjectsProjectIdGet 原始 GET 体——同键缓存共享）
 * 输出:  假设清单（key/默认值/合成值/dim/出处/说明/调向+覆盖标记蓝点——21 条
 *        registry 声明序）+行内 InputNumber 编辑/恢复默认+面板级「提交修改」
 *        一次 PUT /api/projects/{id}→invalidate read 键→自动 POST calc/run
 *
 * 规格说明（FE5 批 6b 段三只读实装；UX2 批 2026-08-30 编辑面收口——
 *   「本面板零编辑交互」挂账解除，D1-D4 预裁决落地）：
 *   - D1 编辑收集=collectAssumptionEdits 纯函数（reset 优先于 draft；draft=
 *     目录默认值等值免空写；NaN/Infinity/null 拒提交进 invalidKeys——行内
 *     error 态提示锁面板级提交）；「恢复默认」=overrides 删键回落 DEFAULTS
 *     （目录外键=删行；未覆盖行 no-op 不产变更）；R 轮 R1（DS-01 显示/
 *     收集优先级倒置修复）：onDraft 清 resets[key]/onReset 清 drafts[key]
 *     ——互斥最新意图胜（纯函数 reset 优先保持为共存防御面）；
 *   - D2 PUT 载荷=原始 GET 体（同键不带 select——raw 缓存共享，窄化产物
 *     禁当 body）经 withAssumptionOverrides 仅替换 design.assumption_overrides
 *     （结构化替换禁散拼，其余键原样回传）；
 *   - D3 409 保守呈现：ProjectLockedError（锁文件 {id}.wp.lock 存在——
 *     services/projects.py save 前置探测）→「项目已被他处修改，请刷新后
 *     重试」，不自动重试不 force（单用户内网工具；force 面=挂账晨裁）；
 *   - D4 PUT 成功→invalidate read 键→自动 POST /api/calc/run（conditions=
 *     rawCheckedUnits 原始 design.checked_units 数组原样透传，缺省=不传）；
 *     两步非原子：run 失败仅提示（保存不回滚——服务端回滚逻辑③类挂账）；
 *     成功后 ?task= 回写（ParamForm D3-③ 同构：replaceState 不触发导航+
 *     TASK_EVENT 派发通知已挂载 pane）；
 *   - 只读形态零回退（D3b）：清单结构（蓝点/值行/出处/说明）与错误/加载
 *     薄壳（Error.message 透出）维持 FE5 形态，编辑面为增量非替换。
 */
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, InputNumber, Typography } from "antd";

import { useRunCalculationApiCalcRunPost } from "../../../shared/api/generated/calc/calc";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
} from "../../../shared/api/generated/projects/projects";
import { WaterprintApiError } from "../../../shared/api/http";
import { TASK_EVENT } from "../../../shared/events";
import { useAssumptionCatalog } from "../api/useUnitCatalog";
import { useProjectDesign } from "../api/useProjectDesign";
import {
  buildAssumptionRows,
  collectAssumptionEdits,
  rawCheckedUnits,
  withAssumptionOverrides,
  type AssumptionRow,
} from "../lib/designParams";

const SELECT_BLUE = "#1668dc";
const GRAY_SMALL = { color: "#8c8c8c", fontSize: 11 };

/** 409 锁冲突保守提示（D3——不 force 不重试，刷新由用户裁量）。 */
const LOCK_HINT = "项目已被他处修改，请刷新后重试（并发写锁守门——不自动覆盖）";

/** 409 面=锁文件冲突（server error_type=ProjectLockedError；HTTP_409 兜底）。 */
function isLockConflict(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "ProjectLockedError" || error.code === "HTTP_409")
  );
}

/** 行内提示（无效 draft——面板级禁提交的行内反馈面）。 */
function InvalidHint() {
  return (
    <Typography.Text type="danger" style={{ fontSize: 11 }}>
      非数值或空——修正后才能提交
    </Typography.Text>
  );
}

/**
 * 单行假设：只读形态（键+蓝点+值行+出处/说明——FE5 零回退）+行内编辑面
 * （InputNumber 草稿+恢复默认——UX2 D1）。
 */
function AssumptionLine({
  row,
  draft,
  reset,
  invalid,
  onDraft,
  onReset,
}: {
  row: AssumptionRow;
  draft: number | null | undefined;
  reset: boolean;
  invalid: boolean;
  onDraft: (value: number | null) => void;
  onReset: () => void;
}) {
  // 编辑态显草稿；恢复默认态显默认值（目录外键 defaultValue=null=清空态）
  const effective =
    draft !== undefined ? draft : reset ? row.defaultValue : row.value;
  return (
    <div style={{ padding: "4px 0", borderBottom: "1px solid #303030" }}>
      <div style={{ fontFamily: "monospace", fontSize: 12, wordBreak: "break-all" }}>
        {row.key}
        {row.overridden ? (
          <span
            title="项目覆盖值（design.assumption_overrides）"
            style={{
              display: "inline-block",
              width: 6,
              height: 6,
              margin: "0 0 0 6px",
              borderRadius: 3,
              background: SELECT_BLUE,
            }}
          />
        ) : null}
      </div>
      <div style={{ fontSize: 12 }}>
        值 {row.value}
        {row.overridden && row.defaultValue !== null
          ? `（覆盖；默认 ${row.defaultValue}）`
          : row.overridden
            ? "（覆盖；目录外键）"
            : "（默认）"}
        {row.dim ? ` · ${row.dim}` : ""}
      </div>
      <div style={{ display: "flex", gap: 4, alignItems: "center", marginTop: 2 }}>
        <InputNumber
          size="small"
          status={invalid ? "error" : undefined}
          value={effective}
          onChange={(value) => onDraft(value)}
          style={{ width: 130 }}
        />
        <Button
          size="small"
          type="text"
          style={{ fontSize: 11, padding: "0 4px", color: GRAY_SMALL.color }}
          onClick={onReset}
        >
          恢复默认
        </Button>
      </div>
      {invalid ? <InvalidHint /> : null}
      {row.source || row.tuningDirection ? (
        <div style={GRAY_SMALL}>
          {[row.source, row.tuningDirection].filter(Boolean).join(" · ")}
        </div>
      ) : null}
      {row.note ? <div style={GRAY_SMALL}>{row.note}</div> : null}
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
  // 行内编辑态（组件内 useState——ParamForm D7 草稿态同构）
  const [drafts, setDrafts] = useState<Record<string, number | null>>({});
  const [resets, setResets] = useState<Record<string, true>>({});

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
  const overrideCount = rows.filter((row) => row.overridden).length;

  if (catalogQuery.isError || designQuery.isError) {
    const error = catalogQuery.error ?? designQuery.error;
    return (
      <section>
        <Typography.Title level={5}>设计假设</Typography.Title>
        <Typography.Text type="danger">
          假设清单加载失败：
          {error instanceof Error ? error.message : "未知错误"}
        </Typography.Text>
      </section>
    );
  }
  const submitDisabled =
    edits.invalidKeys.length > 0 ||
    !edits.changed ||
    save.isPending ||
    rawQuery.data === undefined;
  return (
    <section>
      <Typography.Title level={5}>设计假设</Typography.Title>
      {!catalogQuery.data || !designQuery.data ? (
        <Typography.Text type="secondary">假设清单加载中…</Typography.Text>
      ) : (
        <>
          <Typography.Text type="secondary" style={GRAY_SMALL}>
            {rows.length} 条 registry 声明序
            {overrideCount > 0 ? ` · ${overrideCount} 项项目覆盖` : " · 无项目覆盖"}
            （编辑后「提交修改」=保存+自动重算）
          </Typography.Text>
          <div style={{ maxHeight: 280, overflowY: "auto", marginTop: 4 }}>
            {rows.map((row) => (
              <AssumptionLine
                key={row.key}
                row={row}
                draft={drafts[row.key]}
                reset={resets[row.key] === true}
                invalid={edits.invalidKeys.includes(row.key)}
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
              />
            ))}
          </div>
          <div style={{ marginTop: 8, display: "grid", rowGap: 4 }}>
            <Button
              size="small"
              type="primary"
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
            {save.isError ? (
              <Typography.Text type="danger">
                {isLockConflict(save.error)
                  ? LOCK_HINT
                  : `假设保存失败：${save.error instanceof Error ? save.error.message : "未知错误"}`}
              </Typography.Text>
            ) : null}
            {save.isSuccess && run.isPending ? (
              <Typography.Text type="secondary">
                假设已保存——重算提交中…
              </Typography.Text>
            ) : null}
            {run.isSuccess ? (
              <Typography.Text type="success">
                已提交重算（任务 {(run.data?.task_id ?? "").slice(0, 8)}…）——
                方案页可看进度与失败回显。
              </Typography.Text>
            ) : null}
            {save.isSuccess && run.isError ? (
              <Typography.Text type="danger">
                假设已保存，但重算提交失败：
                {run.error instanceof Error ? run.error.message : "未知错误"}
                （保存不回滚——重新提交计算即可）
              </Typography.Text>
            ) : null}
          </div>
        </>
      )}
    </section>
  );
}
