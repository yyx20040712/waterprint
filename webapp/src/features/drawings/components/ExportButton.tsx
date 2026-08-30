/**
 * 导出发起：单元 Select+工况 Select+导出动作（409 stale 二选一）。
 *
 * 输入:  projectId+单元选项（design.nodes 键序）+工况选项（工况源投影）
 *        +onExported?（导出成功回调——B 批 D5 预览态接缝：drawingsPane
 *        setPreview 消费 ExportDxfResult{fileName,scene,sceneError}）
 * 输出:  导出动作（useExportDxf mutation：2xx→浏览器下载+onExported+
 *        列表刷新；409→Modal 二选一[仍导出旧结果 force 重发 vs 先重算]；
 *        404→「先提交计算」引导；501/网络错→message 分级呈现）
 *
 * 规格说明（FE9 批 6b 段七 D7/D8+B 批 D5 最小缝；骨架冻结规格「stale
 *   守门交互」落点）：
 *   - 错误分级（I-3 分级口径——网络错不挂误导引导）：仅
 *     WaterprintApiError.code==="ExportSourceNotFoundError"（404 无 done
 *     calc）附「先提交计算」引导；code==="StaleExportError"（409）→
 *     antd Modal.confirm 二选一（okText=仍导出旧结果[force=true 重发，
 *     产物与元数据将标注旧三元组]；cancelText=先重算[用户自行回
 *     params/solutions 面板重算——面板间导航挂账 UX 批]）；501 未就绪
 *     面 message.error 原文透传（诚实呈现归属）；
 *   - B 批 D5：mutate onSuccess 透传 onExported（undefined 时 no-op
 *     ——TanStack 判空等价「有则传」；组件其余零改）；
 *   - Select 不写占位文案属性（grep 门禁英文占位特征词规避——FE3 C3
 *     先例）；受控值=state??首选项兜底（服务端回显口径同族）；
 *   - 薄壳不测（useExportDxf 错误归一面由 shared/api/http.ts 同款实现
 *     保证；组件面挂账浏览器亲验）。
 */
import { useState } from "react";
import { Button, Modal, Select, Space, Typography, message } from "antd";

import { WaterprintApiError } from "../../../shared/api/http";
import { useExportDxf, type ExportDxfResult } from "../api/useExportDxf";

/** 404 引导（无 done calc——先提交计算）。 */
const NO_CALC_HINT = "——请先提交计算（POST /api/calc/run）完成后再导出图纸。";

/** 导出发起（单元+工况双选+stale 二选一交互+导出成功回调）。 */
export function ExportButton({
  projectId,
  units,
  conditions,
  onExported,
}: {
  projectId: string;
  units: string[];
  conditions: string[];
  onExported?: (result: ExportDxfResult) => void;
}) {
  const [unitId, setUnitId] = useState<string | null>(null);
  const [conditionKey, setConditionKey] = useState<string | null>(null);
  const [messageApi, contextHolder] = message.useMessage();
  const mutation = useExportDxf();

  const chosenUnit = unitId ?? units[0] ?? "";
  const chosenCondition = conditionKey ?? conditions[0] ?? "";
  const ready = chosenUnit !== "" && chosenCondition !== "";

  /** 提交（force 支线=409 二选一的「仍导出旧结果」）。 */
  const submit = (force: boolean) => {
    void mutation.mutate(
      {
        projectId,
        unitId: chosenUnit,
        conditionKey: chosenCondition,
        force,
      },
      {
        onSuccess: onExported, // B 批 D5：undefined 时 no-op——「有则传」等价
        onError: (error) => {
          if (!(error instanceof WaterprintApiError)) {
            messageApi.error(`导出失败：${error.message}`);
            return; // 网络错/未知面——不挂误导引导（I-3 分级口径）
          }
          if (error.code === "StaleExportError") {
            Modal.confirm({
              title: "结果集已过期（stale）",
              content: error.message,
              okText: "仍导出旧结果（force）",
              cancelText: "先重算",
              onOk: () => {
                submit(true); // force 重发——产物与元数据将标注旧三元组
              },
            });
            return;
          }
          if (error.code === "ExportSourceNotFoundError") {
            messageApi.error(`${error.message}${NO_CALC_HINT}`);
            return;
          }
          messageApi.error(error.message); // 501 未就绪等——原文诚实透传
        },
      },
    );
  };

  return (
    <Space wrap>
      {contextHolder}
      <Typography.Text type="secondary">单元：</Typography.Text>
      <Select
        style={{ minWidth: 180 }}
        value={chosenUnit === "" ? undefined : chosenUnit}
        options={units.map((id) => ({ value: id, label: id }))}
        onChange={(next) => setUnitId(next)}
        disabled={units.length === 0}
      />
      <Typography.Text type="secondary">工况：</Typography.Text>
      <Select
        style={{ minWidth: 120 }}
        value={chosenCondition === "" ? undefined : chosenCondition}
        options={conditions.map((key) => ({ value: key, label: key }))}
        onChange={(next) => setConditionKey(next)}
        disabled={conditions.length === 0}
      />
      <Button
        type="primary"
        loading={mutation.isPending}
        disabled={!ready}
        onClick={() => submit(false)}
      >
        导出图纸（DXF）
      </Button>
    </Space>
  );
}
