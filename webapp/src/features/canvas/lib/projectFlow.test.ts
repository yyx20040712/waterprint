/**
 * 投影层纯函数测试：design 工艺图 JSON → React Flow nodes/edges（D4 TDD）。
 *
 * 输入:  projectFlow 纯函数（node 环境——零 xyflow 运行期 import，先红后绿）
 * 输出:  投影契约断言（format_version 轻门/design 形状窄化逐类拒/悬空边/
 *        kind 徽标面/端口方向聚合/recycle 虚线/layout 优先与拓扑兜底确定性）
 *
 * 规格说明（FE4 批 6b 段一，D1~D6；夹具=golden municipal_34760 内联全量
 * 节选——19 节点 17 边双链，core/tests/golden/golden_data 原样；recycle
 * 边样例取自同族 golden municipal_34760_loop——municipal_34760 无
 * recycle 边）：
 *   - D6 窄化门负例族逐类断言错误消息带索引/键定位（呈现错误薄壳可反查）；
 *   - D3 兜底坐标=波次*X_STEP/层内 key 排序序*Y_STEP——用导出步距常量
 *     计算期望值（不双写魔法数字）。
 */
import { describe, expect, it } from "vitest";

import {
  LAYOUT_X_STEP,
  LAYOUT_Y_STEP,
  ProjectFlowError,
  projectFlow,
} from "./projectFlow";

/** golden municipal_34760 design.nodes 全量内联（19 节点——键序即源序）。 */
const GOLDEN_NODES: Record<string, Record<string, unknown>> = {
  inlet: {
    BOD5: 200.0,
    CODCR: 400.0,
    NH3N: 26.0,
    SS: 250.0,
    TN: 43.0,
    TP: 6.5,
    kind: "municipal_input",
    kz: 1.4,
    q_avg_daily: 0.4023229167,
  },
  municipal_aao: {},
  municipal_bashi_jiliangcao: {},
  municipal_chenshachi: {},
  municipal_chuchenchi: {},
  municipal_cugeshan: {},
  municipal_erchunchi: {},
  municipal_gaomidu: {},
  municipal_vxinglvchi: {},
  municipal_wushui_tisheng: {},
  municipal_xigeshan: {},
  municipal_ziwai: {},
  sludge_bengzhan: {},
  sludge_ganhua: {},
  sludge_hebing: {
    ds_bio: 1928.69,
    ds_chem: 137.705,
    ds_primary: 3240.12,
    p_bio: 0.994,
    p_chem: 0.98,
    p_primary: 0.96,
  },
  sludge_nongsuo: {},
  sludge_shusong: {},
  sludge_tuoshui: {},
  sludge_xiaohua: {},
};

/** golden municipal_34760 design.edges 全量内联（17 边——双独立链）。 */
const GOLDEN_EDGES: Record<string, unknown>[] = [
  { dst: { port_id: "in", unit_id: "municipal_wushui_tisheng" }, src: { port_id: "out", unit_id: "inlet" } },
  { dst: { port_id: "in", unit_id: "municipal_cugeshan" }, src: { port_id: "out", unit_id: "municipal_wushui_tisheng" } },
  { dst: { port_id: "in", unit_id: "municipal_xigeshan" }, src: { port_id: "out", unit_id: "municipal_cugeshan" } },
  { dst: { port_id: "in", unit_id: "municipal_chenshachi" }, src: { port_id: "out", unit_id: "municipal_xigeshan" } },
  { dst: { port_id: "in", unit_id: "municipal_chuchenchi" }, src: { port_id: "out", unit_id: "municipal_chenshachi" } },
  { dst: { port_id: "in", unit_id: "municipal_aao" }, src: { port_id: "out", unit_id: "municipal_chuchenchi" } },
  { dst: { port_id: "in", unit_id: "municipal_erchunchi" }, src: { port_id: "out", unit_id: "municipal_aao" } },
  { dst: { port_id: "in", unit_id: "municipal_gaomidu" }, src: { port_id: "out", unit_id: "municipal_erchunchi" } },
  { dst: { port_id: "in", unit_id: "municipal_vxinglvchi" }, src: { port_id: "out", unit_id: "municipal_gaomidu" } },
  { dst: { port_id: "in", unit_id: "municipal_ziwai" }, src: { port_id: "out", unit_id: "municipal_vxinglvchi" } },
  { dst: { port_id: "in", unit_id: "municipal_bashi_jiliangcao" }, src: { port_id: "out", unit_id: "municipal_ziwai" } },
  { dst: { port_id: "in", unit_id: "sludge_shusong" }, src: { port_id: "out", unit_id: "sludge_hebing" } },
  { dst: { port_id: "in", unit_id: "sludge_bengzhan" }, src: { port_id: "out", unit_id: "sludge_shusong" } },
  { dst: { port_id: "in", unit_id: "sludge_nongsuo" }, src: { port_id: "out", unit_id: "sludge_bengzhan" } },
  { dst: { port_id: "in", unit_id: "sludge_xiaohua" }, src: { port_id: "out", unit_id: "sludge_nongsuo" } },
  { dst: { port_id: "in", unit_id: "sludge_tuoshui" }, src: { port_id: "out", unit_id: "sludge_xiaohua" } },
  { dst: { port_id: "in", unit_id: "sludge_ganhua" }, src: { port_id: "out", unit_id: "sludge_tuoshui" } },
];

/** golden municipal_34760 完整 ProjectFile 顶层（view.layout 全空——兜底必走）。 */
function goldenFixture(
  overrides?: Partial<Record<string, unknown>>,
): Record<string, unknown> {
  return {
    design: {
      assumption_overrides: {},
      checked_units: [],
      constraint_choices: {},
      edges: GOLDEN_EDGES,
      influent: {},
      nodes: GOLDEN_NODES,
      standard_binding: {},
    },
    format_version: "1.0",
    metadata: {
      content_hash: "5c0575e8…",
      data_version: "coefficients@1.0.0+unit_prices@1.0.0",
      engine_version: "waterprint-server 0.1.0",
      format_version: "1.0",
      migrated_from: null,
    },
    view: { camera: {}, layout: {}, timestamp: "", windows: {} },
    ...overrides,
  };
}

/** 双节点小夹具（形状负例与端口聚合用——保持轻量可读）。 */
function tinyFixture(
  overrides?: Partial<Record<string, unknown>>,
): Record<string, unknown> {
  return {
    design: {
      edges: [
        {
          dst: { port_id: "in", unit_id: "unit_b" },
          src: { port_id: "out", unit_id: "unit_a" },
        },
      ],
      nodes: { unit_a: {}, unit_b: {} },
    },
    format_version: "1.0",
    view: {},
    ...overrides,
  };
}

describe("projectFlow：format_version 轻门（D6）", () => {
  it("缺 format_version 拒且消息定位到顶层键", () => {
    const bad = goldenFixture();
    delete bad["format_version"];
    expect(() => projectFlow(bad)).toThrow(ProjectFlowError);
    try {
      projectFlow(bad);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect((error as Error).message).toContain("format_version");
    }
  });

  it("format_version 非 string 拒（数字面）", () => {
    expect(() => projectFlow(goldenFixture({ format_version: 1 }))).toThrow(
      ProjectFlowError,
    );
  });

  it("字符串版本值放行（轻门不校验具体值——版本语义门在 service/core 双闸）", () => {
    const out = projectFlow(goldenFixture({ format_version: "9.9" }));
    expect(out.nodes).toHaveLength(19);
  });
});

describe("projectFlow：design 形状窄化门（D6 逐类显式拒）", () => {
  it("design.nodes 非 object 拒（数组面）", () => {
    const bad = tinyFixture({
      design: { edges: [], nodes: ["unit_a"] },
    });
    expect(() => projectFlow(bad)).toThrow(/design\.nodes/);
  });

  it("节点值非 object 拒且消息带键名定位", () => {
    const bad = tinyFixture({
      design: { edges: [], nodes: { unit_a: 3, unit_b: {} } },
    });
    try {
      projectFlow(bad);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect(error).toBeInstanceOf(ProjectFlowError);
      expect((error as Error).message).toContain("unit_a");
    }
  });

  it("design.edges 非 array 拒", () => {
    const bad = tinyFixture({
      design: { edges: {}, nodes: { unit_a: {}, unit_b: {} } },
    });
    expect(() => projectFlow(bad)).toThrow(/design\.edges/);
  });

  it("边缺 src 拒且消息带索引", () => {
    const bad = tinyFixture({
      design: {
        edges: [{ dst: { port_id: "in", unit_id: "unit_b" } }],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    try {
      projectFlow(bad);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect(error).toBeInstanceOf(ProjectFlowError);
      expect((error as Error).message).toContain("0");
      expect((error as Error).message).toContain("src");
    }
  });

  it("端点非 unit_id/port_id 双 string 拒（port_id 数字面）", () => {
    const bad = tinyFixture({
      design: {
        edges: [
          {
            dst: { port_id: "in", unit_id: "unit_b" },
            src: { port_id: 7, unit_id: "unit_a" },
          },
        ],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    expect(() => projectFlow(bad)).toThrow(/port_id/);
  });

  it("src 端 unit_id 不在 nodes（悬空边）拒且消息带 unit_id", () => {
    const bad = tinyFixture({
      design: {
        edges: [
          {
            dst: { port_id: "in", unit_id: "unit_b" },
            src: { port_id: "out", unit_id: "ghost_9" },
          },
        ],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    try {
      projectFlow(bad);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect(error).toBeInstanceOf(ProjectFlowError);
      expect((error as Error).message).toContain("ghost_9");
    }
  });

  it("dst 端 unit_id 悬空同拒", () => {
    const bad = tinyFixture({
      design: {
        edges: [
          {
            dst: { port_id: "in", unit_id: "ghost_dst" },
            src: { port_id: "out", unit_id: "unit_a" },
          },
        ],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    expect(() => projectFlow(bad)).toThrow(/ghost_dst/);
  });
});

describe("projectFlow：节点投影（D2 纯 unit key+kind 徽标）", () => {
  it("golden 19 节点全投影且 id 序=unit_id 字典序（确定性）", () => {
    const out = projectFlow(goldenFixture());
    expect(out.nodes).toHaveLength(19);
    const ids = out.nodes.map((node) => node.id);
    expect(ids).toEqual([...ids].sort());
    expect(out.nodes.every((node) => node.type === "unit")).toBe(true);
  });

  it("inlet 内置节点 kind=municipal_input 透传且参数值不进 data", () => {
    const out = projectFlow(goldenFixture());
    const inlet = out.nodes.find((node) => node.id === "inlet");
    expect(inlet?.data.unitId).toBe("inlet");
    expect(inlet?.data.kind).toBe("municipal_input");
    // D2：data 键恰集——参数面板挂账段二，BOD5/kz 等不进只读渲染面
    expect(Object.keys(inlet?.data ?? {})).toEqual([
      "unitId",
      "kind",
      "sourcePorts",
      "targetPorts",
    ]);
  });

  it("sludge_hebing 参数覆盖节点 kind=null（单元注册表节点）且参数不进 data", () => {
    const out = projectFlow(goldenFixture());
    const hebing = out.nodes.find((node) => node.id === "sludge_hebing");
    expect(hebing?.data.kind).toBeNull();
    expect(JSON.stringify(hebing?.data)).not.toContain("ds_bio");
  });

  it("端口方向聚合：inlet 源端口 [out]；wushui_tisheng 双向各一", () => {
    const out = projectFlow(goldenFixture());
    const inlet = out.nodes.find((node) => node.id === "inlet");
    expect(inlet?.data.sourcePorts).toEqual(["out"]);
    expect(inlet?.data.targetPorts).toEqual([]);
    const tisheng = out.nodes.find((node) => node.id === "municipal_wushui_tisheng");
    expect(tisheng?.data.sourcePorts).toEqual(["out"]);
    expect(tisheng?.data.targetPorts).toEqual(["in"]);
  });

  it("同侧多端口按字典序排序（loop 节选：hebing 三入端口）", () => {
    const fixture = tinyFixture({
      design: {
        edges: [
          { dst: { port_id: "in_chem", unit_id: "hebing" }, src: { port_id: "sludge_out", unit_id: "chuchenchi" } },
          { dst: { port_id: "in_bio", unit_id: "hebing" }, src: { port_id: "sludge_out", unit_id: "aao" } },
          { dst: { port_id: "in_primary", unit_id: "hebing" }, src: { port_id: "sludge_out", unit_id: "chenshachi" } },
          { dst: { port_id: "in", unit_id: "shusong" }, src: { port_id: "out", unit_id: "hebing" } },
        ],
        nodes: { aao: {}, chenshachi: {}, chuchenchi: {}, hebing: {}, shusong: {} },
      },
    });
    const out = projectFlow(fixture);
    const hebing = out.nodes.find((node) => node.id === "hebing");
    expect(hebing?.data.targetPorts).toEqual(["in_bio", "in_chem", "in_primary"]);
    expect(hebing?.data.sourcePorts).toEqual(["out"]);
  });
});

describe("projectFlow：边投影（D1 方向中性+recycle 虚线例外）", () => {
  it("golden 17 边全投影：端点/handle/箭头标记；无 recycle 即无虚线", () => {
    const out = projectFlow(goldenFixture());
    expect(out.edges).toHaveLength(17);
    const first = out.edges[0];
    expect(first?.source).toBe("inlet");
    expect(first?.sourceHandle).toBe("out");
    expect(first?.target).toBe("municipal_wushui_tisheng");
    expect(first?.targetHandle).toBe("in");
    expect(first?.markerEnd).toEqual({ type: "arrowclosed" });
    for (const edge of out.edges) {
      expect(edge.style?.strokeDasharray).toBeUndefined();
    }
  });

  it("recycle=true → 虚线边（loop 节选：nongsuo→rj_sup 回流）", () => {
    const fixture = tinyFixture({
      design: {
        edges: [
          {
            dst: { port_id: "in", unit_id: "rj_sup" },
            recycle: true,
            src: { port_id: "sup", unit_id: "sludge_nongsuo" },
          },
          {
            dst: { port_id: "in", unit_id: "municipal_wushui_tisheng" },
            recycle: false,
            src: { port_id: "out", unit_id: "rj_sup" },
          },
        ],
        nodes: {
          municipal_wushui_tisheng: {},
          rj_sup: { kind: "recycle_junction" },
          sludge_nongsuo: {},
        },
      },
    });
    const out = projectFlow(fixture);
    expect(out.edges[0]?.style?.strokeDasharray).toBe("6 4");
    expect(out.edges[1]?.style?.strokeDasharray).toBeUndefined();
    // recycle_junction kind 徽标面同路透传（D2 四 kind 之一）
    const rj = out.nodes.find((node) => node.id === "rj_sup");
    expect(rj?.data.kind).toBe("recycle_junction");
  });

  it("边 id 带索引（同端点对多边不撞 id）", () => {
    const fixture = tinyFixture({
      design: {
        edges: [
          { dst: { port_id: "in", unit_id: "unit_b" }, src: { port_id: "out", unit_id: "unit_a" } },
          { dst: { port_id: "in2", unit_id: "unit_b" }, src: { port_id: "out", unit_id: "unit_a" } },
        ],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    const out = projectFlow(fixture);
    expect(new Set(out.edges.map((edge) => edge.id)).size).toBe(2);
  });
});

describe("projectFlow：layout 优先（D3）", () => {
  it("view.layout 全覆盖双 number → position=layout 值直读", () => {
    const fixture = tinyFixture({
      view: {
        layout: { unit_a: { x: 120.5, y: 40 }, unit_b: { x: 400, y: 260 } },
      },
    });
    const out = projectFlow(fixture);
    const a = out.nodes.find((node) => node.id === "unit_a");
    const b = out.nodes.find((node) => node.id === "unit_b");
    expect(a?.position).toEqual({ x: 120.5, y: 40 });
    expect(b?.position).toEqual({ x: 400, y: 260 });
  });

  it("layout 覆盖不全 → 整段忽略走拓扑兜底（unit_a/unit_b 线性链层 0/1）", () => {
    const fixture = tinyFixture({
      view: { layout: { unit_a: { x: 999, y: 999 } } },
    });
    const out = projectFlow(fixture);
    const a = out.nodes.find((node) => node.id === "unit_a");
    expect(a?.position).toEqual({ x: 0, y: 0 });
  });

  it("layout 值形状不符（x 非数字）→ 整段忽略走兜底", () => {
    const fixture = tinyFixture({
      view: {
        layout: { unit_a: { x: "3", y: 0 }, unit_b: { x: 10, y: 10 } },
      },
    });
    const out = projectFlow(fixture);
    const a = out.nodes.find((node) => node.id === "unit_a");
    expect(a?.position).toEqual({ x: 0, y: 0 });
  });

  it("golden view.layout 全空 {} → 兜底路径必走（19 节点全有坐标）", () => {
    const out = projectFlow(goldenFixture());
    expect(out.nodes.every((node) => Number.isFinite(node.position.x))).toBe(true);
  });
});

describe("projectFlow：拓扑兜底确定性（D3 波次分层）", () => {
  it("golden 双链分层：波 0={inlet, sludge_hebing}；链 A 末端层 11", () => {
    const out = projectFlow(goldenFixture());
    const byId = new Map(out.nodes.map((node) => [node.id, node.position]));
    // 波 0：两链首（字典序 inlet < sludge_hebing → y 序 0/1）
    expect(byId.get("inlet")).toEqual({ x: 0, y: 0 });
    expect(byId.get("sludge_hebing")).toEqual({ x: 0, y: LAYOUT_Y_STEP });
    // 波 1：两链第二节点
    expect(byId.get("municipal_wushui_tisheng")).toEqual({ x: LAYOUT_X_STEP, y: 0 });
    expect(byId.get("sludge_shusong")).toEqual({ x: LAYOUT_X_STEP, y: LAYOUT_Y_STEP });
    // 链 A（12 节点）末端层 11（单节点行首）；链 B（7 节点）末端层 6
    // ——波 6 双节点（municipal_aao<sludge_ganhua 字典序 → y 序 0/1）
    expect(byId.get("municipal_bashi_jiliangcao")).toEqual({
      x: 11 * LAYOUT_X_STEP,
      y: 0,
    });
    expect(byId.get("municipal_aao")).toEqual({ x: 6 * LAYOUT_X_STEP, y: 0 });
    expect(byId.get("sludge_ganhua")).toEqual({
      x: 6 * LAYOUT_X_STEP,
      y: LAYOUT_Y_STEP,
    });
    expect(byId.get("municipal_ziwai")).toEqual({ x: 10 * LAYOUT_X_STEP, y: 0 });
  });

  it("同输入双跑输出 deep equal（确定性纯函数）", () => {
    expect(projectFlow(goldenFixture())).toEqual(projectFlow(goldenFixture()));
  });

  it("全无边 → 单列 key 排序（x 全 0、y=序*步距）", () => {
    const fixture = tinyFixture({
      design: { edges: [], nodes: { unit_a: {}, unit_b: {}, unit_c: {} } },
    });
    const out = projectFlow(fixture);
    const positions = out.nodes.map((node) => node.position);
    expect(positions).toEqual([
      { x: 0, y: 0 },
      { x: 0, y: LAYOUT_Y_STEP },
      { x: 0, y: 2 * LAYOUT_Y_STEP },
    ]);
  });

  it("环图破环：无入度 0 节点时取字典序最小起层（确定性不炸）", () => {
    const fixture = tinyFixture({
      design: {
        edges: [
          { dst: { port_id: "in", unit_id: "r_alpha" }, src: { port_id: "out", unit_id: "r_beta" } },
          { dst: { port_id: "in", unit_id: "r_beta" }, src: { port_id: "out", unit_id: "r_alpha" } },
        ],
        nodes: { r_alpha: {}, r_beta: {} },
      },
    });
    const out = projectFlow(fixture);
    const byId = new Map(out.nodes.map((node) => [node.id, node.position]));
    expect(byId.get("r_alpha")).toEqual({ x: 0, y: 0 });
    expect(byId.get("r_beta")).toEqual({ x: LAYOUT_X_STEP, y: 0 });
  });
});

describe("projectFlow：空图与宽容面", () => {
  it("nodes={} edges=[] → 空投影不炸（空态由组件层呈现）", () => {
    const out = projectFlow(
      tinyFixture({ design: { edges: [], nodes: {} } }),
    );
    expect(out.nodes).toEqual([]);
    expect(out.edges).toEqual([]);
  });

  it("recycle 非 bool 值宽容呈现为非虚线（合法性归 server/core 校验链）", () => {
    const fixture = tinyFixture({
      design: {
        edges: [
          {
            dst: { port_id: "in", unit_id: "unit_b" },
            recycle: "yes",
            src: { port_id: "out", unit_id: "unit_a" },
          },
        ],
        nodes: { unit_a: {}, unit_b: {} },
      },
    });
    const out = projectFlow(fixture);
    expect(out.edges[0]?.style?.strokeDasharray).toBeUndefined();
  });
});
