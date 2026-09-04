/**
 * 导出发起：单元 Select（M5 D3 多选）+工况 Select+导出动作三按钮（409
 * stale 二选一）。
 *
 * 输入:  projectId+单元选项（design.nodes 键序——多选）+工况选项（工况源
 *        投影）+onExported?（导出成功回调——B 批 D5 预览态接缝：drawingsPane
 *        setPreview 消费 ExportArtifactResult{fileName,scene,sceneError}）
 * 输出:  导出动作（useExportArtifact mutation×2[dxf/ifc]：2xx→浏览器下载
 *        +onExported+列表刷新；409→Modal 二选一[仍导出旧结果 force 重发
 *        vs 先重算]；404→「先提交计算」引导；501/网络错→message 分级
 *        呈现）；单元/工况 Select 三按钮共享（SC1 D7）
 *
 * 规格说明（FE9 批 6b 段七 D7/D8+B 批 D5 最小缝；SC1 D7 第二按钮；M5
 *   D3/D5 多选批量+第三按钮 2026-09-04）：
 *   - 错误分级（I-3 分级口径——网络错不挂误导引导）：仅
 *     WaterprintApiError.code==="ExportSourceNotFoundError"（404 无 done
 *     calc）附「先提交计算」引导；code==="StaleExportError"（409）→
 *     antd Modal.confirm 二选一（okText=仍导出旧结果[force=true 重发，
 *     产物与元数据将标注旧三元组]；cancelText=先重算[用户自行回
 *     params/solutions 面板重算——面板间导航挂账 UX 批]）；501 未就绪
 *     面 message.error 原文透传（诚实呈现归属）；
 *   - B 批 D5：mutate onSuccess 透传 onExported（undefined 时 no-op
 *     ——TanStack 判空等价「有则传」；组件其余零改）；
 *   - SC1 D7：useExportArtifact 泛化 hook 双实例（dxf/ifc 各一——
 *     loading/错误面独立）；第二按钮「导出模型（IFC）」primary 沿既有
 *     形态（四字标签避插空格坑）；单元/工况 Select 按钮共享；ifc 恒单发
 *     零改（全厂模型无单元面——多选态不联动禁用，ifc 不消费单元选择）；
 *   - M5 D3：单元 Select mode="multiple"（受控回显口径沿承——未交互=
 *     首单元预选兜底；交互后空数组=显式清空态，dxf 按钮 ready 闸收紧）；
 *     全选/清空用 antd 自带 maxTagCount="responsive"/allowClear 形态
 *     （零自绘按钮）；「导出图纸（DXF）」语义升级：N=1 现状单发；N>1
 *     客户端顺序循环 N 个单产物请求（buildBatchExportRequests 纯构造
 *     ——每请求 options:{unit_id} 走即时 blob 面，零任务队列依赖；SSE/
 *     句柄消费零新增）；执行态=按钮 loading+message.info 同键原位更新
 *     「批量导出中 i/N」；任一失败即停（已成功计数进 error message——
 *     诚实呈现不静默跳过；批量面无 409 Modal 支线，stale 原文入中断
 *     消息）；全部成功=message.success「批量出图完成：N 张」（列表键
 *     失效由 mutation onSuccess 逐请求承载——批量=单产物请求序连发，
 *     与 N 次单发等价）；按钮文案多选 N>1 时不变；
 *   - M5 D5：第三按钮「导出全厂总图（DXF）」default 型（ready 闸=工况
 *     选定即可——对偶 ifc 的 conditionOnlyReady 口径；请求体 options
 *     unit_id 置空串=server bare POST 总图语义——_unit_id_of 空串归一
 *     None；成功入 onExported 预览=总图 DXF 线稿）；
 *   - Select 不写占位文案属性（grep 门禁英文占位特征词规避——FE3 C3
 *     先例）；受控值=state??首选项兜底（服务端回显口径同族）；
 *   - 薄壳不测（useExportArtifact 错误归一面由 shared/api/http.ts 同款
 *     实现保证；组件面挂账浏览器亲验——批量循环纯构造面归 batchExport.test）。
 */
import { useState } from "react";
import { Button, Modal, Select, Space, Typography, message } from "antd";

import { WaterprintApiError } from "../../../shared/api/http";
import {
  useExportArtifact,
  type ExportArtifactInput,
  type ExportArtifactResult,
} from "../api/useExportArtifact";
import { buildBatchExportRequests } from "../lib/batchExport";

/** 404 引导（无 done calc——先提交计算；R1-4：按按钮面 kind 化尾词）。 */
const NO_CALC_HINTS = {
  dxf: "——请先提交计算（POST /api/calc/run）完成后再导出图纸。",
  ifc: "——请先提交计算（POST /api/calc/run）完成后再导出模型。",
} as const;

/** 批量进度 message 键（同键重开=原位更新——antd message 合同）。 */
const BATCH_PROGRESS_KEY = "batch-export-progress";

/** 导出发起（单元多选+工况选+批量循环+总图按钮+stale 二选一交互+成功回调）。 */
export function ExportButton({
  projectId,
  units,
  conditions,
  onExported,
}: {
  projectId: string;
  units: string[];
  conditions: string[];
  onExported?: (result: ExportArtifactResult) => void;
}) {
  const [selectedUnits, setSelectedUnits] = useState<string[] | null>(null);
  const [conditionKey, setConditionKey] = useState<string | null>(null);
  const [batching, setBatching] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const dxfMutation = useExportArtifact("dxf");
  const ifcMutation = useExportArtifact("ifc");

  // 受控回显口径沿承：未交互=首单元预选（null 兜底）；交互后 []=显式清空。
  const chosenUnits = selectedUnits ?? units.slice(0, 1);
  const chosenCondition = conditionKey ?? conditions[0] ?? "";
  const ready = chosenUnits.length > 0 && chosenCondition !== "";
  // R1-3：ifc=全厂模型——ready 闸豁免单元选择（仅工况选定即可发起）；M5
  // 总图按钮同闸（对偶口径——单元选择零消费）。
  const conditionOnlyReady = chosenCondition !== "";

  /** 提交（kind 面 mutation 分发；force 支线=409 二选一的「仍导出旧结果」；
   * unitId 覆盖参=总图按钮空串面（bare POST 语义——缺省取首单元）。 */
  const submit = (kind: "dxf" | "ifc", force: boolean, unitId?: string) => {
    const mutation = kind === "dxf" ? dxfMutation : ifcMutation;
    const input: ExportArtifactInput = {
      projectId,
      unitId: unitId ?? chosenUnits[0] ?? "",
      conditionKey: chosenCondition,
      force,
    };
    void mutation.mutate(input, {
      // R1-4：预览态仅 dxf 面消费（ifc 无前端投影——成功后 DrawingPreview
      // 保持原态，不落「皆空引导」态；undefined 时 no-op 同 B 批 D5）。
      onSuccess: kind === "dxf" ? onExported : undefined,
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
              submit(kind, true, unitId); // force 重发（unitId 覆盖参透传——总图面保持空串）
            },
          });
          return;
        }
        if (error.code === "ExportSourceNotFoundError") {
          messageApi.error(`${error.message}${NO_CALC_HINTS[kind]}`);
          return;
        }
        messageApi.error(error.message); // 501 未就绪等——原文诚实透传
      },
    });
  };

  /** M5 D3：批量出图——N>1 客户端顺序循环单产物请求（任一失败即停）。 */
  const submitBatch = async () => {
    const requests = buildBatchExportRequests(chosenUnits, chosenCondition);
    setBatching(true);
    let done = 0;
    try {
      for (const [index, request] of requests.entries()) {
        messageApi.open({
          key: BATCH_PROGRESS_KEY,
          type: "info",
          content: `批量导出中 ${index + 1}/${requests.length}`,
        });
        const result = await dxfMutation.mutateAsync({
          projectId,
          unitId: request.options.unit_id,
          conditionKey: request.condition_key,
        });
        onExported?.(result); // 预览逐次翻新（末张驻留）
        done += 1;
      }
      messageApi.success(`批量出图完成：${requests.length} 张`);
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      messageApi.error(
        `批量导出中断：已完成 ${done}/${requests.length} 张——${reason}`,
      );
    } finally {
      setBatching(false);
    }
  };

  /** dxf 按钮分发（D3）：N=1 现状单发（含 409 force 支线）；N>1 批量循环。 */
  const submitDxf = () => {
    if (chosenUnits.length <= 1) {
      submit("dxf", false);
      return;
    }
    void submitBatch();
  };

  return (
    <Space wrap>
      {contextHolder}
      <Typography.Text type="secondary">单元：</Typography.Text>
      <Select
        mode="multiple"
        style={{ minWidth: 240 }}
        value={chosenUnits}
        options={units.map((id) => ({ value: id, label: id }))}
        onChange={(next) => setSelectedUnits(next)}
        disabled={units.length === 0}
        allowClear
        maxTagCount="responsive"
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
        loading={dxfMutation.isPending || batching}
        disabled={!ready}
        onClick={submitDxf}
      >
        导出图纸（DXF）
      </Button>
      <Button
        type="primary"
        loading={ifcMutation.isPending}
        disabled={!conditionOnlyReady}
        onClick={() => submit("ifc", false)}
      >
        导出模型（IFC）
      </Button>
      <Button
        type="default"
        loading={dxfMutation.isPending || batching}
        disabled={!conditionOnlyReady}
        onClick={() => submit("dxf", false, "")}
      >
        导出全厂总图（DXF）
      </Button>
    </Space>
  );
}
