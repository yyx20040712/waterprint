/**
 * 分组变换数学核（assemble/spec.md §3/§4 规格冻结件——批3 首件）。
 *
 * 输入:  场景图节点 dims+kind（sceneDimsToTarget 归并）+模板典型尺寸
 *        （shellScale）+扫描面节点摘要与 equipment 特征规格（groupTransform）
 * 输出:  TargetDims/壳缩放向量/分组变换 {translation, scale}（列矢量约定
 *        M = T(translation)·diag(scale)——缩放先作用）/行列式
 *
 * 规格说明（S1~S6 终裁落函数；零 three 依赖）：
 *   - 统一公式（S1 唯一定法=「位置缩放+截面轴逆缩放抵消」）：
 *       M = T(t)·diag(σ)，t = anchor ⊙ (s − σ)
 *     s=壳缩放（glTF 轴 [L/L0, H/H0, W/W0]）；σ=该组轴缩放：
 *       shell：σ=s（锚点项恒等抵消——归一化壳直撑计算尺寸）；
 *       trim：延伸轴 σ_i=s_i、定值轴 σ_i=1（截面/高度米制恒定，锚点
 *         随壳缩放走=安装面随池体顶/缘移动；y 轴恒定值——S1 立法）；
 *       equipment：σ=(u,u,u)，u=actual/templateFeature（S3 数据链）；
 *       instance：不经本函数（P7 呈裁——数量分支禁推导未裁）。
 *   - 数学核防线（S6）：一切产出 σ 分量>0⟹det>0（transformDeterminant
 *     断言）；非正尺寸/非法掩码/缺规格=显式 AssembleSpecError（数据病
 *     显式拒非静默）。目标尺寸非正应先经 deviation 裁定降级——本层
 *     throw=漏裁防线（两层分工 spec §6）。
 *   - 轴对应（S2-③）：dims length/width/depth（z-up 存储）→模板本地
 *     glTF 系 x/y/z=长/深/宽（两系经各自 (x,z,−y) 换轴后在 three 世界
 *     同构——单测对拍 projectScene 实跑锚定）。
 */

import type {
  AxisMask,
  EquipmentSpec,
  GroupTransform,
  TargetDims,
  TemplateNodeMeta,
  TemplateSize,
  Vec3,
} from "./types";

/** 分组变换数学非法（非正尺寸/竖直轴入延伸集/缺特征规格/instance 组
 *  越权——模板或 registry 数据病，显式拒）。 */
export class AssembleSpecError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AssembleSpecError";
  }
}

/**
 * 轴对应表（S2-③）：场景图节点 dims → 目标尺寸（米）。
 * box（AAO 廊道族等）：length/width/depth→L/W/H；cylinder（辐流等）：
 * diameter→L=W（直径口径直用，半径换算归 three 接口适配层）、depth→H。
 * 其余 kind/缺键→null（族域外——装配器走 registry 无条目/降级路径，
 * 本函数不抛）。
 */
export function sceneDimsToTarget(
  kind: string,
  dims: Record<string, number>,
): TargetDims | null {
  if (kind === "box") {
    const length = dims["length"];
    const width = dims["width"];
    const depth = dims["depth"];
    if (length === undefined || width === undefined || depth === undefined) {
      return null;
    }
    return { L: length, W: width, H: depth };
  }
  if (kind === "cylinder") {
    const diameter = dims["diameter"];
    const depth = dims["depth"];
    if (diameter === undefined || depth === undefined) {
      return null;
    }
    return { L: diameter, W: diameter, H: depth };
  }
  return null;
}

/**
 * 壳缩放向量（glTF 本地轴序）：x=L/L0（长）、y=H/H0（深/上）、
 * z=W/W0（宽/南）——轴序即轴对应表落数值（单测三值互异断言锚）。
 * 模板典型尺寸非正=registry 声明病显式拒；目标尺寸非正=deviation
 * 应先裁降级（漏裁防线 throw——两层分工 spec §6）。
 */
export function shellScale(target: TargetDims, templateSize: TemplateSize): Vec3 {
  const { L0, W0, H0 } = templateSize;
  if (!(L0 > 0) || !(W0 > 0) || !(H0 > 0)) {
    throw new AssembleSpecError(
      `模板典型尺寸非正：L0=${L0}, W0=${W0}, H0=${H0}——registry templateSize 声明病`,
    );
  }
  const { L, W, H } = target;
  if (!(L > 0) || !(W > 0) || !(H > 0)) {
    throw new AssembleSpecError(
      `目标尺寸非正：L=${L}, W=${W}, H=${H}——deviation 应先裁降级（nonpositive_dim）`,
    );
  }
  return [L / L0, H / H0, W / W0];
}

/** 轴缩放向量行列式（对角阵 det=三分量积；S6 断言面=恒正）。 */
export function transformDeterminant(scale: Vec3): number {
  return scale[0] * scale[1] * scale[2];
}

/** −0 归一 +0（JS 取负零 Artifact——负锚点×零差积出 −0；沿 projectScene
 *  L5R 同坑先例：渲染等价、Object.is/序列化面区分）。 */
function normalizeZero(value: number): number {
  return value === 0 ? 0 : value;
}

/** trim 组轴缩放：延伸轴跟随壳、定值轴恒 1；y（竖直）入延伸集=S1
 *  立法违例显式拒（规范定值不随池深缩放）。 */
function trimScale(mask: AxisMask, shell: Vec3): Vec3 {
  if (mask[1]) {
    throw new AssembleSpecError(
      `trim 竖直轴（y）入延伸集：[${mask.join(",")}]——S1 立法违例（竖直定值，规范定件不随池深缩放）`,
    );
  }
  return [
    mask[0] ? shell[0] : 1,
    mask[1] ? shell[1] : 1,
    mask[2] ? shell[2] : 1,
  ];
}

/**
 * 分组变换（统一公式 §3）：M = T(anchor ⊙ (s − σ))·diag(σ)。
 * shell：σ=s（translation 恒 [0,0,0]——锚点抵消）；trim：延伸轴跟随+
 * 定值轴恒 1（截面米制恒定，锚点随壳走）；equipment：等比 u=actual/
 * templateFeature（保圆——三轴等模）；instance：越权拒（P7 未裁，
 * instanceLayout 归批3 主体）。产出 det≤0 显式拒（S6 硬条款防线）。
 */
export function groupTransform(
  node: TemplateNodeMeta,
  shell: Vec3,
  equipment?: EquipmentSpec,
): GroupTransform {
  let scale: Vec3;
  if (node.group === "shell") {
    scale = shell;
  } else if (node.group === "trim") {
    scale = trimScale(node.stretch, shell);
  } else if (node.group === "equipment") {
    if (equipment === undefined) {
      throw new AssembleSpecError(
        `equipment 组缺特征规格：${node.name}——registry characteristic 声明病`,
      );
    }
    if (!(equipment.templateFeature > 0) || !(equipment.actual > 0)) {
      throw new AssembleSpecError(
        `equipment 特征规格非正：templateFeature=${equipment.templateFeature}, `
          + `actual=${equipment.actual}——registry 声明病`,
      );
    }
    const u = equipment.actual / equipment.templateFeature;
    scale = [u, u, u];
  } else {
    throw new AssembleSpecError(
      `instance 组不经 groupTransform：${node.name}——数量分支 P7 呈裁未决，`
        + "instanceLayout 归批3 主体",
    );
  }
  const translation: Vec3 = [
    normalizeZero(node.anchor[0] * (shell[0] - scale[0])),
    normalizeZero(node.anchor[1] * (shell[1] - scale[1])),
    normalizeZero(node.anchor[2] * (shell[2] - scale[2])),
  ];
  if (!(transformDeterminant(scale) > 0)) {
    throw new AssembleSpecError(
      `分组缩放行列式非正：[${scale.join(",")}]——S6 硬条款（实例矩阵 det>0）`,
    );
  }
  return { translation, scale };
}
