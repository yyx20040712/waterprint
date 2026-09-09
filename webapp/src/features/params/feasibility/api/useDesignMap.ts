/**
 * 可行域求值 hook（PD6 甲案同步端点——POST /api/calc/design-map）。
 *
 * 输入:  projectId + unitId + 轴声明（1D 行内/2D 模态共用）
 * 输出:  useMutation（DesignMapResponse——orval 生成面；错误经
 *        WaterprintApiError message 透出，422/400/404 同 apply 面先例）
 */
import { useMutation } from "@tanstack/react-query";

import { postDesignMapApiCalcDesignMapPost } from "../../../../shared/api/generated/calc/calc";
import type { DesignMapResponse } from "../../../../shared/api/generated/model";
import { WaterprintApiError } from "../../../../shared/api/http";

/** 轴声明载荷（field_id+可选 step/range——PD1 契约）。 */
export type DesignMapAxis = {
  field_id: string;
  step?: number;
  range?: { min: number; max: number };
};

export function useDesignMap(projectId: string, unitId: string) {
  return useMutation<DesignMapResponse, WaterprintApiError, { axes: DesignMapAxis[] }>({
    mutationFn: ({ axes }) =>
      postDesignMapApiCalcDesignMapPost({
        project_id: projectId,
        unit_id: unitId,
        axes: axes.map((axis) => ({
          field_id: axis.field_id,
          step: axis.step ?? null,
          range: axis.range ?? null,
        })),
      }),
  });
}
