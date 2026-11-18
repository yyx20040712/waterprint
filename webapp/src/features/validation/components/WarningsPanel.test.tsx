/**
 * WarningsPanel SSR 测试（T3 前端警告聚合批——三分区渲染/降级/空态；
 * CompareMatrix.test 同构先例：renderToString 零 jsdom，纯展示薄壳零
 * 取数零交互面）。
 *
 * 输入:  构造 ValidationObservation 夹具（三分区行混排/∅ 哨兵单形态/
 *        validation_available=false/空 warnings 四态）
 * 输出:  vitest 断言组：①三分区各归其区（声明级/工况聚合/单工况——分区
 *        标题+行 testid 锚）②空分区不渲染 ③severity 徽标语义色 token
 *        ④行 meta=影响面·code·工况键（聚合区清单+计数/直通区单键/声明级
 *        无工况段）⑤validation_available=false=降级条与源 B 警告行并行
 *        （源 A val 件缺席不吞聚合面——server 锁测「源 B 面仍在」同口径；
 *        零警告时=仅降级条）⑥空 warnings+有 val 件=整体不渲染
 */
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { WarningsPanel } from "./WarningsPanel";
import type {
  AggregatedWarningRow,
  ValidationObservation,
} from "../lib/validationView";

/** 观测夹具工厂（v1 消费面：validation_available+warnings；nodes 恒空）。 */
function observation(
  warnings: AggregatedWarningRow[],
  validation_available = true,
): ValidationObservation {
  return {
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "h1",
    engine_version: "e1",
    data_version: "d1",
    kb_injected: null,
    validation_available,
    conditions: ["avg", "design"],
    nodes: [],
    warnings,
  };
}

/** SSR 文本归一：剥 react-dom/server 文本分段注释节点（<!-- -->）。 */
function textOf(html: string): string {
  return html.replaceAll("<!-- -->", "");
}

/** 三形态混排夹具：∅ 哨兵（源 A）/双工况（源 B ≥2）/单工况（直通）。 */
const MIXED: AggregatedWarningRow[] = [
  {
    code: "kb.influent.bod_band",
    param_key: "bod",
    scope: "plant",
    message: "进水 BOD 300mg/L 超出建议带 [80, 250]",
    condition_keys: [],
    severity: "WARN",
  },
  {
    code: "kb.aao.n_band",
    param_key: "n",
    scope: "municipal_aao",
    message: "N=28 越门：kb.aao.n_band——n 违反 n<=25",
    condition_keys: ["avg", "design"],
    severity: "ERROR",
  },
  {
    code: "kb.cass.srt_band",
    param_key: "srt",
    scope: "municipal_cass",
    message: "泥龄 8d 低于建议带 [12, 25]",
    condition_keys: ["design"],
    severity: "WARN",
  },
];

describe("WarningsPanel 三分区（warning-aggregation.md §3）", () => {
  it("三形态各行归其区：声明级/工况聚合/单工况（标题+行 testid 锚）", () => {
    const html = renderToString(<WarningsPanel observation={observation(MIXED)} />);
    const text = textOf(html);
    expect(html).toContain('data-testid="wp-v4-warnings-declaration"');
    expect(html).toContain('data-testid="wp-v4-warnings-aggregated"');
    expect(html).toContain('data-testid="wp-v4-warnings-single"');
    expect(text).toContain("警告聚合 3");
    expect(text).toContain("声明级 1");
    expect(text).toContain("工况聚合 1");
    expect(text).toContain("单工况 1");
    // 各区行内容锚（message 全文在场）
    expect(text).toContain("进水 BOD 300mg/L 超出建议带");
    expect(text).toContain("N=28 越门");
    expect(text).toContain("泥龄 8d 低于建议带");
  });

  it("行 meta：影响面标签（全厂/节点 ID）+code mono+工况键（清单+计数/单键/∅ 无段）", () => {
    const html = renderToString(<WarningsPanel observation={observation(MIXED)} />);
    const text = textOf(html);
    // 声明级行：scope=plant→全厂；∅ 哨兵无工况段（「工况 」仅两处）
    expect(text).toContain("全厂 · kb.influent.bod_band");
    // 聚合行：清单+计数
    expect(text).toContain("municipal_aao · kb.aao.n_band · 工况 avg、design（2）");
    // 直通行：单键
    expect(text).toContain("municipal_cass · kb.cass.srt_band · 工况 design");
    // ∅ 哨兵行无工况段：meta 工况段恰两处（聚合+直通——声明级缺席）
    expect(text.match(/· 工况 /g)?.length).toBe(2);
    // code 呈现走 mono 字族（窄面板小字 meta 行）
    expect(html).toContain("var(--wp-font-mono)");
  });

  it("severity 徽标语义色 token（ERROR=--wp-error/WARN=--wpv4-warn）+中文徽标", () => {
    const html = renderToString(<WarningsPanel observation={observation(MIXED)} />);
    const text = textOf(html);
    expect(html).toContain("var(--wp-error)");
    expect(html).toContain("var(--wpv4-warn)");
    expect(text).toContain("错误");
    expect(text).toContain("警告");
  });

  it("空分区不渲染（仅 ∅ 哨兵行=声明级区独现，他两区 testid 不在场）", () => {
    const declarationRow = MIXED[0];
    if (declarationRow === undefined) throw new Error("夹具缺声明级行");
    const html = renderToString(
      <WarningsPanel observation={observation([declarationRow])} />,
    );
    expect(html).toContain('data-testid="wp-v4-warnings-declaration"');
    expect(html).not.toContain('data-testid="wp-v4-warnings-aggregated"');
    expect(html).not.toContain('data-testid="wp-v4-warnings-single"');
  });
});

describe("WarningsPanel 降级与空态", () => {
  it("validation_available=false+源 B 警告在场=降级条与三分区并行（源 A val 件缺席不吞聚合面——server 锁测「源 B 面仍在」同口径）", () => {
    const html = renderToString(
      <WarningsPanel observation={observation(MIXED, false)} />,
    );
    const text = textOf(html);
    // 降级条在场（源 A 缺席如实提示）
    expect(html).toContain('data-testid="wp-v4-validation-unavailable"');
    expect(text).toContain("结果集无校验观测（旧版本结果）——重算后生成");
    // 源 B 聚合面照常渲染：面板壳+三分区+数据行均在（不因降级早退）
    expect(html).toContain('data-testid="wp-v4-warnings-panel"');
    expect(html).toContain('data-testid="wp-v4-warnings-declaration"');
    expect(html).toContain('data-testid="wp-v4-warnings-aggregated"');
    expect(html).toContain('data-testid="wp-v4-warnings-single"');
    expect(html.match(/data-testid="wp-v4-warning-row"/g)?.length).toBe(3);
    expect(text).toContain("N=28 越门");
  });

  it("validation_available=false+零警告=仅降级条（无面板壳无数据行）", () => {
    const html = renderToString(
      <WarningsPanel observation={observation([], false)} />,
    );
    const text = textOf(html);
    expect(html).toContain('data-testid="wp-v4-validation-unavailable"');
    expect(text).toContain("结果集无校验观测（旧版本结果）——重算后生成");
    expect(html).not.toContain('data-testid="wp-v4-warnings-panel"');
    expect(html).not.toContain('data-testid="wp-v4-warning-row"');
  });

  it("空 warnings+有 val 件=整体不渲染（零警告不打扰——输出空）", () => {
    const html = renderToString(<WarningsPanel observation={observation([])} />);
    expect(html).toBe("");
  });
});
