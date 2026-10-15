/**
 * @vitest-environment jsdom
 *
 * v4 计算说明区导航/侧栏面拆件测试（V4 批 P5+P6——reportZone.test 预算墙
 * 500 拆件承载：导航条目剥 id 括注 DOM 锚+侧栏横向溢出修复锚〔uiglobal
 * B5=scrollW 193>clientW 186 实测 7px——拖柄外溢+长文无省略双因〕）。
 *
 * 输入:  ReportZone（report 读端点 hook 模块替身——最小 mock 面：useProject
 *        Id+report+项目读+scrollIntoView 桩）+global.css 源文（node fs 直读
 *        ——vitest css 管线桩空 .css?raw）
 * 输出:  断言族：①P5 导航条目显示=剥尾部全 ASCII 括注（title 悬浮全称；
 *        中文括注/无括注零扰动）②P6 拖柄缘内化（.wp-v4-sider 域 right:0
 *        ——left/right 主面不受牵连）③P6 条目省略三件套（minWidth:0+
 *        overflow/textOverflow/whiteSpace——长文不撑宽侧栏）
 */
import { cleanup, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReportZone, stripIdParenthetical } from "./reportZone";

/** localStorage 存根（usePaneWidth 消费面——reportZone.test 同制）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
});

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  report: {
    data: undefined as unknown,
    isError: false as boolean,
    isPending: false as boolean,
  },
}));

vi.mock("../useProjectId", () => ({ useProjectId: () => ["p1"] }));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetProjectReportApiCalcProjectsProjectIdReportGet: () => gate.report,
  useRunCalculationApiCalcRunPost: () => ({ mutate: vi.fn(), isPending: false }),
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({
    data: { project_id: "p1", view: { name: "城南厂" } },
  }),
}));
vi.mock("../../features/drawings/api/useExportArtifact", () => ({
  useExportArtifact: () => ({ mutate: vi.fn(), isPending: false }),
}));

/** 夹具基座（sections 由用例覆写）。 */
const REPORT_BASE = {
  project_id: "p1",
  condition_key: "design",
  stale: false,
  design_hash: "d1d1d1d1d1d1",
  markdown: "## 章",
  generated_from: { digest10: "abc123def0" },
};

function renderZone() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ReportZone />
    </QueryClientProvider>,
  );
}

/** global.css 源文（zeroPedagogyGate.test 同制路径构造）。 */
const globalCssSource = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../global.css"),
  "utf-8",
);

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(cleanup);

describe("计算说明区·V4 导航剥 id 括注（P5——显示面）", () => {
  it("stripIdParenthetical 纯函数（全/半角·中文括注不动·仅尾注·边界）", () => {
    const cases: Array<[string, string]> = [
      ["AAO 生物池（municipal_aao）", "AAO 生物池"], // 全角服务端形
      ["AAO 生物池(municipal_aao)", "AAO 生物池"], // 半角同剥
      ["进出水水质（design 工况，mg/L）", "进出水水质（design 工况，mg/L）"], // 中文括注不动
      ["设计原始资料", "设计原始资料"], // 无括注
      ["（municipal_aao）", ""], // 全括注=剥后空
      ["中段（id）尾注", "中段（id）尾注"], // 仅剥尾部
    ];
    for (const [input, want] of cases) {
      expect(stripIdParenthetical(input)).toBe(want);
    }
  });

  it("条目显示=剥尾部全 ASCII 括注+title 悬浮全称（中文括注/无括注零扰动）", () => {
    gate.report = {
      data: {
        ...REPORT_BASE,
        sections: [
          { id: "uc-aao", title: "AAO 生物池（municipal_aao）", level: 1 },
          { id: "qual", title: "进出水水质（design 工况，mg/L）", level: 2 },
          { id: "plain", title: "设计原始资料", level: 1 },
        ],
      },
      isError: false,
      isPending: false,
    };
    const { container } = renderZone();
    const items = container.querySelectorAll<HTMLElement>(
      '[data-testid="wp-v4-report-nav-item"]',
    );
    expect(items.length).toBe(3);
    expect(items[0]?.textContent).toBe("AAO 生物池"); // 剥 id 括注
    expect(items[1]?.textContent).toBe("进出水水质（design 工况，mg/L）"); // 中文括注不动
    expect(items[2]?.textContent).toBe("设计原始资料");
    expect(items[0]?.getAttribute("title")).toBe("AAO 生物池（municipal_aao）"); // 悬浮全称
    expect(items[1]?.getAttribute("title")).toBe("进出水水质（design 工况，mg/L）");
  });
});

describe("计算说明区·V4 侧栏横向溢出修复（P6——uiglobal B5）", () => {
  it("拖柄缘内化：.wp-v4-sider .wp-v4-drag right:0（-4px 外溢退役；主面板不受牵连）", () => {
    // 侧栏 aside overflow:auto 下柄外溢 4px=scrollWidth 涨面主因之一
    expect(globalCssSource).toMatch(/\.wp-v4-sider \.wp-v4-drag\s*\{\s*right:\s*0;\s*\}/);
    // .wp-v4-left 面保持 -4px（overflow 可见无滚动面——外溢即贴边热区）
    expect(globalCssSource).toMatch(/\.wp-v4-left \.wp-v4-drag\s*\{\s*right:\s*-4px;\s*\}/);
  });

  it("导航条目省略锚：minWidth:0+ellipsis 三件套（长文不撑宽侧栏）", () => {
    gate.report = {
      data: {
        ...REPORT_BASE,
        sections: [
          {
            id: "long",
            title: "超长章题超长章题超长章题超长章题超长章题超长章题超长章题",
            level: 1,
          },
        ],
      },
      isError: false,
      isPending: false,
    };
    const { container } = renderZone();
    const item = container.querySelector<HTMLElement>('[data-testid="wp-v4-report-nav-item"]');
    expect(item).not.toBeNull();
    expect(item?.style.minWidth).toBe("0px"); // jsdom 归一 0→0px
    expect(item?.style.overflow).toBe("hidden");
    expect(item?.style.textOverflow).toBe("ellipsis");
    expect(item?.style.whiteSpace).toBe("nowrap");
  });

  // 主控回炉 R1：柄缘内化+条目省略后实测仍余 3px 幻影横滚
  // （scrollWidth 201>clientWidth 198——分数舍入/纵滚条互作，非实内容
  // 外溢：全部子元素 bounding 右缘 ≤ 内容缘实测在档）。修法=横轴裁剪：
  // overflowX hidden（overflowY auto 保留——导航长列表滚动面不受牵连）。
  it("侧栏横轴裁剪锚：aside overflowX=hidden+overflowY=auto（幻影 3px 横滚退役）", () => {
    gate.report = {
      data: { ...REPORT_BASE, sections: [{ id: "s1", title: "设计依据", level: 1 }] },
      isError: false,
      isPending: false,
    };
    const { container } = renderZone();
    const aside = container.querySelector<HTMLElement>('[data-region="report-nav"]');
    expect(aside).not.toBeNull();
    expect(aside?.style.overflowX).toBe("hidden");
    expect(aside?.style.overflowY).toBe("auto");
  });
});
