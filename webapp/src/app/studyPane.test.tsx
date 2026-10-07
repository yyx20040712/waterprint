/**
 * @vitest-environment jsdom
 *
 * 方案研究子面测试（M6 批 2026-10-07——studyPane 内容实装：双轨初值+四挂载
 * 门+深链回填+联合段窄化门+TASK_EVENT 双轨重读+useTaskFeed×2 终态自刷+
 * 切项目重置+handleApplied 表源不卸载）。
 *
 * 输入:  StudyPane（URL 经 history.replaceState 摆位——真 useProjectId/真
 *        projectParam 消费；vi.mock 边界沿 seatTaskPage 纪律=feature api
 *        模块面〔useTaskFeed/useProjectUnits/useSensitivityQuery〕+generated
 *        面按 taskId 分流的 status 桩与 solutions/raw/apply 桩，禁 mock
 *        react-query 内部/antd——SolutionsTable/JointSolutionsPanel/
 *        RankingControls/DiagnosisPanel 原件真渲染；三图 echarts 壳以叶子
 *        stub 替〔jsdom 无 canvas——测验面在 studyPane 接线非图内；
 *        TornadoChart stub 透传 sensitivityIssue 供⑦断言——裁量申报在批档〕）
 * 输出:  ①空项目文案②双段引导逐字③表+排序控件在场④无解诊断⑤载荷缺失
 *        ⑥取数错误⑦联合面板+sensitivityIssue 透传⑧failed 文案⑨窄化非法
 *        ⑩TASK_EVENT 双轨重读⑪handleApplied=writeTaskParam+派发+表源
 *        不卸载⑫切项目双轨重置⑬useTaskFeed×2 终态=本轨键+联合追加
 *        sensitivity 键+不派发；⑭task-only apply 后表源保持+⑮二次枚举
 *        单元重置（R1 回炉批 W1/W2 锚——applyVariables mock 小扩在案）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { StudyPane } from "./studyPane";
import { PROJECT_EVENT, TASK_EVENT } from "../shared/events";

// P5 R3（2B6 门一复审 W-1 处置）：用例级超时预算——多等待点用例在负载态
// 各点慢成功（单点不超 3000）串行叠加可越 vitest 用例级默认 5000（最劣 ⑮
// 三 findBy 3×3000=9000+渲染/事件开销≈1000）→用例级超时红（非单点超时）；
// 15000=覆盖上限 1.4x+默认值 3x（JointSolutionsPanel 文件级 testTimeout 先例同制）。
vi.setConfig({ testTimeout: 15000 });

// jsdom 缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
// antd Table sticky/响应式面消费 matchMedia（jsdom 缺省无——恒不匹配桩）
if (typeof window.matchMedia !== "function") {
  window.matchMedia = (query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: () => {}, removeListener: () => {},
    addEventListener: () => {}, removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

/** 查询桩形态（react-query v5 常读字段族——paneDomainGate D4 口径）。 */
type QueryStub = {
  data: unknown; isError: boolean; error: unknown;
  isPending: boolean; isLoading: boolean; isFetching: boolean;
  status: string; refetch: () => Promise<unknown>;
};

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => {
  const idle = (): QueryStub => ({
    data: undefined, isError: false, error: null,
    isPending: true, isLoading: true, isFetching: true,
    status: "pending", refetch: () => Promise.resolve({}),
  });
  return {
    idle,
    statusById: new Map<string, QueryStub>(),
    solutions: idle(),
    projectRaw: idle(),
    units: idle(),
    sensitivity: idle(),
    // R1-c ⑮ 断言面：apply mutate 收到的 variables 实录（mock 小扩）
    applyVariables: [] as unknown[],
    feedCalls: [] as { taskId: string | null; onTerminal: ((state: string) => void) | undefined }[],
  };
});

vi.mock("../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: (taskId: string | null, onTerminal?: (state: string) => void) => {
    gate.feedCalls.push({ taskId, onTerminal });
    return null;
  },
}));
vi.mock("../features/solutions/api/useProjectUnits", () => ({
  useProjectUnits: () => gate.units,
}));
vi.mock("../features/solutions/api/useSensitivityQuery", () => ({
  useSensitivityQuery: () => gate.sensitivity,
}));
vi.mock("../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: (taskId: string | null) =>
    (taskId !== null && gate.statusById.get(taskId)) || gate.idle(),
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet: () => gate.solutions,
  // 同步 onSuccess（ApplyOutcome 最小形——handleApplied 接线可测面）
  useApplySolutionApiCalcSolutionsApplyPost: (options: {
    mutation?: { onSuccess?: (outcome: unknown, variables: unknown, context: unknown) => void };
  }) => ({
    mutate: (variables: unknown) => {
      gate.applyVariables.push(variables);
      options?.mutation?.onSuccess?.(
        { recalc_task_id: "t-recalc", new_hash: "hash1234567890", design_changed: true },
        variables,
        undefined,
      );
    },
    isPending: false, isError: false, error: null,
  }),
}));
vi.mock("../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => gate.projectRaw,
}));
vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => gate.idle(),
}));
// 三图 echarts 壳 stub（叶子组件替身——接线面以外零承载）
vi.mock("../features/solutions/components/ParetoChart", () => ({
  ParetoChart: () => <div>pareto-stub</div>,
}));
vi.mock("../features/solutions/components/ParallelCoordsChart", () => ({
  ParallelCoordsChart: () => <div>parallel-stub</div>,
}));
vi.mock("../features/solutions/components/TornadoChart", () => ({
  TornadoChart: ({ sensitivityIssue }: { sensitivityIssue?: string | null }) => (
    <div>tornado-stub:{sensitivityIssue ?? ""}</div>
  ),
}));

/** 成功/错误态查询桩。 */
function successState(data: unknown): QueryStub {
  return { ...gate.idle(), data, isPending: false, isLoading: false, isFetching: false, status: "success" };
}
function errorState(error: Error): QueryStub {
  return { ...gate.idle(), isError: true, error, isPending: false, isLoading: false, isFetching: false, status: "error" };
}

/** 单单元枚举 done 快照（result 载荷可覆写）。 */
function enumDone(taskId: string, result: Record<string, unknown> = {}): QueryStub {
  return successState({
    task_id: taskId, kind: "enumerate", state: "done",
    result: {
      unit_id: "u1", design_hash: "dh-1", project_id: "p1",
      grid_fields: [{ key: "n", dim: "DIMENSIONLESS", label_zh: "池数（格）" }],
      dim_fields: [], feasible_count: 5, ...result,
    },
  });
}

/** 方案分页窄化产物形态（SolutionPageView——mock 面绕过 select 直供）。 */
const SOLUTIONS_PAGE = {
  task_id: "e1", page: 1, size: 50, total: 5, sort: "margin_min",
  columns: ["n", "margin_min", "nan_flag", "condition_key"],
  rows: [{ n: 6, margin_min: 0.22, nan_flag: false, condition_key: "baseline:design" }],
};

/** 联合枚举 combo 夹具（四真键——jointView 白名单内）。 */
function comboFixture(score: number): Record<string, unknown> {
  return {
    params: { unitA: { n: 2 }, unitB: { n: 4 } },
    feasible: true, sensitivity_degraded: false, failed_conditions: [],
    metrics: {
      cost_opex_yuan_a: 100, power_total_kwh_d: 50,
      carbon_intensity_kgco2e_m3: 0.5, cost_capex_yuan: 1234567,
    },
    score,
  };
}

/** 联合枚举 done 快照（result 载荷可覆写）。 */
function jointDone(taskId: string, result: unknown): QueryStub {
  return successState({ task_id: taskId, kind: "joint_enumerate", state: "done", result });
}

const NO_ENUM_HINT =
  "暂无单单元枚举任务——提交入口在顶部「提交计算」命令带；完成后此处展示方案表（margin_min 降序）。";
const NO_JOINT_HINT =
  "暂无联合枚举结果——提交入口在顶部「提交计算」命令带（联合枚举）；完成后此处展示方案比选表与三图。";

/** URL 摆位+每用例新 QueryClient（invalidate 经 spy 观测）。 */
function renderStudyPane(search: string) {
  window.history.replaceState(null, "", search === "" ? "/" : `/?${search}`);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidateSpy = vi.spyOn(client, "invalidateQueries");
  render(<StudyPane />, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
  return { invalidateSpy };
}

beforeEach(() => {
  gate.statusById.clear();
  gate.solutions = gate.idle();
  gate.projectRaw = gate.idle();
  gate.units = gate.idle();
  gate.sensitivity = gate.idle();
  gate.feedCalls.length = 0;
  gate.applyVariables.length = 0;
  window.history.replaceState(null, "", "/");
});
afterEach(cleanup);

describe("StudyPane 空态与引导（M6 D1 段A/B 空源面）", () => {
  it("①projectId null→空项目文案在场（studioPane D7 措辞单源）", () => {
    renderStudyPane("");
    expect(screen.getByText("尚未选择项目——请先在画布槽选择项目")).toBeTruthy();
  });

  it("②无 enum/task→双段引导文案逐字（表源轨/联合轨空源）", () => {
    renderStudyPane("project=p1");
    expect(screen.getByText(NO_ENUM_HINT)).toBeTruthy();
    expect(screen.getByText(NO_JOINT_HINT)).toBeTruthy();
  });
});

describe("StudyPane 段A 方案浏览（单单元枚举——四挂载门）", () => {
  it("③?enum= done+feasible>0→RankingControls+SolutionsTable 在场（排序控件+分页行）", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = successState(SOLUTIONS_PAGE);
    renderStudyPane("project=p1&enum=e1");
    expect(screen.getByText("排序（降序）：")).toBeTruthy();
    // 列头文案在表头与排序下拉选项两处复用（gridFields 单源）——多重匹配合规
    expect(screen.getAllByText("池数（格）").length).toBeGreaterThan(0);
    expect(await screen.findByText("共 5 行", {}, { timeout: 3000 })).toBeTruthy(); // P5 R1（2B6）：findBy 族显式超时——waitFor 族同制同值同论证
    expect(screen.queryByText(/无解诊断/)).toBeNull();
  });

  it("④done+feasible=0→DiagnosisPanel 在场（noSolutions=合法终态）", () => {
    gate.statusById.set(
      "e4",
      enumDone("e4", { feasible_count: 0, diagnosis: { minimal_conflicts: [["n"]], fail_counts: { n: 8 }, suggestions: [] } }),
    );
    renderStudyPane("project=p1&enum=e4");
    expect(screen.getByText(/无解诊断（枚举完成但可行方案数为 0）/)).toBeTruthy();
    expect(screen.queryByText("排序（降序）：")).toBeNull();
  });

  it("⑤done+feasible 缺失→载荷缺失警示在场（R7 防御面）", () => {
    gate.statusById.set("e5", enumDone("e5", { feasible_count: undefined }));
    renderStudyPane("project=p1&enum=e5");
    expect(
      screen.getByText("枚举已完成但结果载荷缺失（feasible_count）——请重新提交枚举。"),
    ).toBeTruthy();
  });

  it("⑥solutionsQuery error→「方案取数失败：」在场", () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = errorState(new Error("boom-502"));
    renderStudyPane("project=p1&enum=e1");
    expect(screen.getByText(/方案取数失败：boom-502/)).toBeTruthy();
  });
});

describe("StudyPane 段B 联合枚举（方案比选）", () => {
  it("⑦?task= joint done→JointSolutionsPanel 在场（combos 容器+sensitivityIssue 透传）", async () => {
    gate.statusById.set(
      "t1",
      jointDone("t1", { unit_ids: ["unitA", "unitB"], diagnosis: null, combos: [comboFixture(0.9), comboFixture(1.1)] }),
    );
    gate.sensitivity = errorState(new Error("敏感性报告损坏"));
    renderStudyPane("project=p1&task=t1");
    expect(screen.getByText(/共 2 个可行组合/)).toBeTruthy();
    // 三图 lazy+Suspense（Tabs forceRender）——异步装载后 stub 透传 issue 断言
    expect(await screen.findByText(/tornado-stub:敏感性报告损坏/, {}, { timeout: 3000 })).toBeTruthy(); // P5 R1（2B6）：findBy 族显式超时——lazy 装载链（waitFor 族同制同值）
    // 表源轨 task 兜底初值=t1：kind 门滤（非 enumerate）→方案表静默
    expect(screen.queryByText("排序（降序）：")).toBeNull();
  });

  it("⑧joint failed→jointTaskNotice 文案在场（批6f 终态分派）", () => {
    gate.statusById.set(
      "t8",
      successState({ task_id: "t8", kind: "joint_enumerate", state: "failed", error_type: "SolveFailedError", error: "求解不收敛", result: null }),
    );
    renderStudyPane("project=p1&task=t8");
    expect(screen.getByText(/联合枚举任务失败：/)).toBeTruthy();
    expect(screen.getByText(/可重新提交/)).toBeTruthy();
  });

  it("⑨joint done 但载荷非法→「联合枚举结果载荷非法：」在场（窄化 try-catch）", () => {
    gate.statusById.set("t9", jointDone("t9", { combos: 42 }));
    renderStudyPane("project=p1&task=t9");
    expect(screen.getByText(/联合枚举结果载荷非法：/)).toBeTruthy();
  });
});

describe("StudyPane 双轨运行期（TASK_EVENT 重读+终态自刷+切项目）", () => {
  it("⑩TASK_EVENT→URL 重读双轨更新：新 task 接管联合轨（表源轨 enum 键不动）", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = successState(SOLUTIONS_PAGE);
    gate.statusById.set(
      "t1",
      jointDone("t1", { unit_ids: ["unitA", "unitB"], diagnosis: null, combos: [comboFixture(0.9), comboFixture(1.1)] }),
    );
    gate.statusById.set(
      "t2",
      successState({ task_id: "t2", kind: "joint_enumerate", state: "failed", error_type: "SolveFailedError", error: "重算失败", result: null }),
    );
    renderStudyPane("project=p1&task=t1&enum=e1");
    expect(screen.getByText(/共 2 个可行组合/)).toBeTruthy();
    window.history.replaceState(null, "", "/?project=p1&task=t2&enum=e1");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t2" }));
    // P5 稳态化（2B6）：满载 CPU 争用下默认 1s 超时假红——显式 timeout 3000
    // （viewer3dPane.test L195 仓内先例；全 mock 同步面隔离实录 <100ms，3s=30x 余量）
    await waitFor(() => {
      expect(screen.getByText(/联合枚举任务失败：/)).toBeTruthy();
    }, { timeout: 3000 });
    expect(screen.getByText("共 5 行")).toBeTruthy(); // 表源轨 enum 键优先不卸载
  });

  it("⑪handleApplied→writeTaskParam+TASK_EVENT 派发+表源不卸载（apply 后旧行保留）", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = successState(SOLUTIONS_PAGE);
    gate.units = successState([{ unitId: "u1", kind: null }]);
    gate.projectRaw = successState({
      metadata: { content_hash: "dh-1" },
      design: { nodes: { u1: { kind: "municipal_aao" } } },
    });
    const { invalidateSpy } = renderStudyPane("project=p1&enum=e1");
    let dispatched = 0;
    const onDispatch = () => {
      dispatched += 1;
    };
    window.addEventListener(TASK_EVENT, onDispatch);
    try {
      // sticky Table 体行异步落位——findBy 等待；antd Button 两中文字符自动
      // 插空格（「应用」→「应 用」）——空白容忍正则
      // P5 R4（2B6 ⑪ click-race 同窗收口——d1 裁定授权）：瞬态 disabled 窗口
      // 前置等待（⑮ 根因同窗：R1-b 表源切换两 commit 间 enumeratedUnitId=null
      // →应用钮恒渲染瞬态禁用，窗内点击被吞——新增 enabled 前置断言=收紧非弱化）
      await waitFor(() => {
        expect(screen.getAllByText(/应\s*用/)[0]?.closest("button")?.disabled).toBe(false);
      }, { timeout: 3000 });
      fireEvent.click(await screen.findByText(/应\s*用/, {}, { timeout: 3000 })); // P5 R1（2B6）：findBy 族显式超时——waitFor 族同制同值同论证
    } finally {
      window.removeEventListener(TASK_EVENT, onDispatch);
    }
    await waitFor(() => {
      expect(window.location.search).toContain("task=t-recalc");
    }, { timeout: 3000 }); // P5 稳态化（2B6）：同上——满载假红族显式超时
    expect(window.location.search).toContain("enum=e1"); // enum 键不动
    expect(dispatched).toBe(1); // TASK_EVENT 恰一派发
    expect(screen.getByText("共 5 行")).toBeTruthy(); // 表源不卸载
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["/api/projects/p1"], // ApplySolutionButton read 键失效（原件行为）
    });
  });

  it("⑫切项目→双轨重置（引导文案回归——prevProject 初挂载早退保深链初值）", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = successState(SOLUTIONS_PAGE);
    gate.statusById.set(
      "t1",
      jointDone("t1", { unit_ids: ["unitA", "unitB"], diagnosis: null, combos: [comboFixture(0.9)] }),
    );
    renderStudyPane("project=p1&task=t1&enum=e1");
    expect(screen.getByText("共 5 行")).toBeTruthy();
    window.history.replaceState(null, "", "/?project=p2");
    window.dispatchEvent(new CustomEvent(PROJECT_EVENT, { detail: "p2" }));
    await waitFor(() => {
      expect(screen.getByText(NO_ENUM_HINT)).toBeTruthy();
    }, { timeout: 3000 }); // P5 稳态化（2B6）：同上——满载假红族显式超时
    expect(screen.getByText(NO_JOINT_HINT)).toBeTruthy();
  });

  it("⑬useTaskFeed×2 终态自刷：本轨键失效+联合实例追加 sensitivity 键+不派发 TASK_EVENT", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.statusById.set(
      "t1",
      jointDone("t1", { unit_ids: ["unitA"], diagnosis: null, combos: [comboFixture(0.9)] }),
    );
    const { invalidateSpy } = renderStudyPane("project=p1&task=t1&enum=e1");
    // 两实例（表源/联合各一——视图/连接态零消费=组件不炸即证）
    const lastEnumFeed = [...gate.feedCalls].reverse().find((c) => c.taskId === "e1");
    const lastJointFeed = [...gate.feedCalls].reverse().find((c) => c.taskId === "t1");
    expect(lastEnumFeed?.onTerminal).toBeTypeOf("function");
    expect(lastJointFeed?.onTerminal).toBeTypeOf("function");
    let reDispatched = 0;
    const onReDispatch = () => {
      reDispatched += 1;
    };
    window.addEventListener(TASK_EVENT, onReDispatch);
    try {
      (lastEnumFeed?.onTerminal as (state: string) => void)("done");
      (lastJointFeed?.onTerminal as (state: string) => void)("done");
    } finally {
      window.removeEventListener(TASK_EVENT, onReDispatch);
    }
    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["/api/calc/tasks/e1"] });
    }, { timeout: 3000 }); // P5 稳态化（2B6）：同上——满载假红族显式超时
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["/api/calc/tasks/t1"] });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["/api/calc/sensitivity/p1"], // 批6e W5 复刻（联合实例追加）
    });
    expect(reDispatched).toBe(0); // study 不派发 TASK_EVENT（席位职责单一）
  });

  it("⑭task-only URL apply 后 TASK_EVENT→表源保持（enum 键缺席不回落——W1 锚）", async () => {
    gate.statusById.set("e1", enumDone("e1"));
    gate.solutions = successState(SOLUTIONS_PAGE);
    renderStudyPane("project=p1&task=e1");
    expect(await screen.findByText("共 5 行", {}, { timeout: 3000 })).toBeTruthy(); // task 键兜底初值=e1；P5 R1（2B6）：findBy 族显式超时——waitFor 族同制同值
    // 模拟 apply 后 writeTaskParam(recalc)：URL 仅 task 键（enum 键缺席——
    // 不经真按钮，直接验证 TASK_EVENT handler 面）
    window.history.replaceState(null, "", "/?project=p1&task=t-recalc");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t-recalc" }));
    await waitFor(() => {
      // 表源保持 e1 不漂移（R1-a 前：handler 回落 task 键→表源=t-recalc
      // →kind 门滤→表静默消失且 NO_ENUM_HINT 因任务键非 null 不显）
      expect(screen.getByText("共 5 行")).toBeTruthy();
    }, { timeout: 3000 }); // P5 稳态化（2B6）：同上——满载假红族显式超时
    expect(screen.getByText("排序（降序）：")).toBeTruthy();
  });

  it("⑮二次枚举换单元→应用目标重置新任务单元（u1→u2——W2 锚）", async () => {
    gate.statusById.set("e1", enumDone("e1")); // result.unit_id="u1"（回填源）
    // enumDone 夹具覆写对象展开在 result 内层→unit_id:"u2" 达成
    gate.statusById.set("e2", enumDone("e2", { unit_id: "u2" }));
    gate.solutions = successState(SOLUTIONS_PAGE);
    // 双单元均就绪（红先态 u1 钉死也要可点——红=实收 u1）
    gate.units = successState([
      { unitId: "u1", kind: null },
      { unitId: "u2", kind: null },
    ]);
    gate.projectRaw = successState({
      metadata: { content_hash: "dh-1" },
      design: {
        nodes: { u1: { kind: "municipal_aao" }, u2: { kind: "municipal_aao" } },
      },
    });
    renderStudyPane("project=p1&enum=e1");
    expect(await screen.findByText("共 5 行", {}, { timeout: 3000 })).toBeTruthy(); // 深链回填 u1；P5 R1（2B6）：findBy 族显式超时——已知假红成员⑮所在族闭合
    // 模拟二次枚举提交写双键（enum+task）；分页换 total=6 供新表在场区分
    gate.solutions = successState({ ...SOLUTIONS_PAGE, total: 6 });
    window.history.replaceState(null, "", "/?project=p1&enum=e2&task=e2");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "e2" }));
    expect(await screen.findByText("共 6 行", {}, { timeout: 3000 })).toBeTruthy(); // 新表在场；P5 R1（2B6）：findBy 族显式超时——已知假红成员⑮所在族闭合
    // P5 R4（2B6 ⑮ click-race 根因收口——d1 裁定授权+DIAG 实证补强）：瞬态
    // disabled 为「双窗」形态（DIAG 捕获：enabled-wait 可在 u1 旧窗即过，
    // 点击落在 R1-b reset 置 null 窗被吞〔antd onClick guard〕→零 mutate→
    // TypeError）——act 静默让渡=效应链（reset null→commit→refix u2→commit）
    // 确定性终态化（u2 终态无再翻转），再 enabled 前置断言（收紧非弱化）+点击。
    await act(async () => {});
    await waitFor(() => {
      expect(screen.getAllByText(/应\s*用/)[0]?.closest("button")?.disabled).toBe(false);
    }, { timeout: 3000 });
    fireEvent.click(await screen.findByText(/应\s*用/, {}, { timeout: 3000 }));
    // 应用载荷 unitId=enumeratedUnitId 透传（R1-b 前：跨任务钉死 u1）
    const last = gate.applyVariables[gate.applyVariables.length - 1] as {
      data: { unit_id: string };
    };
    expect(last.data.unit_id).toBe("u2");
  });
});
