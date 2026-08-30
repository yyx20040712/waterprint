/**
 * drawings 标签页装配：?project= 消费+ErrorBoundary+空态引导+导出发起+
 * 图纸目录+元数据预览卡+"wp:task" 事件桥（FE9 D7）。
 *
 * 输入:  URL ?project=（与 canvas/viewer3d/solutions/elevation/cost 共用）
 *        +useExportsQuery 产物列表+useConditionOptions 工况源+useUnitOptions
 *        单元源（cost/projects 同端点同键缓存共享）+"wp:task" 事件
 * 输出:  图纸标签页（空态引导/导出/目录/元数据卡；查询键前缀 invalidate
 *        联动）
 *
 * 规格说明（FE9 批 6b 段七，D7；costPane 同构第五例）：
 *   - projectId 单一真相=URL：初值经 parseProjectParam+normalizeProjectId
 *     （.wp 尾缀归一）；面板只读不回写（挂账 UX 批）；
 *   - 非 lazy（无 echarts 大件——普通导入）；
 *   - "wp:task" 事件监听（第五处内联+注记对齐——ParamForm dispatch/
 *     solutionsPane/elevationPane/costPane 四处先例；抽公共事件名模块
 *     挂账 UX 批）→invalidate ["/api/exports"] 前缀键（列表+工况源子键
 *     全失效）；
 *   - 工况/单元源查询错误分级呈现（costPane R3 同款口径）：工况源 404
 *     （CostSourceNotFoundError——无 done calc，与导出能力同根）附
 *     「先提交计算」引导；网络错/窄化错不挂误导 hint；
 *   - 空态：?project= 缺失=指引文案；产物列表空=空目录引导（先经
 *     上方导出发起产出图纸）；ErrorBoundary label=图纸预览。
 */
import { useEffect, useState } from "react";
import { Alert, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { ExportButton } from "../features/drawings/components/ExportButton";
import { DrawingPreview } from "../features/drawings/components/DrawingPreview";
import { SheetList } from "../features/drawings/components/SheetList";
import {
  useConditionOptions,
  useExportsQuery,
  useUnitOptions,
} from "../features/drawings/api/useExportsQuery";
import { buildSheetRows } from "../features/drawings/lib/drawingsView";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { normalizeProjectId, parseProjectParam } from "./projectParam";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——图纸针对最近完成计算的结果集导出。";

/** 工况源 404 引导（无 done calc——先提交计算；与导出 404 面同根语义）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签导出图纸。";

export function DrawingsPane() {
  const [projectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );
  // 选中图纸键（SheetList 受控 radio——驱动 DrawingPreview 元数据卡）
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // "wp:task" 事件桥（第五处内联——ParamForm/solutionsPane/elevationPane/
  // costPane 四处先例对齐）：apply 重算后失效前缀键，面板刷新
  useEffect(() => {
    const onTaskParam = () => {
      void queryClient.invalidateQueries({ queryKey: ["/api/exports"] });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [queryClient]);

  const exportsQuery = useExportsQuery(projectId);
  const conditionQuery = useConditionOptions(projectId);
  const unitQuery = useUnitOptions(projectId);

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">
        {NO_PROJECT_HINT}
      </Typography.Paragraph>
    );
  }

  const rows = buildSheetRows(exportsQuery.data ?? []);
  const selected = rows.find((row) => row.key === selectedKey) ?? null;

  return (
    <ErrorBoundary label="图纸预览">
      <section>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          图纸预览（DXF 单元图导出+产物目录）
        </Typography.Title>
        {conditionQuery.isError ? (
          <Typography.Paragraph type="danger">
            工况清单取数失败：
            {conditionQuery.error instanceof Error
              ? conditionQuery.error.message
              : "未知错误"}
            {/* 工况源 404=无 done calc（与导出能力同根）才附引导——网络错不挂 */}
            {conditionQuery.error instanceof WaterprintApiError &&
            conditionQuery.error.code === "CostSourceNotFoundError"
              ? NO_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : null}
        {unitQuery.isError ? (
          <Typography.Paragraph type="danger">
            单元清单取数失败：
            {unitQuery.error instanceof Error
              ? unitQuery.error.message
              : "未知错误"}
          </Typography.Paragraph>
        ) : null}
        <div style={{ marginBottom: 8 }}>
          <ExportButton
            projectId={projectId}
            units={unitQuery.data ?? []}
            conditions={conditionQuery.data ?? []}
          />
        </div>
        {rows.length === 0 ? (
          exportsQuery.isError ? (
            <Typography.Paragraph type="danger">
              产物目录取数失败：
              {exportsQuery.error instanceof Error
                ? exportsQuery.error.message
                : "未知错误"}
            </Typography.Paragraph>
          ) : (
            <Alert
              type="info"
              showIcon
              message="本项目尚无导出产物——经上方「导出图纸」产出后，目录与元数据预览在此呈现"
            />
          )
        ) : (
          <>
            <SheetList
              rows={rows}
              selectedKey={selectedKey}
              onSelect={setSelectedKey}
            />
            <div style={{ marginTop: 16 }}>
              <DrawingPreview row={selected} />
            </div>
          </>
        )}
      </section>
    </ErrorBoundary>
  );
}
