/**
 * 建项 Modal（P0-1——F1 建项入口+F4-文案面收口）：空白新建/导入 JSON 两态。
 *
 * 输入:  open/onClose 受控态+onCreated(projectId) 回调（建项成功面——
 *        写方 pane 回写 ?project= 选中）
 * 输出:  Modal（Radio 模式切换+名称 Input[空白必填/导入可选]+导入文件
 *        选择+创建钮；POST /api/projects {name, project?}）
 *
 * 规格说明（op-chain-fix-plan §一——2026-09-11 用户裁定批）：
 *   - 两态：空白新建（名称必填→空项目创建——core 默认参数兜底，加单元
 *     面归 P0-3）/导入 JSON（文件选择→parseProjectJson→POST {project}
 *     ——手册导入路径产品化，r2 R1 配套项：单批走通「导入→画布渲染→
 *     改参→计算」全链）；
 *   - 名称：空白=必填（normalizeProjectName 校验）；导入=可选覆盖（留空
 *     保留导入文件自带名——server create_project 语义）；不另发 PUT 回写
 *     （创建载荷直带名称，开工体检实核①）；
 *   - 结构校验归 server parse_project 422（FE 不做第二业务源——红线②：
 *     FE 只做 JSON.parse 合法性+顶层对象判别，schema/版本门/深度闸全在
 *     服务面）；错误消息用户语透传（InvalidProjectPayloadError detail）；
 *   - 成功面：message.success+onCreated(project_id)+onClose——写方 pane
 *     经 useProjectId setter 回写 ?project= 并派发 PROJECT_EVENT（六 pane
 *     订阅联动，S3）；项目列表经 invalidateQueries 失效重拉；
 *   - app 层薄壳消费本件与 projectCreate 纯函数（canvasPane/viewer3dPane
 *     两空态同件共用——「两处内联同构挂账 UX 批」的公共抽取在 P0 批
 *     就此收口）；
 *   - 文件读取=File.text()（现代 API——jsdom 零依赖红线维持，SSR 测试
 *     面不触达文件 IO 分支）。
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Input, Modal, Radio, Typography, Upload, message } from "antd";

import {
  getListProjectsApiProjectsGetQueryKey,
  useCreateProjectApiProjectsPost,
} from "../shared/api/generated/projects/projects";
import { WaterprintApiError } from "../shared/api/http";
import {
  PROJECT_NAME_MAX,
  normalizeProjectName,
  parseProjectJson,
} from "./projectCreate";

/** 创建模式（两态——空白新建/导入 JSON）。 */
type CreateMode = "blank" | "import";

export function CreateProjectModal({
  open,
  onClose,
  onCreated,
}: {
  /** 开态（写方 pane 持有）。 */
  open: boolean;
  /** 关闭回调（取消/成功后收口统一经此）。 */
  onClose: () => void;
  /** 建项成功回调（projectId=新项目 id——写方回写 ?project=）。 */
  onCreated: (projectId: string) => void;
}) {
  const [mode, setMode] = useState<CreateMode>("blank");
  const [name, setName] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileText, setFileText] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();

  const nameCheck = normalizeProjectName(name);
  const parsed = fileText === null ? null : parseProjectJson(fileText);
  // 创建钮门：空白=名称必填；导入=文件已选且解析通过（名称可选）
  const canSubmit =
    mode === "blank"
      ? nameCheck.valid
      : parsed !== null && parsed.ok;

  const create = useCreateProjectApiProjectsPost<WaterprintApiError>({
    mutation: {
      onSuccess: (outcome) => {
        void queryClient.invalidateQueries({
          queryKey: getListProjectsApiProjectsGetQueryKey(),
        });
        messageApi.success(
          mode === "blank"
            ? `项目「${nameCheck.name}」已创建`
            : `项目已导入${nameCheck.valid ? `（名称覆盖为「${nameCheck.name}」）` : ""}`,
        );
        resetAndClose();
        onCreated(outcome.project_id);
      },
      onError: (error) => {
        messageApi.error(
          `创建失败：${error instanceof Error ? error.message : "未知错误"}`,
        );
      },
    },
  });

  /** 重置表单态并关弹窗（成功/取消统一面——二次打开零残留）。 */
  function resetAndClose() {
    setMode("blank");
    setName("");
    setFileName(null);
    setFileText(null);
    setFileError(null);
    create.reset();
    onClose();
  }

  return (
    <Modal
      title="新建项目"
      open={open}
      onCancel={resetAndClose}
      footer={null}
      destroyOnHidden
    >
      {contextHolder}
      <Radio.Group
        value={mode}
        onChange={(event) => setMode(event.target.value as CreateMode)}
        style={{ marginBottom: 12 }}
      >
        <Radio.Button value="blank">空白新建</Radio.Button>
        <Radio.Button value="import">导入 JSON</Radio.Button>
      </Radio.Group>
      <div style={{ marginBottom: 12 }}>
        <Typography.Text type="secondary">
          {mode === "blank"
            ? "创建空项目（单元参数用默认值——在画布中添加单元与连线的编辑面建设中）"
            : "选择已导出的项目 JSON 文件导入（结构校验在服务端完成）"}
        </Typography.Text>
      </div>
      <div style={{ marginBottom: 4 }}>
        <Typography.Text style={{ fontSize: 12 }}>
          {mode === "blank"
            ? "项目名称（必填）"
            : "项目名称（可选——留空保留导入文件内名称）"}
        </Typography.Text>
      </div>
      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        maxLength={PROJECT_NAME_MAX}
        style={{ marginBottom: 12 }}
        status={
          mode === "blank" && name.length > 0 && !nameCheck.valid
            ? "error"
            : undefined
        }
      />
      {mode === "import" ? (
        <div style={{ marginBottom: 12 }}>
          <Upload
            accept=".json,application/json"
            maxCount={1}
            beforeUpload={async (file) => {
              setFileName(file.name);
              setFileError(null);
              try {
                setFileText(await file.text());
              } catch {
                setFileText(null);
                setFileError("文件读取失败——请重试或换用其他文件");
              }
              return false; // 阻止自动上传（读取面手工接管）
            }}
            onRemove={() => {
              setFileName(null);
              setFileText(null);
              setFileError(null);
            }}
            fileList={
              fileName === null
                ? []
                : [
                    {
                      uid: "import-file",
                      name: fileName,
                      status: parsed?.ok ? "done" : "error",
                    },
                  ]
            }
          >
            <Button>选择项目 JSON 文件</Button>
          </Upload>
          {fileError ? (
            <Typography.Text type="danger">{fileError}</Typography.Text>
          ) : parsed !== null && !parsed.ok ? (
            <Typography.Text type="danger">{parsed.error}</Typography.Text>
          ) : parsed?.ok ? (
            <Typography.Text type="secondary">
              文件解析通过：导入后名称与单元以文件内容为准
            </Typography.Text>
          ) : null}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <Button onClick={resetAndClose}>取消</Button>
        <Button
          type="primary"
          loading={create.isPending}
          disabled={!canSubmit}
          onClick={() => {
            if (!canSubmit) {
              return;
            }
            create.mutate({
              data: {
                name: nameCheck.valid ? nameCheck.name : undefined,
                project:
                  mode === "import" && parsed?.ok ? parsed.project : undefined,
              },
            });
          }}
        >
          创建项目
        </Button>
      </div>
    </Modal>
  );
}
