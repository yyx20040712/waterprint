/**
 * 检修缺位占位（spec.md §11 S11 裁定——批3 段三；数据源=params/结果面，
 * 零 core 改）。
 *
 * 输入:  nPools（单元设计池数——params 面，如 CASS n_pool）
 *        nActive（当前工况有效池数——condition_key 派生：design_offline_
 *        <unit_id> 即该单元 nPools−1，其余=nPools）
 *        spacing（池心距 m——显示层常量[铁律 3 合法面]，调用方组合
 *        单池宽+净距）
 * 输出:  缺位槽列表（index=近方阵槽序、position=模板本地系池底平面
 *        轮廓中心 [x, 0, z]——渲染层警示占位[半透明轮廓/虚线框]+徽标消费）
 *
 * 规格说明（S11 契约冻结面）：
 *   - 排布口径=近方阵居中（cols=ceil(sqrt(nPools))、行主序、行组中心
 *     对齐）——与 instanceLayout grid 居中口径同构（池组中心=单元
 *     origin）；**末行不二次居中**（槽位锚 cols 网格左对齐——与在用
 *     池前填同口径，工程语义最小承诺；门一 P2-3 口径注记）；
 *   - 缺位=尾槽 [nActive, nPools)（并联池组均质，检修取尾位与在用池
 *     无区分——工程语义最小承诺）；
 *   - 纯数据零异常：契约病（非有限数/nPools<1/nActive<0/spacing≤0/
 *     nActive≥nPools）返回 []，登记归调用方（deviation.ts 两层分工先例）。
 */

import type { Vec3 } from "./types";

/** 缺位槽（index=池组近方阵槽序；position=模板本地系 [x, 0, z]）。 */
export type MissingSlot = {
  readonly index: number;
  readonly position: Vec3;
};

/** −0 归一（JS 负零 Artifact——projectScene/instanceLayout 先例同防）。 */
function z0(value: number): number {
  return value === 0 ? 0 : value;
}

/**
 * 缺位占位派生（S11 纯函数契约——spec §11 冻结签名）。
 *
 * 数量唯一真源=调用方数据面（params nPools+工况 nActive——渲染层不
 * 推导池数，P7 同界）；本函数只做槽位坐标派生（位置推导合法）。
 */
export function missingSlotPlaceholders(
  nPools: number,
  nActive: number,
  spacing: number,
): MissingSlot[] {
  if (
    !Number.isFinite(nPools) ||
    !Number.isFinite(nActive) ||
    !Number.isFinite(spacing) ||
    nPools < 1 ||
    nActive < 0 ||
    spacing <= 0 ||
    nActive >= nPools
  ) {
    return [];
  }
  const total = Math.floor(nPools);
  const active = Math.floor(nActive);
  if (active >= total) {
    return [];
  }
  const cols = Math.max(1, Math.ceil(Math.sqrt(total)));
  const rows = Math.max(1, Math.ceil(total / cols));
  const slots: MissingSlot[] = [];
  for (let index = active; index < total; index += 1) {
    const col = index % cols;
    const row = Math.floor(index / cols);
    slots.push({
      index,
      position: [
        z0((col - (cols - 1) / 2) * spacing),
        0,
        z0((row - (rows - 1) / 2) * spacing),
      ],
    });
  }
  return slots;
}
