/**
 * 保存冲突对话单源（F2 并发丢更新批 2026-11-20）：条件 PUT 收 409
 * ProjectConcurrentWriteError → antd Modal 三选（用我的覆盖/放弃我的
 * 改动/稍后处理）+基线提取/重拉调度纯函数。
 *
 * 输入:  保存链 onError 面 error（WaterprintApiError 判别=isSaveConflict）
 *        +deps{refetchLatest/onOverwrite/onDiscard}（消费面闭包自持）
 * 输出:  surfaceSaveConflict(error, deps)→boolean（true=冲突已接手呈现）
 *        +baseHashOf(raw)（读时基线提取）+confirmSaveConflict（antd 呈现）
 *
 * 规格说明（设计裁决：条件 PUT 乐观锁+FE 冲突对话，不做在场提示）：
 *   - 版本标识=项目文件既有 metadata.content_hash（design 态摘要，
 *     ADR-010 快照体系同源；GET 响应原生携带，PUT ?base_hash= 透传——
 *     零 schema 改动）；
 *   - 「用我的覆盖」=GET 重拉最新（错误体 detail 只内嵌 12 位展示前缀
 *     ——StaleExportError 同款风格，全值经重拉取）→以新基线重发保存体
 *     （保存体自最新 raw 重导出——非 design 面不回写陈旧；onOverwrite
 *     收 {raw, baseHash} 由消费面重建）；
 *   - 「放弃我的改动」=消费面清本地编辑态+重拉最新（onDiscard 闭包）；
 *   - 「稍后处理」=仅关对话，本地改动保留不保存（零动作）；
 *   - 重发再 409（窗口内又有他写）=对话再现（自然循环，禁静默）；
 *   - 文案沿错误分级体系：锁冲突 LOCK_HINT 同级用户面（不 force 不
 *     自动重试——显式选择是本批语义核心）；
 *   - shared/ui 允许 antd（第三方面）；纯逻辑（baseHashOf/surface
 *     调度）与呈现（confirmSaveConflict）同件——deps 注入面沿
 *     exportErrorSurface 先例可 spy 直测。
 */
import { Button, Modal } from "antd";

import { isSaveConflict } from "../api/http";

/** 对话标题（错误分级文案——与 LOCK_HINT 同级用户面）。 */
export const SAVE_CONFLICT_TITLE = "项目已在其他窗口/机器被修改";

/** 对话正文引导尾（三分支各自动作说明——服务器 detail 之后拼接）。 */
export const SAVE_CONFLICT_GUIDE =
  "请选择：用我的覆盖（以本次改动覆盖远端并保存）/ 放弃我的改动（重拉最新，本地改动丢弃）/ 稍后处理（保留本地改动暂不保存）。";

/** 重拉结果（onOverwrite 载荷——最新 raw 供消费面重建保存体）。 */
export type SaveConflictLatest = {
  raw: Record<string, unknown>;
  baseHash: string;
};

/**
 * 读时基线提取：raw.metadata.content_hash（F2 条件 PUT 载荷源）。
 *
 * 非串/空串/缺 metadata=返回 null——消费面不携基线（服务端无条件直写
 * 兼容面；正常 GET 产物恒非空）。
 */
export function baseHashOf(
  raw: Record<string, unknown> | undefined | null,
): string | null {
  if (raw === null || raw === undefined) {
    return null;
  }
  const metadata = raw["metadata"];
  if (
    typeof metadata === "object" &&
    metadata !== null &&
    !Array.isArray(metadata)
  ) {
    const hash = (metadata as Record<string, unknown>)["content_hash"];
    if (typeof hash === "string" && hash !== "") {
      return hash;
    }
  }
  return null;
}

/** 三选对话呈现配置（confirmSaveConflict 入参——deps 注入面可 spy）。 */
export type SaveConflictConfirmOptions = {
  content: string;
  onOverwrite: () => void;
  onDiscard: () => void;
};

/**
 * 三选冲突对话呈现（antd Modal.confirm+自定义 footer 三钮——渲染惰性
 * 函数形态闭包 modal 句柄；稍后处理=仅销毁对话零动作）。
 */
export function confirmSaveConflict(options: SaveConflictConfirmOptions): void {
  let handle: ReturnType<typeof Modal.confirm> | null = null;
  const close = (): void => {
    handle?.destroy();
  };
  handle = Modal.confirm({
    title: SAVE_CONFLICT_TITLE,
    content: `${options.content}\n${SAVE_CONFLICT_GUIDE}`,
    width: 560,
    footer: () => (
      <>
        <Button data-testid="save-conflict-later" onClick={close}>
          稍后处理
        </Button>
        <Button
          data-testid="save-conflict-discard"
          onClick={() => {
            close();
            options.onDiscard();
          }}
        >
          放弃我的改动
        </Button>
        <Button
          data-testid="save-conflict-overwrite"
          type="primary"
          danger
          onClick={() => {
            close();
            options.onOverwrite();
          }}
        >
          用我的覆盖
        </Button>
      </>
    ),
  });
}

/** 冲突调度 deps（消费面注入——refetchLatest 失败/无基线=放弃重发）。 */
export type SaveConflictDeps = {
  confirm: (options: SaveConflictConfirmOptions) => void;
  refetchLatest: () => Promise<SaveConflictLatest | null>;
  onOverwrite: (latest: SaveConflictLatest) => void;
  onDiscard: () => void;
};

/**
 * 保存冲突接手调度（保存链 onError 面单行接入）：isSaveConflict→三选
 * 对话（覆盖=重拉最新→onOverwrite({raw, baseHash})；放弃=onDiscard；
 * 稍后=零动作）→true；非冲突错误零动作返回 false（消费面走既有分级）。
 */
export function surfaceSaveConflict(
  error: unknown,
  deps: SaveConflictDeps,
): boolean {
  if (!isSaveConflict(error)) {
    return false;
  }
  const message = error instanceof Error ? error.message : String(error);
  deps.confirm({
    content: message,
    onOverwrite: () => {
      void deps.refetchLatest().then((latest) => {
        if (latest !== null) {
          deps.onOverwrite(latest);
        }
      });
    },
    onDiscard: () => {
      deps.onDiscard();
    },
  });
  return true;
}
