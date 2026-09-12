/**
 * 模板 inst 组布局（spec.md §11 S8/P7 裁定+P5 常量——批3 主体；
 * 段二扩 box 族布局模式——AAO/CASS）。
 *
 * 输入:  原型节点 AABB（基座位）+场景图 instance_count+壳缩放+布局声明
 *        （mode/spacing/envelope——registry instanceModes/instanceSpacing/
 *        templateSize 派生）
 * 输出:  laid（逐实例位姿——模板本地系 anchor⊙s）或 skipped
 *        （无场景数量——不渲染+调用方登记 fallbackLog）
 *
 * 规格说明（P7 已裁：数量唯一真源=场景图 instance_count；禁由布置域÷
 *   间距常量推导[铁律 3 边界]。位姿=统一公式 σ=𝟙 形：p=anchor⊙s——
 *   基座随壳缩放走，几何恒定不缩[§3 instance 行]）：
 *   - ring（缺省——辐流立柱）：环上均布角距，首实例角=原型基座角；
 *   - grid（AAO/CASS 曝气头——0.8m 间距 P5 签核）：包络域近方阵行列
 *     布点，位置居中，行优先取 count 个（cols=round(L0/spacing) 起算
 *     ——间距≈spacing，行数随 count 适配，位置推导合法[数量不推导]）；
 *   - line_x / line_z（CASS 滗水器等线列）：沿池长/池宽轴均布，
 *     正交轴=原型基座坐标（原型建模即定位在安装线上）；
 *   - rect（box 族走道立柱）：原型基座为角位推断周界矩形（对称半宽
 *     hx=|protoX|/hz=|protoZ|——建模约定原型建在走道中线角位），沿
 *     周界弧长按 spacing 步进 count 点，起点=原型位（顺时针）。
 */

import type { Vec3 } from "./types";

/** 布局模式（registry instanceModes 声明值；缺省 ring=辐流零改）。 */
export type InstanceMode = "ring" | "grid" | "line_x" | "line_z" | "rect";

/** 布局声明（TemplateUnit 从 registry 条目派生——spacing/envelope 仅
 * 非 ring 模式消费）。 */
export type InstanceLayoutOpts = {
  readonly mode?: InstanceMode;
  readonly spacing?: number;
  readonly envelope?: { readonly L0: number; readonly W0: number };
};

export type InstanceLayoutResult =
  | { readonly kind: "laid"; readonly positions: readonly Vec3[] }
  | { readonly kind: "skipped"; readonly reason: "no_scene_count" | "bad_spacing" };

/** grid/line/rect 的间距有效性（非正=registry instanceSpacing 声明病——
 * skipped 登记（P7 语义面外显，不静默错布局）。 */
function validSpacing(opts: InstanceLayoutOpts): boolean {
  return typeof opts.spacing === "number" && opts.spacing > 0;
}

/** −0 归一（JS 负零 Artifact——ring 先例同防）。 */
function z(value: number): number {
  return value === 0 ? 0 : value;
}

/** 环形均布（首实例角=原型基座角——原型位即 0 号位；σ=𝟙 位姿=anchor⊙s）。 */
export function instanceLayout(
  prototypeAabb: { readonly min: Vec3; readonly max: Vec3 },
  count: number | null,
  shell: Vec3,
  opts: InstanceLayoutOpts = {},
): InstanceLayoutResult {
  if (count === null || !Number.isFinite(count) || count < 1) {
    return { kind: "skipped", reason: "no_scene_count" };
  }
  const n = Math.floor(count);
  const cx = (prototypeAabb.min[0] + prototypeAabb.max[0]) / 2;
  const cz = (prototypeAabb.min[2] + prototypeAabb.max[2]) / 2;
  // y 锚=几何中心（门二 P0/P1 修复：meshopt 量化把几何归一化、节点
  // TRS scale 承载尺寸恢复——量化网格原点≈几何 AABB 中心；渲染端
  // clone 清 position 后 group 位=几何中心位——锚取中心而非 min y，
  // 消"0 起建模"的半高偏差）
  const cy = (prototypeAabb.min[1] + prototypeAabb.max[1]) / 2;
  const radius = Math.hypot(cx, cz);
  const theta0 = Math.atan2(cz, cx);
  const mode = opts.mode ?? "ring";
  const positions: Vec3[] = [];

  if (mode === "ring") {
    for (let i = 0; i < n; i += 1) {
      const theta = theta0 + (2 * Math.PI * i) / n;
      const anchorX = radius * Math.cos(theta);
      const anchorZ = radius * Math.sin(theta);
      // p=anchor⊙s（σ=𝟙——位姿随壳缩放走；0 分量归一防 −0 artifact）
      positions.push([
        z(anchorX * shell[0]),
        z(cy * shell[1]),
        z(anchorZ * shell[2]),
      ]);
    }
    return { kind: "laid", positions };
  }

  if (!validSpacing(opts)) {
    return { kind: "skipped", reason: "bad_spacing" };
  }
  const spacing = opts.spacing as number;

  if (mode === "grid") {
    const l0 = opts.envelope?.L0 ?? radius * 2;
    // cols=包络列数上限内取 count（count<包络列=单行紧凑居中，不散布
    // 左端）；rows 随 count 适配（位置推导合法——数量不推导[P7]）。
    // z 向不设界（W0 不 clamp rows）：count 超出包络容量=场景数据信号
    // （门一 W3 记档——布局不裁剪数量真源）
    const cols = Math.max(1, Math.min(Math.round(l0 / spacing), n));
    const rows = Math.max(1, Math.ceil(n / cols));
    for (let i = 0; i < n; i += 1) {
      const r = Math.floor(i / cols);
      const c = i % cols;
      positions.push([
        z((c - (cols - 1) / 2) * spacing * shell[0]),
        z(cy * shell[1]),
        z((r - (rows - 1) / 2) * spacing * shell[2]),
      ]);
    }
    return { kind: "laid", positions };
  }

  if (mode === "line_x") {
    for (let i = 0; i < n; i += 1) {
      positions.push([
        z((i - (n - 1) / 2) * spacing * shell[0]),
        z(cy * shell[1]),
        z(cz * shell[2]),
      ]);
    }
    return { kind: "laid", positions };
  }

  if (mode === "line_z") {
    for (let i = 0; i < n; i += 1) {
      positions.push([
        z(cx * shell[0]),
        z(cy * shell[1]),
        z((i - (n - 1) / 2) * spacing * shell[2]),
      ]);
    }
    return { kind: "laid", positions };
  }

  // rect：周界矩形（对称半宽=原型基座 |cx|/|cz|——建模约定原型在角位
  // 走道中线；弧长步进 spacing，起点=顶行东角顺时针西行。注：真实资产
  // 原型在 (hx,−hz) 角时 0 号位落在 (hx,+hz) 对角（周界对称视觉无碍
  // ——门二 P2 记档；rail_post 现无场景计数不渲染）
  const hx = Math.max(Math.abs(cx), spacing);
  const hz = Math.max(Math.abs(cz), spacing);
  const perimeter = 2 * (2 * hx + 2 * hz);
  for (let i = 0; i < n; i += 1) {
    const s = (i * spacing) % perimeter;
    let x = 0;
    let zz = 0;
    const topLen = 2 * hx;
    const sideLen = 2 * hz;
    if (s < topLen) {
      x = hx - s;
      zz = hz;
    } else if (s < topLen + sideLen) {
      x = -hx;
      zz = hz - (s - topLen);
    } else if (s < 2 * topLen + sideLen) {
      x = -hx + (s - topLen - sideLen);
      zz = -hz;
    } else {
      x = hx;
      zz = -hz + (s - 2 * topLen - sideLen);
    }
    positions.push([z(x * shell[0]), z(cy * shell[1]), z(zz * shell[2])]);
  }
  return { kind: "laid", positions };
}
