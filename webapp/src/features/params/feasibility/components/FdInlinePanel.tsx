/**
 * fd 行内可行域面板（M2 批 2026-10-08——fd 段自 ParamForm 抽出〔预裁决 7
 * ——ParamForm 距 500 行墙仅 5 行，抽出为唯一解〕+§F.2 ①+②组合实装
 * 〔mapping-2b4 §F.2 呈裁建议：Settings 行内嵌入预览——1D 区间条行内
 * 常驻+2D 热力缩略行内+点击 2D 模态放大精读〕）。
 *
 * 输入:  projectId+unitId（design-map 求值域）+fieldId（第一轴=展开行参数）
 *        +params（fdSecondOptions 派生源——连续区间参数过滤）+onBackfill
 *        （草稿回填通道——两键同写零漂移，formatBackfill 归一在消费方）
 * 输出:  fd-panel（第二轴 Select+1D FeasibilityBar 行内常驻〔第二轴未选〕
 *        或 2D 热力缩略行内〔第二轴选定——fd-thumb 容器高 120 定值，内层
 *        wrapper pointerEvents=none 阻断格点击，FeasibilityHeatmap 原件
 *        零改 SVG viewBox 自适应缩略〕+点击缩略模态放大精读〔720——格
 *        点击回填两键/吸附/统计行〕）
 *
 * 规格说明（M2 批预裁决 7/8/9）：
 *   - 状态承接（逐字迁移自 ParamForm fd 段）：fdSecond/fdProduct/
 *     designMap/runFeasibility/pickSecondAxis+fdReqId 请求令牌（R-1
 *     A2-N-04——快速切换轴/第二轴时旧请求晚到不得覆盖新轴产物，
 *     onSuccess 比对拦截）；
 *   - 挂载即取 1D（openFeasibility「展开行→请求」语义——切参数行=
 *     本组件卸载/新实例挂载〔ParamForm 条件渲染 fdField===fieldId〕，
 *     全复位重取由卸载/重挂载承载，openFeasibility 同行早退保留在
 *     ParamForm）；切第二轴仍全复位重取（openFeasibility 现状语义不变）；
 *   - 模态关闭语义更新（预裁决 9——改 R-1/G1-02 行为，申报在批档）：
 *     onCancel=仅关模态，不清产物不重取（fdSecond/fdProduct 保持——
 *     缩略继续在场；R-1 当年「残留 2D 产物使行内条死灰」的病灶随行内
 *     2D 面存在而消失）；
 *   - 模态内 fd-heatmap 与缩略内 fd-heatmap 并存=DOM 双实例（测试探针
 *     getAllByTestId 口径）。
 */
import { useEffect, useRef, useState } from "react";
import { Modal, Select, Typography } from "antd";

import type { DesignMapResponse, ParamEntry } from "../../../../shared/api/generated/model";
import { isContinuousParam } from "../../lib/deriveStep";
import { useDesignMap } from "../api/useDesignMap";
import { FeasibilityBar } from "./FeasibilityBar";
import { FeasibilityHeatmap } from "./FeasibilityHeatmap";

/** 2D 缩略行内高度（定值——§F.2「2D 热力缩略」右列宽 360~420 呈现裁量）。 */
const THUMB_HEIGHT = 120;

export function FdInlinePanel({
  projectId,
  unitId,
  fieldId,
  params,
  onBackfill,
}: {
  projectId: string;
  unitId: string;
  fieldId: string;
  /** 声明面参数（fdSecondOptions 派生源——ParamForm meta.params 直传）。 */
  params: ParamEntry[];
  onBackfill: (key: string, value: number) => void;
}) {
  const [fdSecond, setFdSecond] = useState<string | null>(null);
  const [fdProduct, setFdProduct] = useState<DesignMapResponse | null>(null);
  // 模态开态（缩略点击开/onCancel 关——与 fdSecond 解耦：关闭不清产物）
  const [modalOpen, setModalOpen] = useState(false);
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
  // 挂载即取 1D（openFeasibility「展开行→请求」语义——fieldId 恒定于本
  // 实例生命周期，切参数行=卸载/新实例重挂载全复位重取）
  useEffect(() => {
    runFeasibility([{ field_id: fieldId }]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fieldId]);
  const pickSecondAxis = (secondId: string) => {
    setFdSecond(secondId);
    setFdProduct(null);
    setModalOpen(false); // 切第二轴=新求值全复位（模态若开着一并复位）
    runFeasibility([{ field_id: fieldId }, { field_id: secondId }]);
  };
  const fdSecondOptions = params
    .filter(
      (entry) => isContinuousParam(entry) && entry.field_id !== fieldId,
    )
    .map((entry) => ({
      value: entry.field_id,
      label: `${entry.label_zh ?? entry.field_id}（${entry.field_id}）`,
    }));

  return (
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
      ) : fdSecond === null ? (
        /* §F.2 ①：1D 区间条行内常驻（第二轴未选——现状保持，行内非模态） */
        fdProduct !== null && fdProduct.stats.total > 0 ? (
          <FeasibilityBar
            product={fdProduct}
            onPick={(value) => onBackfill(fieldId, value)}
          />
        ) : fdLoading ? (
          <Typography.Text type="secondary" style={{ fontSize: 11 }}>
            可行域求值中…
          </Typography.Text>
        ) : null
      ) : fdProduct !== null && fdProduct.mask !== null ? (
        /* §F.2 ②：2D 热力缩略行内（高 120 定值；内层 wrapper pointerEvents
           =none 阻断格点击——精读交互收归模态；点击缩略开模态放大精读） */
        <div
          data-testid="fd-thumb"
          title="点击放大精读"
          onClick={() => setModalOpen(true)}
          style={{ height: THUMB_HEIGHT, marginTop: 4, cursor: "pointer" }}
        >
          <div style={{ pointerEvents: "none", width: "100%", height: "100%" }}>
            <FeasibilityHeatmap
              product={fdProduct}
              onPick={(valueA, valueB) => {
                onBackfill(fieldId, valueA);
                onBackfill(fdSecond, valueB);
              }}
            />
          </div>
        </div>
      ) : fdLoading ? (
        <Typography.Text type="secondary" style={{ fontSize: 11 }}>
          可行域求值中…
        </Typography.Text>
      ) : null}

      {/* 模态放大精读（720 沿现状：格点击回填两键/吸附/统计行；手动关）。
          M2 预裁决 9：onCancel=仅关模态不清产物不重取（fdSecond/fdProduct
          保持——缩略继续在场；R-1「残留 2D 产物使行内条死灰」病灶随行内
          2D 面存在而消失——语义更新申报在批档） */}
      <Modal
        open={modalOpen}
        title={`可行域热力图——${fdProduct?.axes[0]?.label_zh ?? fieldId ?? ""} × ${fdProduct?.axes[1]?.label_zh ?? fdSecond ?? ""}`}
        footer={null}
        onCancel={() => setModalOpen(false)}
        width={720}
      >
        {designMap.isError ? (
          <Typography.Text type="danger">
            可行域求值失败：
            {designMap.error instanceof Error ? designMap.error.message : "未知错误"}
          </Typography.Text>
        ) : fdProduct !== null && fdProduct.mask !== null && fdSecond !== null ? (
          <>
            <FeasibilityHeatmap
              product={fdProduct}
              onPick={(valueA, valueB) => {
                onBackfill(fieldId, valueA);
                onBackfill(fdSecond, valueB);
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
    </div>
  );
}
