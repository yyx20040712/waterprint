/**
 * Ribbon 导出快访下拉（M4 批 D1 2026-10-07——ribbon.tsx 行预算 500 硬顶
 * 拆件：check_file_budgets 门禁教义〔AGENTS §2 无豁免清单——真有理由超标
 * →拆文件非申请豁免〕；LineSidebar 拆件先例同旨。行为面=ribbon D1 段
 * 整体迁出零语义变化：Dropdown.Button 主钮切槽保持+全厂总图 DXF 直发
 * +子面导航项）。
 *
 * 输入:  projectId（string|null——null=主钮+下拉整体禁用+title 指引）+
 *        onNavigate（App setTab 透传——主钮/导航项切槽 studio.drawings）
 * 输出:  Dropdown.Button（主钮 wp-ribbon-export 沿用零漂移——M1 探针 P6
 *        锚；菜单两项+data-testid 三新锚=wp-ribbon-export-menu〔popupRender
 *        容器〕/wp-ribbon-export-total-dxf/wp-ribbon-export-open-pane——
 *        门二探针消费面）
 *
 * 规格说明（M4 brief D1；inventory §C「Ribbon『导出』=快访；目录/预览/
 *   批量留 studio.drawings」终裁句）：
 *   - 工况源=useConditionOptions(projectId)（drawings API——ribbon→feature
 *     依赖方向沿 canvasStore 先例）缺省首项；无工况（空数组/取数失败）
 *     =该项禁用+title「先提交计算——工况源为最近完成计算的结果集」；
 *   - 直发=useExportArtifact("dxf") 本件实例（与子面 ExportButton 实例互
 *     不共享状态）；unit_id 置空串=server bare POST 总图语义（ExportButton
 *     第三钮现成口径——三钮中唯一无单元选择依赖者）；错误链经 lib/
 *     exportErrorSurface 共享（409 二选一保持不降级——静默弱化禁）；
 *   - 拆件自持 message.useMessage 实例（contextHolder 随件渲染——错误
 *     toast 挂载面独立，ribbon 主实例互不侵；antd message 合同等价）；
 *   - 测试面经 ribbon.test.tsx 集成覆盖（本件=Ribbon 内部段无独立件）。
 */
import { cloneElement, type ReactElement } from "react";
import { Dropdown, Modal, message } from "antd";
import { ExportOutlined } from "@ant-design/icons";

import { useConditionOptions } from "../features/drawings/api/useExportsQuery";
import { useExportArtifact } from "../features/drawings/api/useExportArtifact";
import { surfaceExportError } from "../features/drawings/lib/exportErrorSurface";
import type { TabTarget } from "./router";

/** 导出快访下拉（M4 D1——拆件自持工况源/直发 mutation/错误链呈现）。 */
export function RibbonExportMenu({
  projectId,
  onNavigate,
}: {
  projectId: string | null;
  onNavigate: (target: TabTarget) => void;
}) {
  const [messageApi, contextHolder] = message.useMessage();
  const conditionsQuery = useConditionOptions(projectId);
  const exportConditions = conditionsQuery.data ?? [];
  const exportDxf = useExportArtifact("dxf");

  /** 快访直发：全厂总图 DXF（unit_id 置空串=server bare POST 总图语义；
   *  工况源缺省首项；错误链经 surfaceExportError 共享〔409 二选一保持
   *  不降级〕）。 */
  const submitTotalDxf = (force: boolean) => {
    if (projectId === null || exportConditions.length === 0) {
      return; // 禁用态守卫（菜单项 disabled 面——不可达防御，不静默裸发）
    }
    exportDxf.mutate(
      { projectId, unitId: "", conditionKey: exportConditions[0] ?? "", force },
      {
        onError: (error) => {
          surfaceExportError(error, "dxf", {
            confirm: Modal.confirm,
            notifyError: messageApi.error,
            retry: () => submitTotalDxf(true),
          });
        },
      },
    );
  };

  return (
    <>
      {contextHolder}
      <Dropdown.Button
        trigger={["click"]}
        icon={<ExportOutlined />}
        disabled={projectId === null}
        onClick={() => onNavigate({ slot: "studio", subface: "drawings" })}
        popupRender={(menu) => <div data-testid="wp-ribbon-export-menu">{menu}</div>}
        menu={{
          items: [
            {
              key: "total-dxf",
              disabled: projectId === null || exportConditions.length === 0,
              title:
                projectId !== null && exportConditions.length === 0
                  ? "先提交计算——工况源为最近完成计算的结果集"
                  : undefined,
              label: (
                <span data-testid="wp-ribbon-export-total-dxf">导出全厂总图（DXF）</span>
              ),
            },
            {
              key: "open-pane",
              label: (
                <span data-testid="wp-ribbon-export-open-pane">单元图·模型·批量——在图纸子面</span>
              ),
            },
          ],
          onClick: ({ key }) => {
            if (key === "total-dxf") {
              submitTotalDxf(false); // 快访真发起（缺省首工况+空 unit_id 总图语义）
            } else if (key === "open-pane") {
              onNavigate({ slot: "studio", subface: "drawings" }); // 导航项=同主钮切槽
            }
          },
        }}
        buttonsRender={([left, right]) => [
          // 主钮 wp-ribbon-export 沿用不动（M1 探针 P6 锚零漂移）——title
          // 在有项目态逐字保持现状；null 态=禁用+指引（run 族口径对齐）
          cloneElement(left as ReactElement<Record<string, unknown>>, {
            "data-testid": "wp-ribbon-export",
            title:
              projectId === null
                ? "先在画布槽选择项目——图纸导出针对最近完成计算的结果集"
                : "图纸导出（目录/预览/批量在图纸子面）",
          }),
          right,
        ]}
      >
        导出
      </Dropdown.Button>
    </>
  );
}
