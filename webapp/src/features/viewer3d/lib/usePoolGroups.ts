/**
 * S11 池组计划/徽标数据通道（Scene 抽离件——500 行预算门；三呈裁
 * 2026-09-13）。
 *
 * 输入:  templateClaims（claimTemplateUnits 产物）+projectDetail
 *        （readProject 弱类型——override 源）+conditionKey（工况真源）
 * 输出:  { poolPlans, poolBadges }（builder 纯函数在 assemble/poolGroup
 *        ——本件只做 hooks 数据通道组合：catalog=Annotations 同款
 *        shared hook，react-query 同键缓存零额外请求）
 */
import { useMemo } from "react";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import {
  buildPoolBadges,
  buildPoolPlans,
  type PoolBadge,
  type PoolClaim,
  type PoolGroupPlan,
} from "../assemble/poolGroup";

export function usePoolGroups(
  claims: ReadonlyMap<string, PoolClaim>,
  projectDetail: unknown,
  conditionKey: string,
): {
  poolPlans: Map<string, PoolGroupPlan>;
  poolBadges: Record<string, PoolBadge>;
} {
  const catalogQuery = useListUnitsApiUnitsGet();
  const poolPlans = useMemo(
    () =>
      buildPoolPlans(
        claims,
        catalogQuery.data?.units,
        projectDetail,
        conditionKey,
      ),
    [claims, catalogQuery.data, projectDetail, conditionKey],
  );
  const poolBadges = useMemo(
    () => buildPoolBadges(claims, poolPlans, conditionKey),
    [claims, poolPlans, conditionKey],
  );
  return { poolPlans, poolBadges };
}
