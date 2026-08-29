/**
 * elevation 标签页装配：?project= 消费+懒加载 ProfileChart+ErrorBoundary+
 * 空态引导+工况切换+提升面板+"wp:task" 事件桥（FE7 D6/D8/D9）。
 *
 * 输入:  URL ?project=（与 canvas/viewer3d/solutions 共用）+useElevationQuery
 *        纵断数据（latest done calc 按需投影）+"wp:task" 事件（apply 重算后）
 * 输出:  高程纵断标签页（空态引导/404 引导/懒加载图表+ConditionSwitcher
 *        +PumpStationsPanel；查询键前缀 invalidate 联动）
 *
 * 规格说明（FE7 批 6b 段五，D6/D8/D9；viewer3dPane/solutionsPane 同构）：
 *   - projectId 单一真相=URL：初值经 parseProjectParam+normalizeProjectId
 *     （.wp 尾缀归一——与 canvas/viewer3d 共用）；面板只读不回写
 *     （项目选择器归 canvas 面——挂账 UX 批）；
 *   - D6 懒加载+chunk 失败重试（viewer3dPane R1 同款）：lazy 持入组件
 *     state——React.lazy 的 thenable 跨挂载持久，动态 import 一旦
 *     reject 复位边界不重执行；重试经 ErrorBoundary onRetry 以新 lazy
 *     实例重建（chartLoader 模块级具名常量复用装载函数）；echarts 经
 *     ProfileChart 动态链切独立异步 chunk（不触 vite.config 冻结面）；
 *   - D8 无任务面板/SSE（scene 同款按需取数）；"wp:task" 事件监听
 *     （事件名常量第三处内联+注记对齐——solutionsPane/ParamForm 两处
 *     先例；抽公共事件名模块挂账 UX 批）→invalidate
 *     ['/api/elevation/'+projectId] 前缀键（工况两键全失效——apply
 *     重算后面板刷新）；
 *   - D9 工况态组件内 useState（不建 store——FE5 D2/FE6 先例，
 *     elevationStore 占位维持）：conditionKey=null 缺省请求→服务端排序
 *     首键回显（Select 受控值=conditionKey??响应回显键）；切换经
 *     queryKey 全量进按需触发（§17.1）；
 *   - 空态：?project= 缺失=指引文案（先在工艺画布标签选择项目）；
 *     查询 error 分级（R3/zM-2 修复 2026-08-29）：仅当
 *     WaterprintApiError.code==="ElevationSourceNotFoundError"（404 无
 *     done calc）才附「先提交计算」引导——网络错/窄化 ElevationViewError
 *     不挂误导 hint（简报 D1 引导语口径针对 404 面）；ErrorBoundary
 *     label=高程纵断。
 */
import { lazy, Suspense, useEffect, useState } from "react";
import { Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { ConditionSwitcher } from "../features/elevation/components/ConditionSwitcher";
import { PumpStationsPanel } from "../features/elevation/components/PumpStationsPanel";
import { useElevationQuery } from "../features/elevation/api/useElevationQuery";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { normalizeProjectId, parseProjectParam } from "./projectParam";

/** ProfileChart 动态 import 装载器（模块级具名常量——echarts 异步 chunk 面）。 */
const chartLoader = () =>
  import("../features/elevation/components/ProfileChart").then((module) => ({
    default: module.ProfileChart,
  }));

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——高程纵断针对最近完成计算的结果集投影。";

/** 404 引导（无 done calc——先提交计算）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签查看纵断。";

export function ElevationPane() {
  const [projectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );
  // D9 工况态（null=缺省请求——服务端首键回显）
  const [conditionKey, setConditionKey] = useState<string | null>(null);
  // D6 lazy 持入 state（chunk 失败重试——viewer3dPane R1 同款）
  const [ProfileChart, setProfileChart] = useState(() => lazy(chartLoader));
  const queryClient = useQueryClient();

  // D8 "wp:task" 事件桥（第三处内联——ParamForm dispatch/solutionsPane
  // 监听两处先例对齐）：apply 重算后失效前缀键，面板刷新
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/elevation/${projectId}`],
        });
      }
    };
    window.addEventListener("wp:task", onTaskParam);
    return () => window.removeEventListener("wp:task", onTaskParam);
  }, [projectId, queryClient]);

  const query = useElevationQuery(projectId, conditionKey);
  const view = query.data ?? null;

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">{NO_PROJECT_HINT}</Typography.Paragraph>
    );
  }

  return (
    <ErrorBoundary
      label="高程纵断"
      onRetry={() => setProfileChart(lazy(chartLoader))}
    >
      <section>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          高程纵断（四线：地面/水面/池底/池顶）
        </Typography.Title>
        {query.isError ? (
          <Typography.Paragraph type="danger">
            纵断取数失败：
            {query.error instanceof Error
              ? query.error.message
              : "未知错误"}
            {/* R3（zM-2）：仅 404 无 done calc 面附引导——网络错/窄化错不挂 */}
            {query.error instanceof WaterprintApiError &&
            query.error.code === "ElevationSourceNotFoundError"
              ? NO_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : view === null ? (
          <Typography.Paragraph type="secondary">
            正在加载高程纵断…
          </Typography.Paragraph>
        ) : (
          <>
            <div
              style={{
                display: "flex",
                gap: 16,
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <ConditionSwitcher
                conditions={view.conditions}
                value={conditionKey ?? view.condition_key}
                onChange={(next) => setConditionKey(next)}
              />
              <Typography.Text type="secondary">
                {view.stations.length} 站（站位序=流程装配序）
              </Typography.Text>
            </div>
            <Suspense fallback={<div>纵断图加载中…</div>}>
              <ProfileChart view={view} />
            </Suspense>
            <PumpStationsPanel view={view} />
          </>
        )}
      </section>
    </ErrorBoundary>
  );
}
