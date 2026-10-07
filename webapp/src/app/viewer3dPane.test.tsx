/**
 * viewer3dPane 目录失败 Alert 测试（F5 D5——catalog 未就绪显式提示）；
 * M5 批增补表征锚（m5-20261007 viewer3d 入槽核验批——装配面既有行为
 * 锚定：空态指引/空态 CTA/ErrorBoundary 接线/Scene 挂载通路四用例对
 * HEAD 绿，红先=N/A〔表征面——M3 D6 先例〕）；
 * M5 R1 回炉（门一双审 k1 B0/W1/N4+d1 B0/W2/N7——R1-a：④ lazy
 * import 目标=Scene 模块锚〔vi.mock 工厂位标记〕；R1-c：② 新建项目
 * 文案锚收紧按钮上下文；R1-d：③ html 断言保留加注释面）。
 *
 * 输入:  Viewer3dPane（catalog 查询 error/成功态注入——generated units
 *        hook 模块替身）+useProjectId/Scene 模块替身（projectId 直进分支）
 *        +M5 增补：useProjectId 受控态位（null=空态分支）+projects 生成
 *        hook 受控空表+ErrorBoundary props 捕获薄壳（委托真实件渲染）
 * 输出:  error 态渲染「单元目录未就绪…按单池显示」warning Alert+「重试」
 *        钮；成功态零 Alert（静默面不挂横幅）；M5 表征锚四用例
 *
 * 形态说明（沿 AssumptionsPanel.test.tsx SSR 先例——零 jsdom 红线；
 *   数据通道=vi.mock 生成 hook 模块返回受控 query 态——零网络面）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { createElement, type ComponentType, type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Viewer3dPane } from "./viewer3dPane";

/** 受控态位（vi.hoisted——工厂闭包同源读写；M5 扩 projectId/projects/
 *  boundary 三位——既有 catalog 位零改；R1-a 扩 sceneModuleLoaded 位）。 */
const mock = vi.hoisted(() => ({
  projectId: "proj-f5-d5" as string | null,
  catalog: {
    isError: false,
    isSuccess: true,
    data: { units: [{ unit_id: "municipal_cass" }] },
  } as { isError: boolean; isSuccess: boolean; data: unknown },
  projects: {
    data: [] as unknown,
    isLoading: false,
    isError: false,
  } as { data: unknown; isLoading: boolean; isError: boolean },
  boundary: null as { label: unknown; onRetry?: unknown } | null,
  sceneModuleLoaded: false,
}));

vi.mock("./useProjectId", () => ({
  useProjectId: () => [mock.projectId, vi.fn()],
}));
vi.mock("../features/viewer3d/components/Scene", () => {
  // R1-a：工厂内置位标记——React.lazy 首渲染即调 import()，mock 工厂
  // 必执行（lazy import 目标=Scene 模块的真源锚——装配面 Suspense 包
  // 任意他件则本工厂零执行，④断言红）
  mock.sceneModuleLoaded = true;
  return {
    Scene: () => createElement("div", null, "scene-stub"),
  };
});
// M5 表征锚③：props 捕获薄壳——委托真实 ErrorBoundary 渲染（零行为面）
vi.mock("./ErrorBoundary", async (importOriginal) => {
  const actual = await importOriginal<{
    ErrorBoundary: ComponentType<{
      label: string;
      onRetry?: () => void;
      children?: ReactNode;
    }>;
  }>();
  return {
    ErrorBoundary: (props: {
      label: string;
      onRetry?: () => void;
      children?: ReactNode;
    }) => {
      mock.boundary = props;
      return createElement(actual.ErrorBoundary, props);
    },
  };
});
vi.mock("../shared/api/generated/units/units", async (importOriginal) => {
  const actual = await importOriginal<
    Record<string, unknown>
  >();
  return {
    ...actual,
    useListUnitsApiUnitsGet: () => mock.catalog,
  };
});
// M5 表征锚①②：projects 生成 hook 受控替身（空表 settled=空态分支）
vi.mock("../shared/api/generated/projects/projects", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    useListProjectsApiProjectsGet: () => mock.projects,
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
  mock.projectId = "proj-f5-d5";
  mock.projects = { data: [], isLoading: false, isError: false };
  mock.boundary = null;
  // sceneModuleLoaded 不重置：mock 工厂=每模块恰一次（③已触发则模块
  // 缓存，④不重跑）——位标记是模块级真源锚非逐用例态（探针实证工厂
  // 执行延迟至 renderToString 返回后 ≤200ms）
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

  it("回炉 W6：后台重取失败但缓存 data 在场（池组照常渲染）→ 零误报", () => {
    mock.catalog = {
      isError: true,
      isSuccess: false,
      data: { units: [{ unit_id: "municipal_cass" }] },
    };
    const html = renderPane();
    expect(html).not.toContain("单元目录未就绪");
  });

  it("回炉 W6：成功而目录空表（units=[]）→ 挂 Alert（真实病态）", () => {
    mock.catalog = { isError: false, isSuccess: true, data: { units: [] } };
    const html = renderPane();
    expect(html).toContain("单元目录未就绪");
  });
});

describe("viewer3dPane 表征锚（M5 批——入槽装配面既有行为锚定）", () => {
  it("M5①空态指引：projectId null+projects 空表 settled→引导句+EMPTY_GUIDE 在场", () => {
    mock.projectId = null;
    const html = renderPane();
    expect(html).toContain("请选择要加载三维场景的项目：");
    expect(html).toContain(
      "暂无项目：点击「新建项目」创建空白项目或导入已有项目 JSON 文件",
    );
  });

  it("M5②空态 CTA：「新建项目」主钮在场（antd Button 四字无插空）", () => {
    mock.projectId = null;
    const html = renderPane();
    // R1-c：文案锚收紧按钮上下文（>新建项目<=标签包裹面——EMPTY_GUIDE
    // 指引句内同字串为裸文本不满足；四字无插空=antd 仅两字插空规则）
    expect(html).toContain(">新建项目<");
    expect(html).toContain("ant-btn-primary");
  });

  it("M5③ErrorBoundary 接线捕获：label=三维视图+onRetry 为函数（R1 同 URL 重建接线在场——只锚接线不断言语义有效性）", () => {
    const html = renderPane();
    // R1-d：接线证据=下方 props 捕获为准；本条 html 断言仅证装载分支
    // 共享面（lazy 挂起→Suspense fallback 在场），与④共用非独立接线证
    expect(html).toContain("三维视图加载中…");
    expect(mock.boundary?.label).toBe("三维视图");
    expect(typeof mock.boundary?.onRetry).toBe("function");
  });

  it("M5④Scene 挂载通路：projectId 非空→lazy Scene 装载分支在场+空态面缺席", async () => {
    const html = renderPane();
    // React.lazy 在 renderToString 必挂起（SSR 不支持 Suspense 懒装载
    // 子树中止——探针实证），锚=Suspense fallback「三维视图加载中…」
    // 在场+空态指引缺席=分支选择锚（既有隐式面显式化）
    expect(html).toContain("三维视图加载中…");
    expect(html).not.toContain("请选择要加载三维场景的项目：");
    // R1-a：lazy import 目标=Scene 模块真源锚（mock 工厂位标记——
    // 探针实证工厂执行延迟至 renderToString 返回后 ≤200ms，vi.waitFor
    // 轮询保稳健；工厂=每模块恰一次，本用例直进分支自触发〔隔离跑
    // 亦成立——模块级锚非用例间依赖〕）
    await vi.waitFor(() => expect(mock.sceneModuleLoaded).toBe(true), {
      timeout: 3000,
    });
  });
});
