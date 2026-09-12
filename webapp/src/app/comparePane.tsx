/**
 * compare 标签页装配：?project= 消费+ErrorBoundary+空态引导+CompareMatrix
 * +锁定基准交互+TASK_EVENT 事件桥（P2 第三批 ADR-018 D1/D3/D5）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook）+useCompareQuery 多工况
 *        对比报告（latest done calc 全工况聚合矩阵）+useProjectQuery raw
 *        （view.compare 锁定态读取/PUT 基座）+TASK_EVENT（apply 重算后）
 * 输出:  工况对比标签页（空态引导/404 引导/过期横幅/锁定基准条+矩阵）
 *
 * 规格说明（P2 第三批 ADR-018；trustPane 同构第六例）：
 *   - projectId 单一真相=URL；面板只读不回写（锁定除外——view 态 PUT，
 *     不参与 design_hash 不触发 stale——D3 语义）；
 *   - 锁定基准（D3）：view.compare={pinned,pinned_hash}——锁定时刻取
 *     报告 design_hash+勾选工况键集；过期判定=pinned_hash≠报告
 *     design_hash（改设计→重算→新结果件 hash 变）→警示横幅+「重新
 *     锁定」（键集保留∩现工况过滤失效键）；「解除锁定」清 compare；
 *   - 表层 stale（result_is_stale）：提示性信息横幅（建议重算），不阻断
 *     比对（与基准过期判定正交——ADR-018 D3 记档）；
 *   - TASK_EVENT 事件桥 invalidate compare 键（第六处监听——trustPane
 *     同制）。
 */
import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Checkbox, Typography, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useProjectQuery } from "../features/canvas/api/useProjectQuery";
import { CompareMatrix } from "../features/compare/components/CompareMatrix";
import { useCompareQuery } from "../features/compare/api/useCompareQuery";
import {
  filterLivePins,
  isPinStale,
  pinOf,
  type CompareReport,
} from "../features/compare/lib/compareView";
import { WaterprintApiError } from "../shared/api/http";
import {
  useSaveProjectApiProjectsProjectIdPut,
} from "../shared/api/generated/projects/projects";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——多工况对比针对最近完成计算的结果集装配。";

/** 404 引导（无 done calc——先提交计算）。 */
const NO_CALC_HINT =
  "——请先提交计算（工艺画布「提交计算」钮）完成后再回本标签查看多工况对比。";

/** raw.view.compare 宽容读取（异形/缺键=null）。 */
function viewCompareOf(raw: unknown): unknown {
  if (typeof raw !== "object" || raw === null) return null;
  const view = (raw as Record<string, unknown>)["view"];
  if (typeof view !== "object" || view === null) return null;
  return (view as Record<string, unknown>)["compare"];
}

/** PUT 载荷构造：raw 仅替换 view.compare（结构化替换——禁散拼）。 */
function withViewCompare(
  raw: unknown,
  compare: Record<string, unknown>,
): Record<string, unknown> {
  const base = (typeof raw === "object" && raw !== null ? raw : {}) as Record<
    string,
    unknown
  >;
  const view = (typeof base["view"] === "object" && base["view"] !== null
    ? base["view"]
    : {}) as Record<string, unknown>;
  return { ...base, view: { ...view, compare } };
}

export function ComparePane() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [selectedKeys, setSelectedKeys] = useState<string[] | null>(null);

  // TASK_EVENT 事件桥监听（第六处——apply 重算后失效键，面板刷新）
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/compare/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  const query = useCompareQuery(projectId);
  const rawQuery = useProjectQuery(projectId ?? "");
  const report: CompareReport | null = query.data ?? null;
  const pin = rawQuery.data !== undefined ? pinOf(viewCompareOf(rawQuery.data)) : null;

  // 勾选面缺省=全部工况键（首锁体验：全选一键锁）
  const checkKeys =
    selectedKeys ?? (report !== null ? [...report.condition_keys] : []);
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: () => {
        if (projectId !== null) {
          void queryClient.invalidateQueries({
            queryKey: [`/api/projects/${projectId}`],
          });
        }
        messageApi.success("锁定基准已保存（视图态——不触发重算）");
      },
      onError: (error) => {
        messageApi.error(
          error instanceof Error ? error.message : "锁定基准保存失败",
        );
      },
    },
  });

  /** 锁定/重新锁定（D3）：pinned=勾选键集+pinned_hash=报告 design_hash。 */
  const lockBaseline = (mode: "lock" | "relock" | "unlock") => {
    if (projectId === null || rawQuery.data === undefined) {
      messageApi.warning("项目数据未就绪，暂不能变更锁定基准");
      return;
    }
    const compare =
      mode === "unlock" || report === null || checkKeys.length === 0
        ? {}
        : { pinned: checkKeys, pinned_hash: report.design_hash };
    save.mutate({
      projectId,
      data: withViewCompare(rawQuery.data, compare) as never,
    });
  };

  const pinExpired = pin !== null && report !== null && isPinStale(pin, report);
  const livePins = useMemo(
    () =>
      pin !== null && report !== null
        ? filterLivePins(pin.pinned, report.condition_keys)
        : null,
    [pin, report],
  );

  if (projectId === null) {
    return <Typography.Paragraph type="secondary">{NO_PROJECT_HINT}</Typography.Paragraph>;
  }

  return (
    <ErrorBoundary label="工况对比">
      <section data-testid="wp-compare-pane">
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          多工况对比（基准 design/avg × 检修敏感性——行=指标，列=工况）
        </Typography.Title>
        {/* 术语说明（验收问询实录 2026-09-12「这个工况是干什么的」——
            工况=同一设计在不同运行条件下的计算口径，三族注释通俗化） */}
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 0 }}>
          「工况」= 同一套设计在不同运行条件下的计算口径：design=最高日
          最高时流量（设计峰值）、avg=平均日流量（日常运行）、
          design_offline_×××=某单元单池检修时的校核（该单元 n−1 池运行）。
          对比同一指标在各工况下的取值，可检验设计在峰值/日常/检修三种
          场景下是否都满足要求。
        </Typography.Paragraph>
        {contextHolder}
        {query.isError ? (
          <Typography.Paragraph type="danger">
            多工况对比报告取数失败：
            {query.error instanceof Error ? query.error.message : "未知错误"}
            {/* 仅 404 无 done calc 面附引导——网络错/窄化错不挂（trustPane 同款） */}
            {query.error instanceof WaterprintApiError &&
            query.error.code === "CompareSourceNotFoundError"
              ? NO_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : report === null ? (
          <Typography.Paragraph type="secondary">正在加载多工况对比报告…</Typography.Paragraph>
        ) : (
          <>
            {/* 表层 stale（提示性——结果已过期建议重算，不阻断比对） */}
            {report.stale ? (
              <Alert
                style={{ marginBottom: 8 }}
                type="info"
                showIcon
                title="当前结果集已过期（设计在计算后有变更）——建议重新提交计算后再比对。"
              />
            ) : null}
            {/* 锁定基准过期横幅（D3：pinned_hash≠结果件 design_hash） */}
            {pinExpired ? (
              <Alert
                style={{ marginBottom: 8 }}
                type="warning"
                showIcon
                title="锁定基准基于旧版设计，当前对比可能失真。"
                action={
                  <Button size="small" onClick={() => lockBaseline("relock")}>
                    重新锁定
                  </Button>
                }
              />
            ) : null}
            {/* 失效工况键提示（受检集变更后 pinned 键不在当前结果） */}
            {livePins !== null && livePins.expired.length > 0 ? (
              <Alert
                style={{ marginBottom: 8 }}
                type="info"
                showIcon
                title={`锁定基准含已移除工况：${livePins.expired.join("、")}（勾选集变更所致——重新锁定可清理）`}
              />
            ) : null}
            {/* 锁定基准条：勾选工况键集+锁定/解锁（view 态——不算 dirty） */}
            <div
              style={{
                display: "flex",
                gap: 12,
                alignItems: "center",
                flexWrap: "wrap",
                marginBottom: 8,
              }}
            >
              <Typography.Text type="secondary">对比基准：</Typography.Text>
              <Checkbox.Group
                options={report.condition_keys.map((key) => ({
                  value: key,
                  label: key,
                }))}
                value={checkKeys}
                onChange={(next) => setSelectedKeys(next as string[])}
              />
              {pin !== null ? (
                <>
                  <Button
                    size="small"
                    type="primary"
                    loading={save.isPending}
                    disabled={checkKeys.length === 0}
                    onClick={() => lockBaseline("relock")}
                  >
                    重新锁定
                  </Button>
                  <Button size="small" loading={save.isPending} onClick={() => lockBaseline("unlock")}>
                    解除锁定
                  </Button>
                </>
              ) : (
                <Button
                  size="small"
                  type="primary"
                  loading={save.isPending}
                  disabled={checkKeys.length === 0}
                  onClick={() => lockBaseline("lock")}
                >
                  锁定基准
                </Button>
              )}
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {pin !== null && !pinExpired
                  ? `已锁定（结果 ${pin.pinned_hash.slice(0, 8)}…）`
                  : "未锁定"}
              </Typography.Text>
            </div>
            <CompareMatrix
              report={report}
              pinned={pin !== null ? pin.pinned : null}
            />
          </>
        )}
      </section>
    </ErrorBoundary>
  );
}
