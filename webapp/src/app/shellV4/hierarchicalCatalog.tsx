/**
 * 右键分级目录（B1 骨架批 2026-10-09——画布空白右键两级菜单：一级=五
 * 工艺类+结构节点尾组、二级=组内具体工艺；wireframe-d-v4 屏 2 形）。
 *
 * 输入:  x/y（光标位——fixed 定位）+onPick(unit: CatalogUnitEntry)（二级
 *        项点选回调）+onClose（外点/Escape 关闭）+useListUnitsApiUnitsGet
 *        （/api/units 目录——buildCatalogGroups 分级分组）
 * 输出:  两级菜单（.wp-v4-menu：m1 一级列表 hover/点选高亮→m2 二级列表；
 *        二级项点选=onPick 即关）
 *
 * 规格说明（B1 任务书 §三.3——plan §九.1「单元库新形态，原库列/抽屉退役」）：
 *   - 一级类即分组（catalogCategories 单源——36 单元全覆盖核验在测试）；
 *   - 二级目录=组内具体工艺（name_zh 直出，服务端序）；
 *   - 视口钳位（右/下缘溢出回退——固定菜单不遮二级项）；
 *   - 关闭通道三式：外点（pane click 捕获）/Escape/二级项点选。
 */
import { useEffect, useMemo, useRef, useState } from "react";

import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import {
  buildCatalogGroups,
  type CatalogUnitEntry,
} from "../catalogCategories";

export function HierarchicalCatalog({
  x,
  y,
  onPick,
  onClose,
}: {
  /** 光标 clientX/clientY（fixed 定位锚）。 */
  x: number;
  y: number;
  /** 二级项点选（unit=目录条目——unit_id/name_zh/kind）。 */
  onPick: (unit: CatalogUnitEntry) => void;
  onClose: () => void;
}) {
  const catalog = useListUnitsApiUnitsGet();
  const groups = useMemo(
    () => buildCatalogGroups(catalog.data?.units ?? []),
    [catalog.data],
  );
  const [activeId, setActiveId] = useState(groups[0]?.category.id ?? null);
  const ref = useRef<HTMLDivElement | null>(null);

  // 首组随数据到达校正（目录晚到=activeId 兜底首组）
  useEffect(() => {
    if (activeId === null && groups.length > 0) {
      setActiveId(groups[0]?.category.id ?? null);
    }
  }, [groups, activeId]);

  // 外点/Escape 关闭（document 捕获——menu 内点选不关〔二级项自关〕）
  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      if (ref.current !== null && !ref.current.contains(event.target as Node)) {
        onClose();
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("mousedown", onDown, true);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown, true);
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  const active = groups.find((group) => group.category.id === activeId) ?? groups[0];
  // 视口钳位（估宽 240/高 260——右/下缘溢出回退）
  const left = Math.min(x, Math.max(8, window.innerWidth - 250));
  const top = Math.min(y, Math.max(8, window.innerHeight - 270));

  return (
    <div
      ref={ref}
      className="wp-v4-menu"
      style={{ left, top }}
      data-testid="wp-v4-catalog"
    >
      <ul className="wp-v4-m1" data-testid="wp-v4-catalog-level1">
        {groups.map((group) => (
          <li
            key={group.category.id}
            className={group.category.id === active?.category.id ? "on" : ""}
            data-category={group.category.id}
            onClick={() => setActiveId(group.category.id)}
            onMouseEnter={() => setActiveId(group.category.id)}
          >
            <span>{group.category.label}</span>
            <span>›</span>
          </li>
        ))}
      </ul>
      <ul className="wp-v4-m2" data-testid="wp-v4-catalog-level2">
        {(active?.units ?? []).map((unit) => (
          <li
            key={unit.unit_id}
            data-unit={unit.unit_id}
            onClick={() => {
              onPick(unit);
              onClose();
            }}
          >
            {unit.name_zh}
          </li>
        ))}
      </ul>
    </div>
  );
}
