/**
 * 设计假设清单面板：默认值显性化只读清单（§3 保证 7——DEFAULTS∪覆盖合成）。
 *
 * 输入:  projectId（useAssumptionCatalog 声明面+useProjectDesign 覆盖面）
 * 输出:  假设只读清单（key/默认值/合成值/dim/出处/说明/调向+覆盖标记蓝点
 *        ——21 条 registry 声明序，覆盖计数提示）
 *
 * 规格说明（FE5 批 6b 段三，D1 只读实装——骨架期「修改走 design 态保存
 *   流程」的编辑面挂账：本面板零编辑交互；默认值显性化=每条出处可见）：
 *   - 合成行=buildAssumptionRows（DEFAULTS∪assumption_overrides 覆盖优先
 *     ——目录外覆盖键追加成行）；覆盖标记=蓝点+「默认 x」并列显示；
 *   - 与 ParamForm 共消费 useProjectDesign（同 queryKey 缓存自动共享——
 *     apply 提交 invalidate 后本面板随 refetch 同步）；
 *   - 错误/加载薄壳与 ParamForm 同构（Error.message 透出）。
 */
import { useMemo } from "react";
import { Typography } from "antd";

import { useAssumptionCatalog } from "../api/useUnitCatalog";
import { useProjectDesign } from "../api/useProjectDesign";
import { buildAssumptionRows, type AssumptionRow } from "../lib/designParams";

const SELECT_BLUE = "#1668dc";
const GRAY_SMALL = { color: "#8c8c8c", fontSize: 11 };

/** 单行假设（只读——覆盖行蓝点+默认值并列）。 */
function AssumptionLine({ row }: { row: AssumptionRow }) {
  return (
    <div style={{ padding: "4px 0", borderBottom: "1px solid #303030" }}>
      <div style={{ fontFamily: "monospace", fontSize: 12, wordBreak: "break-all" }}>
        {row.key}
        {row.overridden ? (
          <span
            title="项目覆盖值（design.assumption_overrides）"
            style={{
              display: "inline-block",
              width: 6,
              height: 6,
              margin: "0 0 0 6px",
              borderRadius: 3,
              background: SELECT_BLUE,
            }}
          />
        ) : null}
      </div>
      <div style={{ fontSize: 12 }}>
        值 {row.value}
        {row.overridden && row.defaultValue !== null
          ? `（覆盖；默认 ${row.defaultValue}）`
          : row.overridden
            ? "（覆盖；目录外键）"
            : "（默认）"}
        {row.dim ? ` · ${row.dim}` : ""}
      </div>
      {row.source || row.tuningDirection ? (
        <div style={GRAY_SMALL}>
          {[row.source, row.tuningDirection].filter(Boolean).join(" · ")}
        </div>
      ) : null}
      {row.note ? <div style={GRAY_SMALL}>{row.note}</div> : null}
    </div>
  );
}

export function AssumptionsPanel({ projectId }: { projectId: string }) {
  const catalogQuery = useAssumptionCatalog();
  const designQuery = useProjectDesign(projectId);
  const rows = useMemo(
    () =>
      buildAssumptionRows(
        catalogQuery.data?.assumptions ?? [],
        designQuery.data?.assumptionOverrides ?? {},
      ),
    [catalogQuery.data, designQuery.data],
  );
  const overrideCount = rows.filter((row) => row.overridden).length;

  if (catalogQuery.isError || designQuery.isError) {
    const error = catalogQuery.error ?? designQuery.error;
    return (
      <section>
        <Typography.Title level={5}>设计假设（只读）</Typography.Title>
        <Typography.Text type="danger">
          假设清单加载失败：
          {error instanceof Error ? error.message : "未知错误"}
        </Typography.Text>
      </section>
    );
  }
  return (
    <section>
      <Typography.Title level={5}>设计假设（只读）</Typography.Title>
      {!catalogQuery.data || !designQuery.data ? (
        <Typography.Text type="secondary">假设清单加载中…</Typography.Text>
      ) : (
        <>
          <Typography.Text type="secondary" style={GRAY_SMALL}>
            {rows.length} 条 registry 声明序
            {overrideCount > 0 ? ` · ${overrideCount} 项项目覆盖` : " · 无项目覆盖"}
            （覆盖编辑挂账后续批）
          </Typography.Text>
          <div style={{ maxHeight: 280, overflowY: "auto", marginTop: 4 }}>
            {rows.map((row) => (
              <AssumptionLine key={row.key} row={row} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
