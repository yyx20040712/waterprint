/**
 * @vitest-environment jsdom
 *
 * App 级 LazyPane 懒实例提升测试（rootfix-20261008——UF-67 根治批：lazy
 * 实例按 load WeakMap 记忆化提升出渲染通道——remount 复调 ctor 消除+显式
 * 重试换新实例语义保持）。
 *
 * 沿革：UF-66 批登记 jsdom 测试面盲区（mock import 无模块图语义——
 * errorBoundary.test 全绿与此不冲突）；UF-67 批定位中断源=App.tsx LazyPane
 * useState(() => lazy(load)) lazy 实例生于渲染通道（诊断档
 * .workflow/uf67-20261008/diag-uf67-summary.md——三证链正面仪器化/scratch
 * 对照/反事实记忆化 E1c）；本批=rootfix 根治实施+本文件 App 级红先锚。
 *
 * 红先声明：用例①对 HEAD〔无记忆化〕跑红——HEAD 形态下失败首挂入
 * 「新 lazy→再 ctor」复调链（vitest mock 工厂失败无缓存=每次动态
 * import 复调桩；jsdom/HEAD 下 React 重试节流使复调有界——首挂 1+
 * 复挂 2=3，降级最终提交）→ 红=remount 后计数断言红（AssertionError:
 * expected 3 to be 1——红跑实录 .workflow/rootfix-20261008/
 * red-run-rootfix.txt；笔4 r1 勘正：原「重试环饱和事件环、alert 永不
 * 提交→超时红」预言句与实录不符，改述实录口径〔k1-W1——主控红跑
 * 日志亲读裁决〕）；桩内置风暴遥测（复调达 5/10 次打点——健康形态
 * 单用例峰值≤3〔表冷首挂 1+双重试 2〕零输出，门限 5 保持风暴专属
 * 判别力〔d1-N2 笔4〕）。
 * 实施后同用例转绿=记忆化实例拒绝态直读→ErrorBoundary 即时降级提交。
 *
 * 输入:  App 整树 jsdom 挂载（深链 ?tab=studio.drawings 经
 *        history.replaceState 摆位——aiSeat.test URL 先例）；vi.mock 边界
 *        沿 paneDomainGate 纪律=feature api/生成 hook 模块面无害空态
 *        （禁 mock react-query 内部/antd）+懒装载 chunk 面计次拒绝桩
 *        （drawingsPane/siteplanPane——@vitest/mocker ManualMockedModule
 *        .resolve 工厂失败不缓存=每次动态 import 复调，桩计数即 ctor
 *        复调计数）+canvasPane 静态桩（xyflow/three 重链评估隔离——
 *        canvas 槽非判据面永不激活）；App 模块单次加载跨用例共享
 *        （记忆表 WeakMap/loaders 模块级单例跨用例持久——①~④断言取
 *        相对差值零序依赖〔表冷/表热两态皆绿——笔4 r1 k1-W1/d1-N3〕；
 *        ③仍置末位〔翻桩缓存面〕）
 * 输出:  断言组四用例：①remount 不再复调 ctor（核心红先锚：首挂降级
 *        在场→unmount→整树重挂→桩计数不变+降级即时复现）；②显式重试
 *        语义保持（降级后点「重试」→桩复调恰+1+边界复位瞬态+再降级
 *        在场——errorBoundary.test 重试交互先例）；③重试换新实例入表
 *        形锁定（翻桩拒后成→重试恢复→remount 取最新已解析实例不回归
 *        降级——rootfix 择稳判据「重试后再 remount 不回归」形态锁：
 *        「不入表」形态下本用例红=remount 回退旧拒绝态实例降级复现）；
 *        ④多槽独立性（siteplan 槽独立失败降级——drawings 记忆项零扰动
 *        =记忆表按 load 分键）。
 *
 * 规格说明（rootfix-20261008 简报 D1/D2）：
 *   - 记忆表=模块级 WeakMap<load, lazy 实例>（load 均模块级单例——四槽
 *     loader+studio 五子面 loader）跨 remount/跨组件树生命周期恒同实例：
 *     payload 已定局（Rejected/Resolved）即直读不再复调 ctor——「ctor→
 *     import 拒绝→调度重试→初始化器重跑→新 lazy→再 ctor」循环引擎拆除；
 *   - onRetry=直接构造新 lazy+入表（现行语义零变：显式用户动作换新实例
 *     破失败占位+边界复位；入表=重试后 remount 取最新实例不回退旧拒绝态）；
 *   - jsdom 无资源时序→lazyPaneLoader capturedUrl=null→无 bust 面——桩
 *     计数与 R1 冷却零耦合（纯 React 层行为面）；
 *   - 用例序注记：③翻桩成功后 mock 模块被缓存（工厂成功即缓存——后续
 *     import 零工厂复调），置末位；①②④桩恒拒无缓存面且断言序独立
 *     （相对差值形——表冷〔本用例首构造 +1〕/表热〔前置用例已入表
 *     +0〕两态皆绿）。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面：
// antd Tree/浮层挂载期消费 ResizeObserver；ChatPanel 底部锚滚动 effect
// 消费 Element.scrollIntoView——jsdom 两 API 均缺席，aiSeat.test 同款）。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
if (typeof Element.prototype.scrollIntoView !== "function") {
  Element.prototype.scrollIntoView = () => {};
}

/** 计次桩态（vi.hoisted——vi.mock 工厂闭包同源读写；imports=动态 import
 *  即 ctor 复调计数；resolveAt=翻桩阈值〔null=恒拒；imports≥该值成功〕）。 */
const paneStubs = vi.hoisted(() => ({
  drawings: { imports: 0, resolveAt: null as number | null },
  siteplan: { imports: 0 },
}));

/** 取数/突变 hook 无害空态（vi.hoisted——vi.mock 工厂内可引用面；
 *  react-query v5 常读字段族沿 paneDomainGate D4 口径补齐）。 */
const apiIdle = vi.hoisted(() => ({
  query: () => ({
    data: undefined,
    isError: false,
    error: null,
    isPending: true,
    isLoading: true,
    isFetching: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  }),
  mutation: () => ({
    mutate: () => {},
    mutateAsync: () => Promise.resolve({}),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    reset: () => {},
  }),
}));

vi.mock("../features/aiconnect/api/useAiConnection", () => ({
  useAiConnection: () => ({
    statusQuery: {
      data: undefined,
      isError: false,
      error: null,
      isLoading: true,
      isPending: true,
      status: "pending",
    },
    setupMutation: apiIdle.mutation(),
  }),
}));
vi.mock("../features/ai_chat/api/useAiChat", () => ({
  CHAT_HISTORY_KEY: (id: string) => ["/api/ai/sessions", id, "messages"],
  useChatSessions: () => apiIdle.query(),
  useChatHistory: () => apiIdle.query(),
  useSendChatMessage: () => apiIdle.mutation(),
}));
vi.mock("../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: () => null,
}));
vi.mock("../features/opsdebug/api/useOpsChainQuery", () => ({
  useOpsChainQuery: () => apiIdle.query(),
}));
vi.mock("../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => apiIdle.query(),
  useCancelTaskApiCalcTasksTaskIdCancelPost: () => apiIdle.mutation(),
  useRunCalculationApiCalcRunPost: () => apiIdle.mutation(),
  useRunEnumerationApiCalcEnumeratePost: () => apiIdle.mutation(),
}));
vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => apiIdle.query(),
  useListConstraintsApiConstraintsGet: () => apiIdle.query(),
}));
vi.mock("../shared/api/generated/projects/projects", () => ({
  getListProjectsApiProjectsGetQueryKey: () => ["/api/projects"],
  useListProjectsApiProjectsGet: () => apiIdle.query(),
  useCreateProjectApiProjectsPost: () => apiIdle.mutation(),
  useReadProjectApiProjectsProjectIdGet: () => apiIdle.query(),
  useSaveProjectApiProjectsProjectIdPut: () => apiIdle.mutation(),
  useValidateProjectApiProjectsProjectIdValidatePost: () => apiIdle.mutation(),
  useCopyProjectApiProjectsProjectIdCopyPost: () => apiIdle.mutation(),
  useRenameProjectApiProjectsProjectIdRenamePost: () => apiIdle.mutation(),
  useDeleteProjectApiProjectsProjectIdDelete: () => apiIdle.mutation(),
}));
vi.mock("../shared/api/generated/solution/solution", () => ({
  useRunJointEnumerationApiSolutionJointEnumeratePost: () => apiIdle.mutation(),
}));
// canvas 槽静态桩（xyflow/three 重链评估隔离——canvas 槽非判据面永不激活）
vi.mock("./canvasPane", () => ({
  CanvasPane: () => <div>CANVAS-STUB</div>,
}));
// 计次拒绝桩（核心观测面——工厂失败不缓存=每次动态 import 复调计数）
vi.mock("./drawingsPane", () => {
  paneStubs.drawings.imports += 1;
  if (paneStubs.drawings.imports === 5 || paneStubs.drawings.imports === 10) {
    console.log(
      `[drawingsPane 桩] 动态 import 已被复调 ${paneStubs.drawings.imports} 次——渲染通道 ctor 复调风暴形态（UF-67）`,
    );
  }
  if (
    paneStubs.drawings.resolveAt !== null &&
    paneStubs.drawings.imports >= paneStubs.drawings.resolveAt
  ) {
    return { DrawingsPane: () => <div>DRAWINGS-OK</div> };
  }
  return Promise.reject(new Error("stub: Loading chunk drawingsPane failed."));
});
vi.mock("./siteplanPane", () => {
  paneStubs.siteplan.imports += 1;
  return Promise.reject(new Error("stub: Loading chunk siteplanPane failed."));
});

/** 降级面/交互锚（ErrorBoundary 主面前缀——分级无关稳定锚）。 */
const ALERT_DRAWINGS = "面板异常（图纸预览）";
const ALERT_SITEPLAN = "面板异常（厂区布置）";
const RETRY = "重试";

/** App 挂载（深链摆位——initialTarget 真消费；search 不带前导 ?——
 *  aiSeat.test URL 先例）。App 经文件顶静态 import（vi.mock 提升 hoist
 *  先于其求值生效；App 静态图重评估 ~11s 级入文件 import 相位——免占
 *  用例/hook 超时预算；记忆表/loaders 模块级单例跨用例持久，本文件不
 *  做 resetModules）。 */
function mountApp(search = "tab=studio.drawings") {
  window.history.replaceState(null, "", search === "" ? "/" : `/?${search}`);
  return render(<App />);
}

beforeEach(() => {
  paneStubs.drawings.imports = 0;
  paneStubs.drawings.resolveAt = null;
  paneStubs.siteplan.imports = 0;
  window.history.replaceState(null, "", "/");
});
afterEach(cleanup);

describe("LazyPane 懒实例提升（rootfix-20261008——remount 复调 ctor 消除）", () => {
  it("①remount 不再复调 ctor（核心红先锚）：首挂降级在场→整树重挂→桩计数不变+降级即时复现", async () => {
    // 序独立化（笔4 r1 k1-W1/d1-N3）：相对差值形——表冷（本用例首构造）
    // +1 / 表热（前置用例已入表）+0 两态皆过
    const base = paneStubs.drawings.imports;
    const first = mountApp();
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    expect(paneStubs.drawings.imports - base).toBeLessThanOrEqual(1);
    // 核心红先锚（强断言不弱化）：remount 零复调——HEAD 下复挂 +2≠before 仍红
    const before = paneStubs.drawings.imports;
    first.unmount();
    const second = mountApp();
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    expect(paneStubs.drawings.imports).toBe(before);
  }, 20000);

  it("②显式重试语义保持：降级后点「重试」→桩复调恰+1+边界复位瞬态→再降级在场", async () => {
    mountApp();
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    const baseline = paneStubs.drawings.imports;
    fireEvent.click(screen.getByRole("button", { name: RETRY }));
    // 边界复位瞬态：重试批内换新 lazy 挂起→Suspense fallback（alert 退场）
    expect(screen.queryByText(ALERT_DRAWINGS)).toBeNull();
    // 新实例再拒绝→再降级在场（重试=新 lazy=ctor 复调恰一次）
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    expect(paneStubs.drawings.imports).toBe(baseline + 1);
  }, 20000);

  it("④多槽独立性：siteplan 槽独立失败降级——drawings 记忆项零扰动（记忆表按 load 分键）", async () => {
    mountApp();
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    const drawingsBaseline = paneStubs.drawings.imports;
    fireEvent.click(screen.getByRole("tab", { name: "厂区布置" }));
    await screen.findByText(ALERT_SITEPLAN, {}, { timeout: 5000 });
    expect(paneStubs.siteplan.imports).toBe(1);
    expect(paneStubs.drawings.imports).toBe(drawingsBaseline);
    // 互不串：drawings 降级面仍在场（destroyInactiveTabPane=false 驻留）
    expect(screen.getByText(ALERT_DRAWINGS)).toBeTruthy();
  }, 20000);

  it("③重试换新实例入表形锁定（择稳判据）：翻桩拒后成→重试恢复→remount 取已解析实例不回归降级", async () => {
    const view = mountApp();
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    const baseline = paneStubs.drawings.imports;
    // 重试#1：新实例仍拒（翻桩阈值未达）→再降级
    fireEvent.click(screen.getByRole("button", { name: RETRY }));
    await screen.findByText(ALERT_DRAWINGS, {}, { timeout: 5000 });
    expect(paneStubs.drawings.imports).toBe(baseline + 1);
    // 翻桩：下一次动态 import 成功——重试#2=新实例装载恢复
    paneStubs.drawings.resolveAt = paneStubs.drawings.imports + 1;
    fireEvent.click(screen.getByRole("button", { name: RETRY }));
    await screen.findByText("DRAWINGS-OK", {}, { timeout: 5000 });
    const settled = paneStubs.drawings.imports;
    view.unmount();
    // remount：入表形=取重试#2 已解析实例（不入表形态此处回归降级=红）
    mountApp();
    await screen.findByText("DRAWINGS-OK", {}, { timeout: 5000 });
    expect(screen.queryByText(ALERT_DRAWINGS)).toBeNull();
    expect(paneStubs.drawings.imports).toBe(settled);
  }, 20000);
});
