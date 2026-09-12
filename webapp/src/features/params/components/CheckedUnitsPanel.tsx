/**
 * CheckedUnitsPanel（工况校核集合面板——P2 第三批 ADR-018 D4）。
 *
 * 输入:  projectId+useReadProject 原始 GET 体（勾选恢复投影/PUT 基座）
 * 输出:  Checkbox.Group 勾选面板（标题行「受检 k 单元 → 计算工况 2+k 档」
 *        代价提示+勾选即 PUT——CP2 约束勾选持久化样板同构）
 *
 * 规格说明（P2 第三批 ADR-018 D4）：
 *   - 集合语义呈现：标题行直出运行代价（k 受检=2+k 工况——ADR-007
 *      线性口径；散落单元属性无法呈现全局代价=独立面板设计因）；
 *   - 保存链路=CP2 样板复刻：乐观 set+整项目 PUT（withCheckedUnits
 *      结构化替换）→onSuccess invalidate read 键（digest 变→既有 stale
 *      机制自动激活：横幅/导出 409 零新增）→onError 回滚+锁冲突提示；
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
import { LOCK_HINT, WaterprintApiError, isLockConflict } from "../../../shared/api/http";

export function CheckedUnitsPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId);
  const save = useSaveProjectApiProjectsProjectIdPut<WaterprintApiError>();

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
          messageApi.error(
            isLockConflict(error)
              ? LOCK_HINT
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
          options={checkable.map((unitId) => ({ value: unitId, label: unitId }))}
          value={checkedKeys}
          onChange={(next) => handleChange(next as string[])}
        />
      )}
    </div>
  );
}
