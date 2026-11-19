/**
 * 工艺单元库侧栏（b3 功能面重涂批 2026-11-19——稿 network.html 左栏
 * .pane.left 形：分级目录树常驻〔一级类折叠组+二级单元行〕+搜索过滤+
 * 点行落画布通道；沿革 B1 右键二级目录〔hierarchicalCatalog〕常驻化——
 * 右键通道保留，本栏=第二添加通道）。
 *
 * 输入:  onPickUnit（二级项点选——ProcessZone 组装 addRequest 落画布
 *        中心）+useListUnitsApiUnitsGet（/api/units 目录——
 *        buildCatalogGroups 分级分组）
 * 输出:  左栏：pane-head〔工艺单元库+计数〕+搜索框+树（六类折叠组——
 *        组头计数 badge+组内单元行〔+ 前缀〕）+底注（添加方式说明）
 *
 * 规格说明（b3 批准稿 network.html 左栏段）：
 *   - 一级类=buildCatalogGroups 单源（六类声明序——与右键目录同源，
 *     两通道分组恒一致）；
 *   - 搜索=unit_id/name_zh 前端过滤（本地零新端点；命中组保留、空组
 *     隐藏；空串=全量）；
 *   - 点行=onPickUnit（落画布中心——拖拽通道=后续批裁量，稿「拖到
 *     画布」语义以点选先行承载）；
 *   - 组折叠态本地（默认全展——服务端序保持）。
 */
import { useMemo, useState } from "react";

import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import {
  buildCatalogGroups,
  type CatalogUnitEntry,
} from "../catalogCategories";

export function UnitLibraryPane({
  onPickUnit,
}: {
  /** 二级项点选（unit=目录条目——unit_id/name_zh/kind）。 */
  onPickUnit: (unit: CatalogUnitEntry) => void;
}) {
  const catalog = useListUnitsApiUnitsGet();
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set());

  const groups = useMemo(() => {
    const all = buildCatalogGroups(catalog.data?.units ?? []);
    const needle = search.trim().toLowerCase();
    if (needle === "") {
      return all;
    }
    return all
      .map((group) => ({
        ...group,
        units: group.units.filter(
          (unit) =>
            unit.unit_id.toLowerCase().includes(needle) ||
            unit.name_zh.toLowerCase().includes(needle),
        ),
      }))
      .filter((group) => group.units.length > 0);
  }, [catalog.data, search]);

  const total = useMemo(
    () => (catalog.data?.units ?? []).length,
    [catalog.data],
  );

  return (
    <aside className="wp-v4-pane left" data-region="unit-library">
      <div className="wp-v4-pane-head">
        <h3>工艺单元库</h3>
        <span className="wp-v4-badge">{total}</span>
      </div>
      <div className="wp-v4-search">
        <input
          aria-label="搜索单元"
          placeholder="搜索中文名或单元 ID"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          data-testid="wp-v4-lib-search"
        />
      </div>
      <div className="wp-v4-pane-body">
        {catalog.isError ? (
          <p
            role="alert"
            style={{ color: "var(--wp-error)", fontSize: 11, padding: "6px 10px" }}
          >
            目录加载失败：
            {catalog.error instanceof Error ? catalog.error.message : "未知错误"}
          </p>
        ) : catalog.isPending ? (
          <p style={{ color: "var(--wp-text-2)", fontSize: 11, padding: "6px 10px" }}>
            目录加载中…
          </p>
        ) : groups.length === 0 ? (
          <p style={{ color: "var(--wp-text-2)", fontSize: 11, padding: "6px 10px" }}>
            无匹配单元
          </p>
        ) : (
          <div className="wp-v4-tree" data-testid="wp-v4-lib-tree">
            {groups.map((group) => {
              const open = !collapsed.has(group.category.id);
              return (
                <div key={group.category.id} data-category={group.category.id}>
                  <button
                    type="button"
                    className="wp-v4-tree-group"
                    aria-expanded={open}
                    data-testid={`wp-v4-lib-group-${group.category.id}`}
                    onClick={() =>
                      setCollapsed((prev) => {
                        const next = new Set(prev);
                        if (next.has(group.category.id)) {
                          next.delete(group.category.id);
                        } else {
                          next.add(group.category.id);
                        }
                        return next;
                      })
                    }
                  >
                    <span className="chev" aria-hidden>
                      {open ? "▾" : "▸"}
                    </span>
                    <span>{group.category.label}</span>
                    <span className="cnt">{group.units.length}</span>
                  </button>
                  {open
                    ? group.units.map((unit) => (
                        <button
                          key={unit.unit_id}
                          type="button"
                          className="wp-v4-tree-row"
                          data-testid={`wp-v4-lib-unit-${unit.unit_id}`}
                          title={unit.unit_id}
                          onClick={() => onPickUnit(unit)}
                        >
                          <span>{unit.name_zh}</span>
                          <span className="plus" aria-hidden>
                            +
                          </span>
                        </button>
                      ))
                    : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
      <div className="wp-v4-pane-foot">
        点选单元加入画布，或右键画布空白处按业务分组添加。端口类型决定可连接方向。
      </div>
    </aside>
  );
}
