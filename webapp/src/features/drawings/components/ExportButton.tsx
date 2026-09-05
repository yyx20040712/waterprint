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
 *   - M5 D3（SVRB D6③ 改写 2026-09-05）：单元 Select mode="multiple"（受控
 *     回显口径沿承——未交互=首单元预选兜底；交互后空数组=显式清空态，
 *     dxf 按钮 ready 闸收紧）；全选/清空用 antd 自带 maxTagCount=
 *     "responsive"/allowClear 形态（零自绘按钮）；「导出图纸（DXF）」：
 *     N=1 现状单发（含 409 Modal 二选一支线——零触碰）；N>1 服务端批量
 *     任务（useExportBatch 单 body 提交→任务态：进度 message「导出中
 *     i/N·kind·unit」原位更新+终态消息含「成功 N/失败 M·首错」/取消
 *     已产计数/失败原文；预览驻留不动——批量面无 blob 流；列表出新行
 *     由 hook 终态 invalidate 承载）；按钮文案多选 N>1 时不变；
 *   - M5 D5：第三按钮「导出全厂总图（DXF）」default 型（ready 闸=工况
 *     选定即可——对偶 ifc 的 conditionOnlyReady 口径；请求体 options
 *     unit_id 置空串=server bare POST 总图语义——_unit_id_of 空串归一
 *     None；成功入 onExported 预览=总图 DXF 线稿）；
 *   - Select 不写占位文案属性（grep 门禁英文占位特征词规避——FE3 C3
 *     先例）；受控值=state??首选项兜底（服务端回显口径同族）；
 *   - 薄壳不测（useExportArtifact 错误归一面由 shared/api/http.ts 同款
 *     实现保证；组件面挂账浏览器亲验——批量循环纯构造面归 batchExport.test）；
 *   - B5 D2/D3（2026-09-06 批量任务体验批）：IFC 按钮 loading 并入 batching
 *     （三按钮统一 in-flight 门）；进度 toast 内嵌 antd Progress 行内条
 *     （duration=0 持有+终态 destroy 销毁——同键原位更新形态不变）；挂
 *     BatchStatusLine 常驻回溯行（最近批量任务三态——hook lastOutcome 消费）。
 */
import { useEffect, useState } from "react";
import { Button, Modal, Progress, Select, Space, Typography, message } from "antd";

import { WaterprintApiError } from "../../../shared/api/http";
import {
  useExportArtifact,
  type ExportArtifactInput,
  type ExportArtifactResult,
} from "../api/useExportArtifact";
import { useExportBatch } from "../api/useExportBatch";
import { BatchStatusLine } from "./BatchStatusLine";

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
  const batchApi = useExportBatch("dxf"); // SVRB D6②：N>1 服务端批量任务面

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

  /** SVRB D6③：批量出图——N>1 服务端批量任务（单 body 提交+任务态进度/
   * 终态消息——files/failures 双清单诚实计数；N=1 单发路径零触碰）。 */
  const submitBatch = async () => {
    setBatching(true);
    try {
      const outcome = await batchApi.submitBatch({
        projectId,
        units: chosenUnits,
        conditionKey: chosenCondition,
      });
      if (outcome.state === "done") {
        const failed = outcome.failures.length;
        if (failed === 0) {
          messageApi.success(`批量出图完成：${outcome.files.length} 张`);
        } else {
          messageApi.warning(
            `批量出图完成：成功 ${outcome.files.length}/失败 ${failed}` +
              `——首错：${outcome.failures[0]?.error ?? "未知"}`,
          );
        }
      } else if (outcome.state === "cancelled") {
        messageApi.info(`批量出图已取消：已产 ${outcome.files.length} 张`);
      } else {
        messageApi.error(`批量出图失败：${outcome.error ?? "未知错误"}`);
      }
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      messageApi.error(`批量出图提交失败：${reason}`);
    } finally {
      messageApi.destroy(BATCH_PROGRESS_KEY); // B5 D3：终态销毁（duration=0 持有态收口）
      setBatching(false);
    }
  };

  // B5 R2（G1-07）：组件卸载收口常驻进度 toast——finally 不达路径（在途切页）
  // 下 antd message 独立于组件树驻留，卸载即销毁（同 key 无残留）。
  useEffect(() => () => messageApi.destroy(BATCH_PROGRESS_KEY), [messageApi]);

  // B5 D3：进度=message 文本+antd Progress 行内条（percent=Math.round(*100)
  // TaskPanel 先例；duration=0 持有——终态 destroy 销毁，同键原位更新不变）。
  useEffect(() => {
    if (!batching || batchApi.progress === null) {
      return;
    }
    const { done, total, stageText, percent } = batchApi.progress;
    messageApi.open({
      key: BATCH_PROGRESS_KEY,
      type: "info",
      duration: 0,
      content: (
        <>
          {`导出中 ${done}/${total}·${stageText}`}
          <Progress percent={Math.round(percent * 100)} size="small" />
        </>
      ),
    });
  }, [batchApi.progress, batching, messageApi]);

  /** dxf 按钮分发（D3/SVRB D6③）：N=1 现状单发（含 409 force 支线）；N>1 服务端批量任务。 */
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
        loading={ifcMutation.isPending || batching}
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
      {/* B5 D3：最近批量任务常驻回溯行（toast 瞬态+本行回溯——按钮旁挂载） */}
      <BatchStatusLine
        kind="dxf"
        progress={batchApi.progress}
        lastOutcome={batchApi.lastOutcome}
      />
    </Space>
  );
}
