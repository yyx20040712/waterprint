/**
 * 检修观测卡组件 SSR 测试（门一回炉轮 1 k1-W2 主控裁定——renderToString
 * 先例=solutionsNotices.test.tsx：react-dom/server 断言，零新依赖〔P4 未裁
 * 不破〕，无 jsdom 无渲染库）。
 *
 * 输入:  MaintenanceObservationView 纯展示组件+ValidationObservation 桩
 * 输出:  三降级条文案可见（val 缺席/kb 未注入/stale——顺带锚死 antd6
 *        Alert title prop 现行性〔B1 误判免疫针：title 渲染路径在
 *        6.x=Alert.js mergedTitle〕）+nodes 空态+节点行渲染各一
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import {
  narrowValidationObservation,
  type ValidationObservation,
} from "../lib/maintenanceView";

import { MaintenanceObservationView } from "./MaintenanceObservationView";

/** SSR 渲染壳（QueryClientProvider——catalog name_zh 查询上下文需求，
 * TaskPanel.test 同款先例；SSR 期查询 pending→节点头回退 node_id 直显）。 */
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

const VAL_MISSING_TITLE =
  "本结果无校验件（旧版本计算或校验件缺失/损坏）——重新提交计算后可获取。";
const KB_MISSING_TITLE =
  "kb 未注入：本结果计算时约束知识库未参与（kb 执法面为空）——重算后可获取。";
const STALE_TITLE =
  "结果已过期：计算后设计有变更——建议重新提交计算获取最新检修观测。";

function observation(overrides: Record<string, unknown>): ValidationObservation {
  return narrowValidationObservation({
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "h1",
    engine_version: "e1",
    data_version: "d1",
    kb_injected: true,
    validation_available: true,
    conditions: ["design", "design_offline_municipal_aao"],
    nodes: [
      {
        node_id: "municipal_aao",
        faces: [
          {
            condition_key: "design_offline_municipal_aao",
            kb: { "param.n.positive": true, "param.h2.positive": false },
            any_fail: true,
            ratio: { n: 2.0 },
            fixgeom_min: -1.0,
          },
        ],
      },
    ],
    warnings: [],
    ...overrides,
  });
}

function render(obs: ValidationObservation): string {
  return renderToString(
    <QueryClientProvider client={queryClient}>
      <MaintenanceObservationView observation={obs} />
    </QueryClientProvider>,
  );
}

describe("MaintenanceObservationView SSR（k1-W2）", () => {
  it("健康态：节点头与逐工况行渲染（kb 条目通过/越门+分化字段+裕度）", () => {
    const html = render(observation({}));
    expect(html).toContain("municipal_aao"); // 节点头（catalog 名缺席回退 node_id）
    expect(html).toContain("检修越门"); // any_fail 故障灯（nodeFailed）
    expect(html).toContain("通过"); // kb 条目 pass Tag
    expect(html).toContain("越门"); // kb 条目 fail Tag
    expect(html).toContain("×2.000"); // ratio 分化键值
    expect(html).toContain("-1.00"); // fixgeom 裕度
  });

  it("三降级条文案可见（antd6 Alert title prop 现行性锚——B1 免疫针）", () => {
    const html = render(observation({
      stale: true,
      kb_injected: false,
      validation_available: false,
    }));
    expect(html).toContain(VAL_MISSING_TITLE);
    expect(html).toContain(KB_MISSING_TITLE);
    expect(html).toContain(STALE_TITLE);
  });

  it("nodes 空态：无可观测检修工况", () => {
    const html = render(observation({ nodes: [] }));
    expect(html).toContain("无可观测检修工况");
  });
});
