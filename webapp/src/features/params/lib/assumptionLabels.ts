/**
 * 设计假设中文物理意义标签（C2-ALIGN A5r）：key → 展示名映射。
 *
 * 输入:  假设 key（registry AssumptionSet 键面）
 * 输出:  assumptionLabel(key)——中文物理意义标签（未知键 fail-open 回退
 *        key 原文——可见性保底，禁隐藏）
 *
 * 规格说明（briefs/task-c2-align-plan.md A5r——用户澄清 2026-09-12：
 *   「所有参数都要显示物理意义而不是代码名称」）：
 *   - 目录 AssumptionEntry 无标签字段（key/default/dim/source/note/
 *     tuning_direction 六字段——API 实核）——本字典=显示层翻译面
 *     （shared/dimLabels 同款纪律：展示层映射非业务复制）；
 *   - 词条来源=registry 22 键的 note 物理语义提炼（值/单位/出处零触碰
 *     ——仅命名）；长期归宿=core registry Assumption 增 label_zh+
 *     server 透出（挂账升级路径——与 assumptionScope 分类同批记档）；
 *   - registry 增键未入字典 → fail-open 回退 key 原文（可见性保底——
 *     key 裸显即可读性提示）；镜像测试=手工键面（webapp 禁 import
 *     core/python 面——AL-N-01 R2 诚实化：core 增键不自动红，须手工
 *     同步词条+镜像；core 化挂账[Assumption.label_zh]为根治路径）。
 */

/** registry 22 键 → 中文物理意义（值域语义提炼自 note——非编造数值面）。 */
const LABELS: Readonly<Record<string, string>> = {
  "safety.superheight": "安全超高",
  "loop.tolerance": "回路收敛容差",
  "loop.max_iterations": "回路迭代步数上限",
  "loop.damping": "回路阻尼系数",
  "solution.grid.base_per_dim": "枚举网格每维基数上限",
  "elevation.wall_thickness": "池壁厚度（概算）",
  "elevation.bury_depth.max": "池底埋深告警上限",
  "elevation.drop_threshold": "跌水提示阈值",
  "elevation.losses.friction_lambda": "沿程损失系数 λ",
  "elevation.losses.gravity": "重力加速度 g",
  "elevation.losses.weir_coefficient": "堰流流量系数",
  "elevation.losses.orifice_coefficient": "孔口流量系数",
  "elevation.pump.pipe_length": "提升管路概算管长",
  "elevation.pump.pipe_diameter": "提升管路概算管径",
  "geometry.pool.spacing": "并联池组列间距",
  "network.solve.tolerance": "管网求解流量容差",
  "network.solve.max_iterations": "管网二分轮数上限",
  "network.solve.depth_min": "管网水深区间下限",
  "network.solve.depth_max": "管网水深区间上限",
  "network.excel.max_rows": "管网导入行数上限",
  "network.excel.max_file_bytes": "管网导入文件大小上限",
  "solution.design_map.max_points": "可行域扫描总点数上限",
};

/** registry 22 键全集（镜像测试锁——core 增键未入字典即红）。 */
export const ASSUMPTION_KEYS: readonly string[] = Object.keys(LABELS);

/** key → 中文物理意义标签（未知键 fail-open 回退 key 原文）。 */
export function assumptionLabel(key: string): string {
  return LABELS[key] ?? key;
}
