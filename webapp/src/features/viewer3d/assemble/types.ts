/**
 * 三维模板装配·类型层（assemble/spec.md 规格冻结件——批3 首件 2026-09-12）。
 *
 * 输入:  无运行时输入（纯类型+冻结常量；groupScan/computeTransforms/
 *        deviation/registry 后续件共用词汇——本批只冻结词汇与常量）
 * 输出:  Vec3/GroupKind/AxisMask/TargetDims/TemplateSize/TemplateNodeMeta/
 *        EquipmentSpec/GroupTransform/RatioDomainEntry/DeviationResult
 *        +DEFAULT_TRIM_STRETCH（trim 缺省延伸掩码）
 *
 * 规格说明（spec.md §2/§3/§9；零 three 依赖——纯函数纪律）：
 *   - 工作系=模板本地 glTF 系（X 东=长向、Y 上=深向、Z 南=宽负向——
 *     Blender z-up 建模经 +Y up 导出后节点坐标实际所在系；轴对应表
 *     spec §1 与 projectScene L5R 换轴 (x,z,−y) 同构直配）；
 *   - GroupKind 四组（命名规约 shell|trim|equip|inst；R1 终裁无 cap 组
 *     ——剖口封盖走 C2VD stencil 机制非预建组）；
 *   - trim 竖直轴恒不入延伸集（S1 立法：规范定值不随池深缩放——
 *     glTF 系竖直=y）。
 */

/** 三分量向量（模板本地 glTF 系——[x=长, y=深/上, z=宽/南负向]）。 */
export type Vec3 = readonly [number, number, number];

/** 分组类（Blender 命名规约 shell/trim/equip/inst 四组；扫描层归一时
 *  equip→equipment、inst→instance 映射到本枚举）。 */
export type GroupKind = "shell" | "trim" | "equipment" | "instance";

/** 延伸轴掩码（glTF 本地轴序 [x=长, y=深/上, z=宽]；true=该轴跟随壳
 *  缩放，false=定值轴。trim 组 y 恒 false——S1 竖直定值立法）。 */
export type AxisMask = readonly [boolean, boolean, boolean];

/** 目标尺寸（米——场景图 dims 经 sceneDimsToTarget 归并的长宽深；
 *  cylinder 族 L=W=diameter）。 */
export type TargetDims = {
  readonly L: number;
  readonly W: number;
  readonly H: number;
};

/** 模板典型尺寸（米——registry 声明；语义=模板中壳外接盒实际米数
 *  [S3 终裁：templateSize=模板特征实际米数口径]，CI 对拍 shell 组
 *  AABB 容差校验）。 */
export type TemplateSize = {
  readonly L0: number;
  readonly W0: number;
  readonly H0: number;
};

/** trim 组缺省延伸掩码=水平双向（长+宽延伸、高度恒定——池顶沿/环形
 *  走道类主形态；单延伸向件显式 `__ax` 后缀声明）。 */
export const DEFAULT_TRIM_STRETCH: AxisMask = [true, false, true];

/** 扫描面节点摘要（groupScan 产出——批3 主体件；本批冻结其消费契约：
 *  锚点派生规则见 spec §3——trim=节点 AABB min（安装面锚）、
 *  equipment=registry 语义锚[pool_center_bottom→模板原点 / aabb_min]、
 *  shell 锚点恒等抵消任意、instance 不经 groupTransform）。 */
export type TemplateNodeMeta = {
  readonly name: string;
  readonly group: GroupKind;
  readonly stretch: AxisMask;
  /** 锚点（模板米制 glTF 本地系——锚定语义=随壳缩放走的位置基准点）。 */
  readonly anchor: Vec3;
};

/** equipment 特征规格（S3 数据链闭环：u=actual/templateFeature；actual
 *  由 registry actualFactor 派生系数从场景 dims 折算，如中心筒
 *  actualFactor=0.12×diameter）。 */
export type EquipmentSpec = {
  /** 模板中该特征实际米数（如中心筒直径 3.0m）。 */
  readonly templateFeature: number;
  /** 实际特征米数（registry actualFactor×场景 dim 派生）。 */
  readonly actual: number;
};

/** 分组变换输出（列矢量约定：M = T(translation)·diag(scale)——缩放先
 *  作用[S2-①]；组件层以 three Object3D position/scale 分量承载）。 */
export type GroupTransform = {
  readonly translation: Vec3;
  readonly scale: Vec3;
};

/** 比例域声明条目（ratio=numerator/denominator 两轴比；闭域 [min,max]
 *  ——typical 比由 registry 建条目时以 templateSize 标定，运行时只判
 *  绝对比域[P2 呈裁初始值，spec §6 附草案表]）。 */
export type RatioDomainEntry = {
  readonly key: string;
  readonly numerator: "L" | "W" | "H";
  readonly denominator: "L" | "W" | "H";
  readonly min: number;
  readonly max: number;
};

/** 降级判定结果（ok=模板面可行；fallback 决策归装配器走 FallbackBox
 *  +fallbackLog 登记——本类型零异常纯数据）。 */
export type DeviationResult =
  | { readonly ok: true }
  | {
      readonly ok: false;
      readonly reason: "nonpositive_dim";
      readonly dim: "L" | "W" | "H";
    }
  | {
      readonly ok: false;
      readonly reason: "ratio_out_of_domain";
      readonly key: string;
      readonly ratio: number;
      readonly domain: readonly [number, number];
    };
