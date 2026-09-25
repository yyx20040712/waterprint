/**
 * viewer3dPane 目录失败 Alert 测试（F5 D5——catalog 未就绪显式提示）。
 *
 * 输入:  Viewer3dPane（catalog 查询 error/成功态注入——generated units
 *        hook 模块替身）+useProjectId/Scene 模块替身（projectId 直进分支）
 * 输出:  error 态渲染「单元目录未就绪…按单池显示」warning Alert+「重试」
 *        钮；成功态零 Alert（静默面不挂横幅）
 *
 * 形态说明（沿 AssumptionsPanel.test.tsx SSR 先例——零 jsdom 红线；
 *   数据通道=vi.mock 生成 hook 模块返回受控 query 态——零网络面）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { createElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Viewer3dPane } from "./viewer3dPane";

/** 受控态位（vi.hoisted——工厂闭包同源读写）。 */
const mock = vi.hoisted(() => ({
  catalog: {
    isError: false,
    isSuccess: true,
    data: { units: [{ unit_id: "municipal_cass" }] },
  } as { isError: boolean; isSuccess: boolean; data: unknown },
}));

vi.mock("./useProjectId", () => ({
  useProjectId: () => ["proj-f5-d5", vi.fn()],
}));
vi.mock("../features/viewer3d/components/Scene", () => ({
  Scene: () => createElement("div", null, "scene-stub"),
}));
vi.mock("../shared/api/generated/units/units", async (importOriginal) => {
  const actual = await importOriginal<
    Record<string, unknown>
  >();
  return {
    ...actual,
    useListUnitsApiUnitsGet: () => mock.catalog,
  };
});

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderPane(): string {
  return renderToString(
    createElement(
      QueryClientProvider,
      { client: queryClient },
      createElement(Viewer3dPane),
    ),
  );
}

afterEach(() => {
  mock.catalog = {
    isError: false,
    isSuccess: true,
    data: { units: [{ unit_id: "municipal_cass" }] },
  };
});

describe("viewer3dPane 目录失败 Alert（F5 D5）", () => {
  it("catalog error 态：warning Alert 文案+重试钮在场", () => {
    mock.catalog = { isError: true, isSuccess: false, data: undefined };
    const html = renderPane();
    expect(html).toContain("单元目录未就绪");
    expect(html).toContain("池组/分池暂按单池显示");
    // antd Button 两字插空（教训 24）：「重试」渲染为「重 试」
    expect(html).toContain("重 试");
  });

  it("catalog 成功态：零 Alert（静默面不挂横幅——零行为漂移）", () => {
    const html = renderPane();
    expect(html).not.toContain("单元目录未就绪");
  });
});
