/**
 * 投影层 vitest（D3）：DXF 文本 → SVG 场景模型（内联最小 fixture——探针
 * 实证仅 ENTITIES 段即可解析、中文无损；模板字符串构造避 shell heredoc
 * EOF 怪癖——b-probe 实录）。
 *
 * 输入:  内联 DXF fixture 字符串（mini/带表/带块三形态+残件）
 * 输出:  projectDxf 断言（items 展开/Y 翻转数值锚/extents 边距算术/ACI
 *        色映射/DIMENSION 匿名块+INSERT 变换/DxfSceneError/退化防御）
 *
 * 规格说明（B 批 D3；dxfScene.ts 契约面——渲染薄壳 DxfSvg 不测先例）：
 *   - 坐标口径：x'=x−minX+5%·spanX、y'=maxY−y+5%·spanY（DXF Y 向上/
 *     SVG Y 向下顶翻）；width/height=span·1.1（两侧 5% 边距）；
 *   - fontSize=max(dxfHeight, max(spanX,spanY)/60)（显示层可读口径）；
 *   - INSERT 变换：p'=position+R(rotation°)·(xScale·vx, yScale·vy)；
 *   - fixture 行数说明：带 TABLES/BLOCKS 段物理最小 ~40-66 行（mini.dxf
 *     先例 39 行同族）——简报 ≤30 行为意向值，物理不可行面记档。
 */
import { describe, expect, it } from "vitest";

import { DxfSceneError, projectDxf, type SvgItem } from "./dxfScene";

/** 最小 DXF（探针 mini.dxf 先例：仅 ENTITIES 段——无表=色兜底负例面）。 */
const MINI_DXF = `  0
SECTION
  2
ENTITIES
  0
LWPOLYLINE
  8
WP-process-pool
 90
3
 10
0.0
 20
0.0
 10
45000.0
 20
0.0
 10
45000.0
 20
30000.0
  0
TEXT
  8
WP-anno-label
 10
1000.0
 20
31000.0
 40
2.5
  1
粗格栅中文
  0
ENDSEC
  0
EOF
`;

/** 带 LAYER 表（ACI 7/1 两层）+两条 poly——色映射正例面。 */
const TABLE_DXF = `  0
SECTION
  2
TABLES
  0
TABLE
  2
LAYER
 70
2
  0
LAYER
  2
WP-a
 62
7
  0
LAYER
  2
WP-b
 62
1
  0
ENDTAB
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LWPOLYLINE
  8
WP-a
 90
2
 10
0.0
 20
0.0
 10
100.0
 20
0.0
  0
LWPOLYLINE
  8
WP-b
 90
2
 10
0.0
 20
50.0
 10
100.0
 20
50.0
  0
ENDSEC
  0
EOF
`;

/** BLOCKS（*D1 匿名块+箭头块 _CLOSEDFILLED）+DIMENSION——块展开面。 */
const DIM_DXF = `  0
SECTION
  2
BLOCKS
  0
BLOCK
  2
_CLOSEDFILLED
  0
SOLID
  8
0
 10
0.0
 20
0.0
 11
-1.0
 21
0.5
 12
-0.333
 22
0.0
 13
-1.0
 23
-0.5
  0
ENDBLK
  0
BLOCK
  2
*D1
  0
LINE
  8
WP-dim
 10
0.0
 20
0.0
 11
100.0
 21
0.0
  0
MTEXT
  8
WP-dim
 10
50.0
 20
10.0
 40
2.5
  1
4500
  0
POINT
  8
Defpoints
 10
25.0
 20
0.0
  0
INSERT
  8
WP-dim
  2
_CLOSEDFILLED
 10
100.0
 20
0.0
 41
0.25
 42
0.25
 50
90.0
  0
ENDBLK
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
DIMENSION
  8
WP-dim
  2
*D1
 10
0.0
 20
0.0
 11
50.0
 21
10.0
 70
32
  0
ENDSEC
  0
EOF
`;

/** 空实体段（SECTION/ENTITIES/EOF 骨架）——退化防御面。 */
const EMPTY_DXF = `  0
SECTION
  2
ENTITIES
  0
ENDSEC
  0
EOF
`;

/** 按类型取唯一项（fixture 每类至多一项——重复即测试自身错）。 */
function soleItem(items: SvgItem[], kind: SvgItem["kind"]): SvgItem {
  const hits = items.filter((item) => item.kind === kind);
  const sole = hits[0];
  if (hits.length !== 1 || sole === undefined) {
    throw new Error(`fixture 断言前置失败：${kind} 应恰一项，得到 ${hits.length}`);
  }
  return sole;
}

/** 取 polygon points 解析后的第 i 组坐标对（形态异常即测试自身错）。 */
function pairAt(pairs: number[][], index: number): [number, number] {
  const pair = pairs[index];
  const x = pair?.[0];
  const y = pair?.[1];
  if (x === undefined || y === undefined) {
    throw new Error(`fixture 断言前置失败：points[${index}] 形态异常`);
  }
  return [x, y];
}

describe("projectDxf 基本投影", () => {
  it("LWPOLYLINE→path+TEXT→text 两项；中文逐字往返", () => {
    const scene = projectDxf(MINI_DXF);
    expect(scene.items).toHaveLength(2);
    const path = soleItem(scene.items, "path");
    expect(path.kind).toBe("path");
    const text = soleItem(scene.items, "text");
    // 中文无损（E 冻结 §三最大风险面——逐字断言）
    expect(text).toMatchObject({ kind: "text", text: "粗格栅中文" });
  });

  it("fontSize=max(dxf 高度, 图幅跨度/60)——750=45000/60 可读性放大", () => {
    const text = soleItem(projectDxf(MINI_DXF).items, "text");
    expect(text.kind === "text" && text.fontSize).toBe(750);
  });
});

describe("坐标变换（Y 顶翻+extents 边距）", () => {
  it("Y 翻转数值锚：y'=maxY−y+5%·spanY（31000 顶→1550 底）", () => {
    // minX=0 maxX=45000 minY=0 maxY=31000 → padY=0.05·31000=1550
    const text = soleItem(projectDxf(MINI_DXF).items, "text");
    // TEXT 起点 (1000,31000)：x'=1000+2250=3250；y'=31000−31000+1550=1550
    expect(text).toMatchObject({ kind: "text", x: 3250, y: 1550 });
  });

  it("extents+两侧 5% 边距：width=1.1·spanX=49500、height=1.1·spanY=34100", () => {
    const scene = projectDxf(MINI_DXF);
    expect(scene.width).toBe(49500);
    expect(scene.height).toBe(34100);
    // path 折线 d 全坐标数值锚（整数坐标零浮点尾差——整串断言）
    const path = soleItem(scene.items, "path");
    // 顶点 (45000,30000)：y'=31000−30000+1550=2550（Y 顶翻+边距算术）
    expect(path.kind === "path" && path.d).toBe(
      "M 2250,32550 L 47250,32550 L 47250,2550",
    );
  });
});

describe("ACI 图层色映射（1-7 显示层常量）", () => {
  it("表内层取色：colorIndex 7→#303030（白线深灰适配）、1→#ff0000", () => {
    const paths = projectDxf(TABLE_DXF).items.filter(
      (item) => item.kind === "path",
    );
    expect(paths).toHaveLength(2);
    const [first, second] = paths;
    if (first === undefined || second === undefined) {
      throw new Error("fixture 断言前置失败：两条 path 预期缺项");
    }
    expect(first.kind === "path" && first.color).toBe("#303030");
    expect(second.kind === "path" && second.color).toBe("#ff0000");
  });

  it("无表/缺层→中性 #6b6b6b 兜底", () => {
    const path = soleItem(projectDxf(MINI_DXF).items, "path");
    expect(path.kind === "path" && path.color).toBe("#6b6b6b");
  });
});

describe("DIMENSION 匿名块展开", () => {
  it("块内 LINE→path、MTEXT→text、POINT 跳过（POINT 不产项）", () => {
    const items = projectDxf(DIM_DXF).items;
    const kinds = items.map((item) => item.kind).sort();
    expect(kinds).toEqual(["path", "solid", "text"]);
    const text = soleItem(items, "text");
    expect(text).toMatchObject({ kind: "text", text: "4500" });
  });

  it("INSERT 变换数值锚：p'=position+R(90°)·(scale·v)——箭头 SOLID 四点", () => {
    // 图幅：minX=0 maxX=100.125 minY=−0.25 maxY=10 → padX=5.00625 padY=0.5125
    // SOLID 局部点 (0,0)/(−1,0.5)/(−0.333,0)/(−1,−0.5)，scale 0.25，旋转 90°，
    // 平移 (100,0)——顶点 1 不动点变换后 (100,0)→(105.00625, 10.5125)
    const solid = soleItem(projectDxf(DIM_DXF).items, "solid");
    if (solid.kind !== "solid") {
      throw new Error("unreachable");
    }
    const pts = solid.points
      .split(" ")
      .map((pair) => pair.split(",").map(Number));
    expect(pts).toHaveLength(4);
    const [x0, y0] = pairAt(pts, 0);
    const [x1, y1] = pairAt(pts, 1);
    const [x2, y2] = pairAt(pts, 2);
    const [x3, y3] = pairAt(pts, 3);
    expect(x0).toBeCloseTo(105.00625, 5);
    expect(y0).toBeCloseTo(10.5125, 5);
    expect(x1).toBeCloseTo(104.88125, 5);
    expect(y1).toBeCloseTo(10.7625, 5);
    expect(x2).toBeCloseTo(105.00625, 5);
    expect(y2).toBeCloseTo(10.59575, 5);
    expect(x3).toBeCloseTo(105.13125, 5);
    expect(y3).toBeCloseTo(10.7625, 5);
  });
});

describe("错误与退化防御", () => {
  it("空串/残件→DxfSceneError（中文消息含原始 error.message）", () => {
    expect(() => projectDxf("")).toThrow(DxfSceneError);
    try {
      projectDxf("");
    } catch (error) {
      const err = error as DxfSceneError;
      expect(err.name).toBe("DxfSceneError");
      expect(err.message).toContain("DXF 解析失败");
      expect(err.message).toContain("Empty file");
    }
    const FRAGMENT_DXF = "  0\nSECTION\n  2\nENTITIES\n";
    expect(() => projectDxf(FRAGMENT_DXF)).toThrow(DxfSceneError);
  });

  it("空实体→1×1 空场景（不除零不炸）", () => {
    expect(projectDxf(EMPTY_DXF)).toEqual({
      width: 1,
      height: 1,
      items: [],
    });
  });
});
