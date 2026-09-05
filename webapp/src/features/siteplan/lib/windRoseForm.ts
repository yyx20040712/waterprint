/**
 * 风玫瑰值表单纯逻辑面（B5 D5——WindRosePanel 写回语义真源；零 antd 零
 * hook——node 直测红线内）。
 *
 * 输入:  wind_rose 原对象（Record<string,number>|null——core SitePlanOptions
 *        .wind_rose 消费面）+八方位表单全量值（dir→number|null，null=未填）
 * 输出:  mergeWindRose 纯函数（合并写回={...原对象未知键保留, ...八方位
 *        非空非负有限值}；全空+有未知键→仅未知键；全空+无未知键→null）
 *
 * 规格说明（简报 D5 改裁——deepseek 必改 1「未知键保留」落地）：
 *   - 键集=固定八方位（WIND_DIRS 单源 import 自 windRoseGeometry——渲染面
 *     同源；开放键=用户可输入渲染不显示的方位，纯困惑源）；
 *   - 未知键（如 NNW）不随八方位编辑静默丢失；全量丢弃唯「清空」显式
 *     确认门（组件面 Popconfirm→onClear 上行 null）；
 *   - 八方位值负/NaN/±Infinity 过滤不入写回（防御直通——InputNumber
 *     min=0 禁负为第一道，本层兜底；未知键值原样保留——JSON 通道真值，
 *     渲染层本就跳过未知键）。
 */
import { WIND_DIRS } from "./windRoseGeometry";

/** 八方位键型（WIND_DIRS 单源派生）。 */
export type WindDir = (typeof WIND_DIRS)[number];

/** 表单值面（dir→用户输入；null/缺省=未填）。 */
export type WindRoseFormValues = Partial<Record<WindDir, number | null>>;

/** 可写回值判定（防御直通：NaN/±Infinity/负值不入写回）。 */
function isWritableNumber(value: number): boolean {
  return Number.isFinite(value) && value >= 0;
}

/** 合并写回（B5 D5 单源）：未知键保留+八方位非空值；两源皆空→null。 */
export function mergeWindRose(
  original: Record<string, number> | null,
  values: WindRoseFormValues,
): Record<string, number> | null {
  const merged: Record<string, number> = {};
  for (const [key, entry] of Object.entries(original ?? {})) {
    if (!(WIND_DIRS as readonly string[]).includes(key)) {
      merged[key] = entry; // 未知键原样保留（不随八方位编辑静默丢失）
    }
  }
  for (const dir of WIND_DIRS) {
    const entry = values[dir];
    if (typeof entry === "number" && isWritableNumber(entry)) {
      merged[dir] = entry;
    }
  }
  return Object.keys(merged).length === 0 ? null : merged;
}
