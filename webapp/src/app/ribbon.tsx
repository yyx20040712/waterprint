/**
 * Ribbon 命令带（M1 批 2026-10-06——顶栏中段四命令定版〔用户实裁〕：
 * 提交计算〔唯一入口〕/校验/导出快访/三维快访；M4 批 2026-10-07 导出
 * 快访接内容——Dropdown 形：主钮切槽保持+总图 DXF 直发+子面导航项）。
 *
 * 输入:  projectId（string|null——null=主钮禁用+title 指引）+onNavigate
 *        （导航回调——App setTab：导出→studio.drawings/三维快访→viewer3d）
 *        +canvasStore 编辑会话 selector+useReadProject raw（保存/校验体
 *        基座）+paramsStore 草稿计数（F3-A1 闸）
 * 输出:  命令带容器（data-region="ribbon"）：①提交计算=Dropdown.Button
 *        主钮「全项目计算」（runCalc 链自 canvasEditToolbar 整体迁入：
 *        decideRunCalc 分派/dirty 先存后算 mutateAsync 链〔保存失败即止〕/
 *        参数草稿闸文案/GD-N-01 受检单元面/rawQuery loading 堵未就绪窗）
 *        +菜单「单元枚举…/联合枚举…」两 Modal（三入口收编一——mapping §A）；
 *        ②校验=编辑态草稿体校验（⑦甲警告放行；报告=Popover 自持）；
 *        ③导出=RibbonExportMenu 拆件（M4 D1——Dropdown 形：主钮〔wp-
 *        ribbon-export 沿用〕点击=切槽 studio.drawings〔现状行为+title
 *        逐字保持〕+菜单两项：总图 DXF 真发起/子面导航项；工况源与直发
 *        mutation/错误链归拆件自持——ribbon.tsx 行预算 500 硬顶拆出，
 *        详见 ribbonExportMenu.tsx 头注）；projectId
 *        null=主钮+下拉整体禁用）；④三维快访=切槽 viewer3d
 *
 * 规格说明（mapping-2b4 §D 终核+brief D5+M4 brief D1；两裁量位〔编辑开关/
 *   保存〕留画布槽内工具条——canvasEditToolbar 解构后两态闭环维持，M1
 *   零增量）：
 *   - 提交计算唯一入口：主钮全项目计算（不依赖选中+dirty——F4 残余根治
 *     承袭）；枚举两轨提交面归菜单 Modal（进度呈现面席位接管/结果面 M6
 *     ——过渡态诚实反馈 message task_id）；
 *   - 单元枚举 Modal=EnumerateBar 原件承载（props 接线复刻 solutionsPane
 *     L162/L323-334 面：useProjectUnits+useConstraints+restoreConstraintKeys
 *     恢复+勾选即 PUT 持久〔mergeGroupSelection 合成全集+乐观回滚〕+
 *     useRunEnumeration onSuccess=writeEnumParam+writeTaskParam+TASK_EVENT
 *     派发+关 Modal）；projectId null=Modal 内提示不渲染表单；
 *   - 联合枚举 Modal=JointSubmitForm（jointSolutions.tsx 裁剪件——结果
 *     面段 M6 study 接管，本批提交条段）；
 *   - 校验：非编辑态/raw 未就绪=禁用+title 说明；草稿变更清陈旧报告
 *     （useEffect 沿现状）；报告=钮下 Popover Alert 迁移形态；
 *   - 纯函数 decideRunCalc/paramDraftBlockMessage 自 canvasEditToolbar 迁
 *     本文件导出（canvasEditToolbar.test 随迁 import——断言零改零弱化）；
 *   - M4 D1 导出快访接内容（inventory §C「Ribbon『导出』=快访；目录/
 *     预览/批量留 studio.drawings」终裁句）：实装面拆件 ribbonExportMenu
 *     （check_file_budgets 500 行硬顶——本文件 D1 段整体迁出零语义变化；
 *     总图直发=三钮中唯一无单元选择依赖者〔对偶 ifc 的 conditionOnlyReady
 *     口径〕，工况源=useConditionOptions 缺省首项，无工况=该项禁用+title
 *     引导；409 二选一经 surfaceExportError 共享链保持不降级；演示动线③
 *     单元图/批量态留子面——菜单项导航不复制多选面）。
 */
import { cloneElement, useEffect, useState, type ReactElement } from "react";
import { Alert, Button, Dropdown, Modal, Popover, Typography, message } from "antd";
import { AuditOutlined, EyeOutlined } from "@ant-design/icons";
import { useQueryClient } from "@tanstack/react-query";

import { EnumerateBar } from "./enumerateBar";
import { JointSubmitForm } from "./jointSolutions";
import { draftProjectRaw } from "../features/canvas/lib/designWriter";
import {
  useCanvasStore,
  useDirty,
  useDraft,
  useEditing,
} from "../features/canvas/store/canvasStore";
import { useParamsStore } from "../features/params/store/paramsStore";
import { useConstraints } from "../features/params/api/useConstraints";
import {
  filterSelectable,
  mergeGroupSelection,
  restoreConstraintKeys,
  toPayloadItems,
} from "../features/params/lib/constraintPicker";
import { withConstraintChoices } from "../features/params/lib/designParams";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { RibbonExportMenu } from "./ribbonExportMenu";
import {
  useRunCalculationApiCalcRunPost,
  useRunEnumerationApiCalcEnumeratePost,
} from "../shared/api/generated/calc/calc";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
  useValidateProjectApiProjectsProjectIdValidatePost,
} from "../shared/api/generated/projects/projects";
import type { WaterprintApiError } from "../shared/api/http";
import { isLockConflict, LOCK_HINT } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import type { TabTarget } from "./router";
import { writeEnumParam, writeTaskParam } from "./solutionsUrlState";

/** 校验结果态（⑦甲——null=未校验；valid=true 成功态文案行）。 */
type ValidateReport = { valid: boolean; errors: string[] } | null;

/** raw design.checked_units 宽容读取（constraintPicker.rawCheckedUnits 同口径）。 */
function rawCheckedUnits(raw: unknown): string[] {
  if (typeof raw !== "object" || raw === null) {
    return [];
  }
  const design = (raw as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return [];
  }
  const checked = (design as Record<string, unknown>)["checked_units"];
  return Array.isArray(checked) ? checked.filter((id): id is string => typeof id === "string") : [];
}

/** P0-B 决策面（fix-plan 批2 纯函数——vitest 直测）：提交计算动作分派。
 *  dirty 编辑态：body 未就绪=阻断并提示（保存需要体）；就绪=先存后算。
 *  只读态：draft===null ⇒ body 恒 null 属正常态，直接算（呈裁⑥ 常驻
 *  提交计算语义——旧实现把 body 守卫放在最前，只读态被静默吞掉）。
 *  F3/A-1 扩：参数草稿计数非零=block-param-draft（先于存/算——工具条
 *  保存不携带参数草稿，直算=陈旧参数裸失败；禁自动 apply 红线）。 */
export type RunCalcDecision = "block-param-draft" | "save-run" | "run" | "block-unready";
export function decideRunCalc(
  dirty: boolean,
  body: unknown,
  paramDraftCount = 0,
): RunCalcDecision {
  if (paramDraftCount > 0) {
    return "block-param-draft";
  }
  if (dirty) {
    return body === null ? "block-unready" : "save-run";
  }
  return "run";
}

/** F3/A-1 拦截文案（纯函数——vitest 锁三要素：计数/『提交重算』正门/
 *  「保存不携带」因果；禁含糊指路）。 */
export function paramDraftBlockMessage(count: number): string {
  return `参数面板有 ${count} 项未提交——请先在参数面板点『提交重算』（工具条保存不携带参数草稿）`;
}

/** 单元枚举 Modal 体（EnumerateBar 承载——接线复刻 solutionsPane 提交面；
 *  Modal 开态才挂载=取数面随开随取；key=projectId 切项目重挂全复位）。 */
function EnumerateModalBody({
  projectId,
  onDone,
}: {
  projectId: string;
  onDone: () => void;
}) {
  const [unitId, setUnitId] = useState<string | null>(null);
  const [constraintKeys, setConstraintKeys] = useState<string[]>([]);
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const unitsQuery = useProjectUnits(projectId);
  const constraintsQuery = useConstraints();
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId);

  // CP2 D3 恢复：raw 到达（装载/切项目键变）→恢复勾选全集
  useEffect(() => {
    const raw = rawQuery.data;
    if (raw !== undefined) {
      setConstraintKeys(restoreConstraintKeys(raw));
    }
  }, [rawQuery.data]);

  const saveConstraints = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>({
    mutation: {
      onSuccess: (_outcome, variables) => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${variables.projectId}`],
        });
      },
    },
  });

  const enumerate = useRunEnumerationApiCalcEnumeratePost<WaterprintApiError>({
    mutation: {
      onSuccess: (response) => {
        // ENG5 D6：枚举轨写 enum 键+task 键同步回写+TASK_EVENT 派发
        // （URL 回写驱动已挂载面——solutionsPane onSuccess 同款）
        writeEnumParam(response.task_id);
        writeTaskParam(response.task_id);
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: response.task_id }),
        );
        messageApi.success(
          `枚举任务已提交：${response.task_id}（进度见右侧 AI 席位「任务」分页——结果呈现随 M6 批）`,
        );
        onDone();
      },
    },
  });

  const selectableConstraints = filterSelectable(constraintsQuery.data ?? [], unitId);
  /** CP2 D4+R-1：勾选=本组变更合成全集（跨单元键保留）→乐观 set+PUT。 */
  const handleConstraintChange = (nextKeys: string[]) => {
    const raw = rawQuery.data;
    const prevKeys = constraintKeys;
    const groupKeys = selectableConstraints.map((entry) => entry.key);
    const mergedKeys = mergeGroupSelection(constraintKeys, groupKeys, nextKeys);
    setConstraintKeys(mergedKeys);
    if (raw === undefined) {
      messageApi.warning("项目数据未就绪，勾选暂未保存");
      return;
    }
    saveConstraints.mutate(
      { projectId, data: withConstraintChoices(raw, mergedKeys) },
      {
        onError: (error) => {
          setConstraintKeys(prevKeys);
          messageApi.error(
            isLockConflict(error)
              ? LOCK_HINT
              : `约束勾选保存失败：${error instanceof Error ? error.message : "未知错误"}`,
          );
        },
      },
    );
  };

  return (
    <div>
      {contextHolder}
      <EnumerateBar
        units={unitsQuery.data ?? []}
        unitId={unitId}
        onUnitChange={setUnitId}
        constraintEntries={selectableConstraints}
        constraintKeys={constraintKeys}
        onConstraintChange={handleConstraintChange}
        enumeratePending={enumerate.isPending}
        onEnumerate={() => {
          if (unitId === null) {
            return;
          }
          // R-3：本组投影空回 null（禁发 {constraints:[]}）
          const items = toPayloadItems(selectableConstraints, constraintKeys);
          enumerate.mutate({
            data: {
              project_id: projectId,
              unit_ids: [unitId],
              options: items.length === 0 ? null : { constraints: items },
            },
          });
        }}
        enumerateError={
          enumerate.isError
            ? enumerate.error instanceof Error
              ? enumerate.error.message
              : "未知错误"
            : null
        }
        unitsLoading={unitsQuery.isLoading}
        unitsError={
          unitsQuery.isError
            ? unitsQuery.error instanceof Error
              ? unitsQuery.error.message
              : "未知错误"
            : null
        }
      />
    </div>
  );
}

export function Ribbon({
  projectId,
  onNavigate,
}: {
  projectId: string | null;
  onNavigate: (target: TabTarget) => void;
}) {
  const editing = useEditing(projectId);
  const dirty = useDirty(projectId);
  const draft = useDraft(projectId);
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null },
  });
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [report, setReport] = useState<ValidateReport>(null);
  const [enumOpen, setEnumOpen] = useState(false);
  const [jointOpen, setJointOpen] = useState(false);
  const store = useCanvasStore;
  const paramDraftCount = useParamsStore((s) =>
    projectId !== null ? s.draftHint[projectId] ?? 0 : 0,
  );

  // 草稿变更即清陈旧校验报告（报告只对当次草稿版本有效——沿现状）
  useEffect(() => {
    setReport(null);
  }, [draft]);

  const validate = useValidateProjectApiProjectsProjectIdValidatePost();
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();
  const run = useRunCalculationApiCalcRunPost<WaterprintApiError>({
    mutation: {
      onSuccess: (outcome) => {
        // AssumptionsPanel D4 同构：?task= 回写+TASK_EVENT（联动）
        writeTaskParam(outcome.task_id);
        window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: outcome.task_id }));
      },
    },
  });

  /** 保存/校验体：时点最新 raw+草稿四面（红线⑤ 双守口径）。 */
  const body =
    draft !== null && rawQuery.data !== undefined
      ? draftProjectRaw(rawQuery.data, draft)
      : null;

  const runCalc = async () => {
    const decision = decideRunCalc(dirty, body, paramDraftCount);
    if (decision === "block-param-draft") {
      // F3/A-1：参数草稿闸——不 save 不 mutate（禁自动 apply），只指路正门
      messageApi.warning(paramDraftBlockMessage(paramDraftCount));
      return;
    }
    if (decision === "block-unready") {
      messageApi.error("项目数据未就绪——稍候重试");
      return;
    }
    try {
      if (decision === "save-run") {
        if (body === null) {
          return; // 类型收窄守卫（决策与载荷同帧求值，理论不可达）
        }
        await save.mutateAsync({ projectId: projectId as string, data: body });
        store.getState().markSaved();
        void queryClient.invalidateQueries({
          queryKey: [`/api/projects/${projectId}`],
        });
        messageApi.success("图面已保存——正在提交计算");
      }
      run.mutate(
        {
          data: {
            project_id: projectId as string,
            // GD-N-01：编辑态恒用草稿受检面（空清单不回退 raw）；只读态读 raw
            ...(draft !== null
              ? draft.checkedUnits.length > 0
                ? { conditions: draft.checkedUnits }
                : {}
              : rawQuery.data !== undefined && rawCheckedUnits(rawQuery.data).length > 0
                ? { conditions: rawCheckedUnits(rawQuery.data) }
                : {}),
          },
        },
        {
          onError: (error: WaterprintApiError) => {
            messageApi.error(error instanceof Error ? error.message : "提交计算失败");
          },
        },
      );
    } catch {
      // GD-N-02：保存失败显式呈报（mutateAsync 无 per-call onError）
      messageApi.error("保存失败——未提交计算（请检查网络/锁冲突后重试）");
    }
  };

  return (
    <div
      data-region="ribbon"
      // R13（裁决 F-7）：容器行内换行样式删除——换行模式下 Dropdown.Button
      // 内部 ant-space-compact 独占整行（实测 411px 全宽）把校验/导出/
      // 三维快访挤到第二行（顶栏 28+8+28=64px 超窗 16px）；命令带恒单行
      // （nowrap 语义——48px 顶栏不变式优先于窄视口换行；窄视口压缩面=
      // 可接受边缘，2B6 视觉验收复核）
      style={{ display: "flex", alignItems: "center", gap: 8 }}
    >
      {contextHolder}
      <Dropdown.Button
        trigger={["click"]}
        loading={run.isPending || rawQuery.isLoading}
        onClick={() => void runCalc()}
        menu={{
          items: [
            { key: "unit-enum", label: "单元枚举…" },
            { key: "joint-enum", label: "联合枚举…" },
          ],
          onClick: ({ key }) => {
            if (key === "unit-enum") {
              setEnumOpen(true);
            } else if (key === "joint-enum") {
              setJointOpen(true);
            }
          },
        }}
        buttonsRender={([left, right]) => [
          // 主钮 null 禁用经 clone 限定（Dropdown.Button 整组 disabled 会
          // 连菜单触发钮禁用——枚举入口 null 态须可达〔Modal 内提示面〕）
          cloneElement(left as ReactElement<Record<string, unknown>>, {
            "data-testid": "wp-ribbon-run",
            disabled: projectId === null,
            title: projectId === null ? "先在画布槽选择项目" : "全项目计算（编辑会话有修改时先保存后计算）",
          }),
          right,
        ]}
      >
        全项目计算
      </Dropdown.Button>
      <Popover
        open={report !== null}
        onOpenChange={() => setReport(null)}
        trigger="click"
        content={
          report === null ? null : (
            <Alert
              style={{ maxWidth: 420 }}
              type={report.valid ? "success" : "warning"}
              showIcon
              message={report.valid ? "结构校验通过" : "结构校验发现以下问题（不阻断保存——中间态合法）"}
              description={
                report.errors.length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {report.errors.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : undefined
              }
            />
          )
        }
      >
        <Button
          data-testid="wp-ribbon-validate"
          icon={<AuditOutlined />}
          disabled={!editing || rawQuery.data === undefined || draft === null}
          title={
            !editing
              ? "校验=编辑态草稿体结构检查——先在画布槽进入编辑"
              : rawQuery.data === undefined || draft === null
                ? "项目数据未就绪"
                : "校验当前草稿体（警告不阻断保存）"
          }
          loading={validate.isPending}
          onClick={() => {
            if (body === null) {
              return;
            }
            validate.mutate(
              { projectId: projectId as string, data: body },
              {
                onSuccess: (response) => {
                  setReport({ valid: response.valid, errors: response.errors });
                },
                onError: () => {
                  setReport({ valid: false, errors: ["校验请求失败（服务不可达或载荷非法）"] });
                },
              },
            );
          }}
        >
          校验
        </Button>
      </Popover>
      {/* M4 D1：导出快访下拉（拆件 ribbonExportMenu——行预算 500 硬顶，
          行为面=主钮切槽保持+总图直发+子面导航项，详见该件头注） */}
      <RibbonExportMenu projectId={projectId} onNavigate={onNavigate} />
      <Button
        data-testid="wp-ribbon-viewer3d"
        icon={<EyeOutlined />}
        title="三维视图快访（切槽 viewer3d）"
        onClick={() => onNavigate({ slot: "viewer3d" })}
      >
        三维快访
      </Button>

      {/* 三入口收编一：枚举两轨 Modal（mapping §A——提交面归 Ribbon 唯一入口下） */}
      <Modal
        open={enumOpen}
        title="单元枚举"
        footer={null}
        width={760}
        onCancel={() => setEnumOpen(false)}
      >
        {enumOpen && projectId !== null ? (
          <EnumerateModalBody key={projectId} projectId={projectId} onDone={() => setEnumOpen(false)} />
        ) : (
          <Typography.Paragraph type="secondary">
            尚未选择项目——请先在画布槽选择项目
          </Typography.Paragraph>
        )}
      </Modal>
      <Modal
        open={jointOpen}
        title="联合枚举"
        footer={null}
        width={760}
        onCancel={() => setJointOpen(false)}
      >
        {jointOpen && projectId !== null ? (
          <JointSubmitForm key={projectId} projectId={projectId} onSubmitted={() => setJointOpen(false)} />
        ) : (
          <Typography.Paragraph type="secondary">
            尚未选择项目——请先在画布槽选择项目
          </Typography.Paragraph>
        )}
      </Modal>
    </div>
  );
}
