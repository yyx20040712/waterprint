/**
 * cost 标签页装配：?project= 消费+ErrorBoundary+空态引导+工况 Select+
 * EstimateTable+IndicatorsCard+"wp:task" 事件桥（FE8 D8）。
 *
 * 输入:  URL ?project=（与 canvas/viewer3d/solutions/elevation 共用）
 *        +useCostQuery 概算数据（latest done calc 四模块装配）+
 *        "wp:task" 事件（apply 重算后）
 * 输出:  概算标签页（空态引导/404 引导/分级汇总表+指标卡；工况切换=
 *        查询键切换按需触发；查询键前缀 invalidate 联动）
 *
 * 规格说明（FE8 批 6b 段六，D8；elevationPane 同构第四例）：
 *   - projectId 单一真相=URL：初值经 parseProjectParam+normalizeProjectId
 *     （.wp 尾缀归一）；面板只读不回写（挂账 UX 批）；
 *   - 非 lazy（无 echarts 大件——普通导入；elevation 懒加载面不适用）；
 *   - "wp:task" 事件监听（第四处内联+注记对齐——ParamForm dispatch/
 *     solutionsPane/elevationPane 三处先例；抽公共事件名模块挂账 UX 批）
 *     →invalidate ['/api/cost/'+projectId] 前缀键（工况两键全失效）；
 *   - 工况态组件内 useState（不建 store——FE5/6/7 先例，costStore 占位
 *     维持）：conditionKey=null 缺省请求→服务端 design 基线档回显
 *     （D2——缺省=design 非排序首键；Select 受控值=conditionKey??响应
 *     回显键）；Select 不写占位文案属性（grep 门禁规避）；
 *   - 空态：?project= 缺失=指引文案；查询 error 分级（elevationPane R3
 *     同款）：仅 WaterprintApiError.code==="CostSourceNotFoundError"
 *     （404 无 done calc）才附「先提交计算」引导——网络错/窄化
 *     CostViewError 不挂误导 hint；ErrorBoundary label=概算。
 */
import { useEffect, useState } from "react";
import { Select, Alert, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useCostQuery } from "../features/cost/api/useCostQuery";
import { EstimateTable } from "../features/cost/components/EstimateTable";
import { IndicatorsCard } from "../features/cost/components/IndicatorsCard";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { normalizeProjectId, parseProjectParam } from "./projectParam";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——概算针对最近完成计算的结果集装配。";

/** 404 引导（无 done calc——先提交计算）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签查看概算。";

export function CostPane() {
  const [projectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );
  // 工况态（null=缺省请求——服务端 design 基线档回显，D2）
  const [conditionKey, setConditionKey] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // "wp:task" 事件桥（第四处内联——ParamForm/solutionsPane/elevationPane
  // 三处先例对齐）：apply 重算后失效前缀键，面板刷新
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/cost/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  const query = useCostQuery(projectId, conditionKey);
  const view = query.data ?? null;

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">{NO_PROJECT_HINT}</Typography.Paragraph>
    );
  }

  return (
    <ErrorBoundary label="概算">
      <section>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          概算（分部分项+措施+间接+预备+税分级汇总）
        </Typography.Title>
        {query.isError ? (
          <Typography.Paragraph type="danger">
            概算取数失败：
            {query.error instanceof Error ? query.error.message : "未知错误"}
            {/* 仅 404 无 done calc 面附引导——网络错/窄化错不挂（R3 同款） */}
            {query.error instanceof WaterprintApiError &&
            query.error.code === "CostSourceNotFoundError"
              ? NO_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : view === null ? (
          <Typography.Paragraph type="secondary">
            正在加载概算…
          </Typography.Paragraph>
        ) : (
          <>
            {/* AUDIT2 FIX2（C-1 闭环）：结果集过期显式提示——禁静默旧图 */}
            {view.stale ? (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 8 }}
                message="设计已修改但未重算——下表基于旧结果集（服务端 stale 旗标；重新提交计算后刷新）"
              />
            ) : null}
            <div
              style={{
                display: "flex",
                gap: 16,
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Typography.Text type="secondary">工况：</Typography.Text>
                <Select
                  style={{ minWidth: 200 }}
                  value={conditionKey ?? view.condition_key}
                  options={view.conditions.map((key) => ({
                    value: key,
                    label: key,
                  }))}
                  onChange={(next) => setConditionKey(next)}
                />
              </div>
              <Typography.Text type="secondary">
                单价包版本 {view.price_data_version}｜设计规模{" "}
                {view.design_scale.toLocaleString("zh-CN", {
                  maximumFractionDigits: 1,
                })}{" "}
                m³/d（{view.sheet.detail_rows.length} 笔明细——行序=服务端装配序）
              </Typography.Text>
            </div>
            <EstimateTable view={view} />
            <div style={{ marginTop: 16 }}>
              <IndicatorsCard view={view} />
            </div>
          </>
        )}
      </section>
    </ErrorBoundary>
  );
}
