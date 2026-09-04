/**
 * drawings 标签页装配：?project= 消费+ErrorBoundary+空态引导+导出发起+
 * 图纸目录+元数据预览卡+线稿预览态接线（FE9 D7+B 批 D6）+"wp:task"
 * 事件桥。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook——与 canvas/viewer3d/
 *        solutions/elevation/cost 共用，S3 订阅面）+useExportsQuery
 *        产物列表+useConditionOptions 工况源+useUnitOptions 单元源
 *        （cost/projects 同端点同键缓存共享）+TASK_EVENT 事件
 * 输出:  图纸标签页（空态引导/导出/目录/元数据卡+线稿渲染区；查询键
 *        前缀 invalidate 联动）
 *
 * 规格说明（FE9 批 6b 段七 D7；costPane 同构第五例；B 批 D6 接线）：
 *   - projectId 单一真相=URL（useProjectId 共享 hook——S3 读方订阅面；
 *     .wp 尾缀归一在 hook 内）；面板只读不回写（挂账 UX 批）；
 *   - B 批 D6：preview 态=最近一次导出结果（ExportButton onExported
 *     回调 setPreview——scene/sceneError 喂 DrawingPreview 渲染区）；
 *     useEffect([projectId]) 切项目清空（他项目残影=误导面禁）；
 *   - 非 lazy（无 echarts 大件——普通导入）；
 *   - TASK_EVENT 事件桥监听（第五处监听——常量已收口 shared/events[S12]
 *     ——D7 勘误措辞；ParamForm dispatch/solutionsPane/elevationPane/
 *     costPane 四处先例）→invalidate ["/api/exports"] 前缀键=导出列表键
 *     失效（R5[DS-07]：工况源键 ['/api/cost/${projectId}'] 不在该前缀下，
 *     由 costPane 第四处事件桥 invalidate 同键缓存联动——注记如实）；
 *   - 工况/单元源查询错误分级呈现（costPane R3 同款口径）：工况源 404
 *     （CostSourceNotFoundError——无 done calc，与导出能力同根）附
 *     「先提交计算」引导；网络错/窄化错不挂误导 hint；
 *   - UX1 D3 单元 Select 可投影面过滤：ExportButton units=node.kind ∈
 *     目录 builtin 集（useUnitCatalog——同键 ['/api/units'] 缓存共享）
 *     之外的可投影单元（inlet 等内置节点不再混入——FE9 挂账[默认首选
 *     项恒 inlet→501]收口）；catalog 未就绪（loading/error）不过滤
 *     （优雅降级——过滤是增强非门禁，全量选项兜底）；内置四 kind
 *     值域零硬编码（真源=/api/units 目录判别通道）；
 *   - 空态：?project= 缺失=指引文案；产物列表空=空目录引导（先经
 *     上方导出发起产出图纸；R6[DS-03] 加载期 isPending 渲染 Spin——
 *     data 未到时 rows=[] 非空态语义，不误显引导）；ErrorBoundary
 *     label=图纸预览。
 */
import { useEffect, useState } from "react";
import { Alert, Spin, Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { ExportButton } from "../features/drawings/components/ExportButton";
import { DrawingPreview } from "../features/drawings/components/DrawingPreview";
import { SheetList } from "../features/drawings/components/SheetList";
import {
  useConditionOptions,
  useExportsQuery,
  useUnitOptions,
} from "../features/drawings/api/useExportsQuery";
import { useUnitCatalog } from "../features/drawings/api/useUnitCatalog";
import type { ExportArtifactResult } from "../features/drawings/api/useExportArtifact";
import { buildSheetRows } from "../features/drawings/lib/drawingsView";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——图纸针对最近完成计算的结果集导出。";

/** 工况源 404 引导（无 done calc——先提交计算；与导出 404 面同根语义）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签导出图纸。";

export function DrawingsPane() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  // 选中图纸键（SheetList 受控 radio——驱动 DrawingPreview 元数据卡）
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  // B 批 D6：线稿预览态=最近一次导出结果（绑定导出动作非行选中）
  const [preview, setPreview] = useState<ExportArtifactResult | null>(null);
  const queryClient = useQueryClient();

  // B 批 D6：切项目清空预览（他项目残影=误导面禁）
  useEffect(() => {
    setPreview(null);
  }, [projectId]);

  // TASK_EVENT 事件桥监听（第五处——常量已收口 shared/events[S12]；D7
  // 勘误措辞；ParamForm/solutionsPane/elevationPane/costPane 四处先例
  // 对齐）：apply 重算后失效前缀键，面板刷新
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
  // UX1 D3 可投影面过滤：node.kind ∈ 目录 builtin 集的内置节点剔除
  // （ExportButton 兜底首选项随之=首个可投影单元）；catalog 未就绪
  // （data undefined——loading/error）不过滤，全量选项兜底（增强非门禁）
  const builtinIds = useUnitCatalog().data ?? null;
  const unitRefs = unitQuery.data ?? [];
  const exportableUnits =
    builtinIds === null
      ? unitRefs.map((unit) => unit.unitId)
      : unitRefs
          .filter((unit) => !builtinIds.has(unit.kind ?? ""))
          .map((unit) => unit.unitId);

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
          图纸目录与导出（DXF 单元图+全厂总图+批量导出）
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
            units={exportableUnits}
            conditions={conditionQuery.data ?? []}
            onExported={setPreview}
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
          ) : exportsQuery.isPending ? (
            // R6（DS-03）：加载期不误显空目录引导（costPane「正在加载」专门
            // 分支同款——data 未到时 rows=[] 非「无产物」）
            <Spin />
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
              <DrawingPreview
                row={selected}
                scene={preview?.scene ?? null}
                sceneError={preview?.sceneError ?? null}
              />
            </div>
          </>
        )}
      </section>
    </ErrorBoundary>
  );
}
