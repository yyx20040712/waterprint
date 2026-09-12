/**
 * 工况键显示映射：GR-20 冻结键族 → 工程中文名（工况面 UX 反馈批件 1）。
 *
 * 输入:  condition_key 字符串（载荷面的工况稳定键——core contracts/
 *        condition.py ConditionSet.key 三族：design / avg /
 *        design_offline_<unit_id>）+unitNames（unit_id → 中文名索引
 *        ——/api/units catalog name_zh 真源，调用方经 orval listUnits
 *        hook select 投影）
 * 输出:  conditionLabel(key, unitNames) → 工程中文名（design→「最高日
 *        最高时」、avg→「平均日」、design_offline_<id>→「<单元中文名>
 *        检修」；单元中文名缺失退「<unit_id> 检修」id 透传；族外键
 *        原样返回——诚实呈现不猜语义，dimLabels 同口径）
 *
 * 规格说明（工况面 UX 反馈批 2026-09-12，用户裁定）：
 *   - 键值全 UI 面中文化（用户反馈「拼音显得太笨」）；命名口径=
 *     工程全称（design=最高日最高时/avg=平均日/design_offline=单元名+
 *     检修）；**全部中文名 title 悬浮显示原始键**（用户裁定——追溯面
 *     对照接口文档；title 挂接归各消费面）；
 *   - 纯显示层词典（result_schema R2「稳定字段 ID+中文名只存在于 i18n
 *     显示层」铁律——dimLabels 先例同制）；键族 GR-20 冻结值域可穷举
 *     =词典法前提；**零换算零改键**（工况键是载荷/哈希面冻结值——
 *     显示层只译不改）；
 *   - offline 键拆段=固定前缀 slice（前缀长度恒定，unit_id 含下划线
 *     不歧义）；单元中文名真源=catalog name_zh（服务端 manifest），
 *     FE 不复制单元名录（避免第二真相源）；
 *   - 基线两族为静态词典；offline 族为参数化合成（unitNames 运行期
 *     取数——catalog 未就绪=空索引，退 id 透传非阻塞）。
 */

/** unit_id → 中文名索引（catalog name_zh 投影——调用方 select 建面）。 */
export type UnitNameIndex = Record<string, string>;

/** 基线工况键 → 中文名（GR-20 冻结两档——静态词典面）。 */
export const BASE_CONDITION_LABELS: Record<string, string> = {
  design: "最高日最高时",
  avg: "平均日",
};

/** offline 键固定前缀（core condition.py GR-20 冻结字面量镜像）。 */
const OFFLINE_PREFIX = "design_offline_";

/** offline 键中文名：单元中文名+「检修」（缺失退 id 透传——非猜测）。 */
function offlineLabel(unitId: string, unitNames: UnitNameIndex): string {
  const name = unitNames[unitId];
  return name !== undefined ? `${name}检修` : `${unitId} 检修`;
}

/** 工况键 → 工程中文名（基线词典命中 / offline 拆段合成 / 族外原样）。 */
export function conditionLabel(key: string, unitNames: UnitNameIndex): string {
  const base = BASE_CONDITION_LABELS[key];
  if (base !== undefined) {
    return base;
  }
  if (key.startsWith(OFFLINE_PREFIX)) {
    return offlineLabel(key.slice(OFFLINE_PREFIX.length), unitNames);
  }
  return key;
}

/** catalog → unit_id→中文名索引（orval hook select 投影——结构化参数
 * 不 import orval 类型；模块级引用稳定=select 不逐渲染重跑，
 * useCompareQuery 同纪律）。 */
export function unitNameIndex(catalog: {
  units: ReadonlyArray<{ unit_id: string; name_zh: string }>;
}): UnitNameIndex {
  const index: Record<string, string> = {};
  for (const unit of catalog.units) {
    index[unit.unit_id] = unit.name_zh;
  }
  return index;
}
