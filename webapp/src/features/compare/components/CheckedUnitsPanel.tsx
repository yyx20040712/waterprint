/**
 * CheckedUnitsPanel（工况校核集合面板——P2 第三批 ADR-018 D4；工况面
 * UX 反馈批件 2 归位 comparePane 双页[原 App Sider 挂点拆除——ADR-018
 * D4 附勘正]；件 1 勾选选项 unit_id→中文名接线）。
 *
 * 输入:  projectId+useReadProject 原始 GET 体（勾选恢复投影/PUT 基座）
 *        +catalog name_zh（勾选选项中文名——orval listUnits select）
 * 输出:  Checkbox.Group 勾选面板（标题行「受检 k 单元 → 计算工况 2+k 档」
 *        代价提示+勾选即 PUT——CP2 约束勾选持久化样板同构）
 *
 * 规格说明（P2 第三批 ADR-018 D4；工况面 UX 反馈批 2026-09-12）：
 *   - 集合语义呈现：标题行直出运行代价（k 受检=2+k 工况——ADR-007
 *      线性口径；散落单元属性无法呈现全局代价=独立面板设计因）；
 *   - 归位（件 2——用户反馈「工况校核应该放在工况对比面板中」）：
 *      App Sider 挂点拆除，组件随 checkedUnits lib 迁 features/compare
 *      （对比面板双页右页——ParamTabs Segmented 制式同款）；
 *   - 勾选选项中文化（件 1）：label=unit_id→name_zh（catalog 真源），
 *      title 悬浮显原 unit_id（追溯面对照接口文档——用户裁定口径）；
 *   - 保存链路=CP2 样板复刻：乐观 set+整项目 PUT（withCheckedUnits
 *      结构化替换）→onSuccess invalidate read 键（digest 变→既有 stale
 *      机制自动激活：横幅/导出 409 零新增）→onError 回滚+分级 toast
 *      （锁冲突 LOCK_HINT/ProjectNotFound·InvalidPayload 固定摘要/其余
 *      raw 透出——UF-59 2A4 批 domainGate 码表门控）；
 *   - 恢复投影∩可勾全集（幽灵勾选过滤——designWriter 级联清理为服务端
 *      第一道，本面第二道呈现防线）。
 */
import { useState } from "react";
import { Checkbox, Typography, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import {
  checkableUnits,
  restoreCheckedKeys,
  withCheckedUnits,
} from "../lib/checkedUnits";
import {
  useReadProjectApiProjectsProjectIdGet,
  useSaveProjectApiProjectsProjectIdPut,
} from "../../../shared/api/generated/projects/projects";
import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { unitNameIndex } from "../../../shared/conditionLabels";
import { LOCK_HINT, WaterprintApiError, isLockConflict } from "../../../shared/api/http";
import { domainGate } from "../../../shared/api/sourceGate";

export function CheckedUnitsPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId);
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();
  // 件 1：勾选选项中文名（catalog name_zh 真源——模块级 select 稳定引用）
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};

  const raw = rawQuery.data;
  const checkable = raw !== undefined ? checkableUnits(raw) : [];
  const restored = raw !== undefined ? restoreCheckedKeys(raw) : [];
  const [checked, setChecked] = useState<string[] | null>(null);
  const checkedKeys = checked ?? restored;

  /** D4+R-1（CP2 同款）：勾选=乐观 set+PUT 全量替换（onError 回滚）。 */
  const handleChange = (nextKeys: string[]) => {
    if (raw === undefined) {
      messageApi.warning("项目数据未就绪，勾选暂未保存");
      return;
    }
    const prevKeys = checkedKeys;
    setChecked(nextKeys);
    save.mutate(
      { projectId, data: withCheckedUnits(raw, nextKeys) as never },
      {
        onSuccess: () => {
          void queryClient.invalidateQueries({
            queryKey: [`/api/projects/${projectId}`],
          });
          messageApi.success(
            `已保存：受检 ${nextKeys.length} 单元 → 计算工况 ${2 + nextKeys.length} 档`,
          );
        },
        onError: (error) => {
          setChecked(prevKeys);
          // UF-59（2A4 domainGate 码表门控）：锁冲突既有 LOCK_HINT 零改→
          // ProjectNotFound/InvalidPayload 两码固定摘要（码表依据=server
          // projects.py PUT 链路领域码族——toast 闪现面禁 API 句式）；
          // 网络错/其他错保 raw 透出（I-3 分级口径）
          const notFound = domainGate(
            error,
            "ProjectNotFoundError",
            "保存失败：项目不存在或已被删除——请刷新页面核对",
          );
          const invalidPayload = domainGate(
            error,
            "InvalidProjectPayloadError",
            "保存失败：项目数据校验未通过——项目可能已被他处修改，请刷新后重试",
          );
          messageApi.error(
            isLockConflict(error)
              ? LOCK_HINT
              : notFound.domain
                ? notFound.text
                : invalidPayload.domain
                  ? invalidPayload.text
                  : `工况校核保存失败：${error instanceof Error ? error.message : "未知错误"}`,
          );
        },
      },
    );
  };

  return (
    <div
      data-testid="wp-checked-units-panel"
      style={{
        padding: "8px 12px",
        borderTop: "1px solid var(--wp-border-2)",
      }}
    >
      {contextHolder}
      <Typography.Text strong style={{ fontSize: 12 }}>
        工况校核
      </Typography.Text>
      <Typography.Paragraph
        type="secondary"
        style={{ fontSize: 12, marginBottom: 4 }}
      >
        受检 {checkedKeys.length} 单元 → 计算工况 {2 + checkedKeys.length} 档
        （design/avg 基线+每受检单元一条 n-1 池检修敏感性——ADR-007）
      </Typography.Paragraph>
      {checkable.length === 0 ? (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          画布中尚无可校核的工艺单元
        </Typography.Text>
      ) : (
        <Checkbox.Group
          style={{ display: "flex", flexDirection: "column", gap: 2 }}
          options={checkable.map((unitId) => ({
            value: unitId,
            // 件 1：中文名 label+悬浮原 unit_id（追溯面）
            label: (
              <span title={unitId}>
                {unitNames[unitId] ?? unitId}
              </span>
            ),
          }))}
          value={checkedKeys}
          onChange={(next) => handleChange(next as string[])}
        />
      )}
    </div>
  );
}
