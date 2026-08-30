/**
 * drawings 单元目录查询：orval units hook 薄封装（builtin 判别通道——
 * UX1 D3 单元 Select 可投影面过滤的真源）。
 *
 * 输入:  无参（GET /api/units 静态目录——与 params 面同键缓存共享）
 * 输出:  useQuery 结果句柄（data=Set<string>——catalog kind==='builtin'
 *        条目的 unit_id 集[=design.nodes 值键同面：内置节点 kind 值即
 *        目录 unit_id]；错误统一 WaterprintApiError——本封装零错误处理）
 *
 * 规格说明（UX1 批 6b 段八 D3；params useUnitCatalog 同键先例——
 *   features 互禁 import 故本 feature 自持封装，不互借）：
 *   - queryKey 恒 ['/api/units'] 与 params 面 useUnitCatalog 同键缓存
 *     自动共享（单次取数多 feature 消费——META1 registry 投影，进程期
 *     内目录不失效，无 invalidate 面）；
 *   - select 投影 builtin 集：kind 判别值取生成物单源
 *     （UnitMetaEntryKind.builtin——禁手写双份）；四内置 kind 值域
 *     零硬编码（真源=服务端目录 36 条中 kind==='builtin' 条目的
 *     unit_id 集——server units.py _builtin_entry「unit_id=kind=
 *     design.nodes 值键同面」合同）；
 *   - 消费面（drawingsPane）：catalog 未就绪（loading/error——data
 *     undefined）不过滤（优雅降级——过滤是增强非门禁）；
 *   - select 模块级引用稳定（不逐渲染重跑——react-query 结构保持）。
 */
import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { UnitMetaEntryKind } from "../../../shared/api/generated/model";

/** 目录响应 → builtin unit_id 集（可投影面过滤的判别集）。 */
function selectBuiltinIds(catalog: { units: { kind: string; unit_id: string }[] }): Set<string> {
  const ids = new Set<string>();
  for (const entry of catalog.units) {
    if (entry.kind === UnitMetaEntryKind.builtin) {
      ids.add(entry.unit_id);
    }
  }
  return ids;
}

/** 单元目录 builtin 集查询（D3 过滤通道——data undefined=未就绪不过滤）。 */
export function useUnitCatalog() {
  return useListUnitsApiUnitsGet<Set<string>, Error>({
    query: { select: selectBuiltinIds },
  });
}
