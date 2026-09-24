/**
 * 参数编辑态 slice：草稿/校验错误/脏标记（结构预留：随 M2 实装）。
 *
 * 输入:  表单编辑动作
 * 输出:  编辑态 store（脏标记驱动顶栏状态）
 *
 * 规格说明（骨架冻结，实装必须满足）：
 *   - 服务端校验结果不落地本 store（§17.2 界限）。
 *
 * R2-P1-3 实装（round2 批2 扩——2026-09-25 E2E-2 批）：只承载「未提交
 * 参数草稿计数」提示面（projectId → count），驱动画布工具条「保存」徽标
 * 与保存 toast 诚实化；草稿本体仍留 ParamForm 本地 useState（D7 单面板
 * 无跨组件态的既有边界不变——本 store 是提示面不是草稿面）。
 */
import { create } from "zustand";

type ParamsState = {
  /** projectId → 未提交参数草稿计数（0/缺键=无待提交）。 */
  draftHint: Record<string, number>;
  setDraftHint: (projectId: string, count: number) => void;
};

export const useParamsStore = create<ParamsState>((set) => ({
  draftHint: {},
  setDraftHint: (projectId, count) =>
    set((state) =>
      state.draftHint[projectId] === count
        ? state
        : { draftHint: { ...state.draftHint, [projectId]: count } },
    ),
}));
