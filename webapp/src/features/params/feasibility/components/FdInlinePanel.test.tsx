/**
 * @vitest-environment jsdom
 *
 * fd 行内面板测试（M2 批 2026-10-08——fd 可行域段自 ParamForm 抽出+
 * §F.2 ①+②组合实装：1D 条行内常驻/2D 热力缩略行内+点击模态放大精读/
 * 模态关闭不清产物不重取〔预裁决 9 新语义〕/请求令牌迁移锚/错误两态）。
 *
 * 输入:  FdInlinePanel（vi.mock 边界=useDesignMap 模块面〔mutate 调用实录+
 *        onSuccess 队列受控——请求令牌与不重取断言源〕；禁 mock react-query
 *        内部/antd——FeasibilityBar/FeasibilityHeatmap/Modal/Select 原件
 *        真渲染〔fd-bar/fd-heatmap/fd-cell 探针锚直测〕）
 * 输出:  断言组：①未选第二轴→fd-bar 在场（1D 常驻锚）+挂载即取 1D；
 *        ②第二轴选定→fd-thumb 在场+内层 wrapper pointerEvents=none（格
 *        点击阻断面）+缩略容器 click→模态开；③模态开=fd-heatmap 双实例
 *        （getAllByTestId 长度 2——缩略+模态 DOM 并存）+模态内可行格点击
 *        →onBackfill 两键成对；④模态关→fd-thumb 仍在+mutate 计数不增
 *        （不重取——预裁决 9）；⑤请求令牌=快速切轴旧 onSuccess 晚到不
 *        覆盖（R-1 A2-N-04 语义迁移锚）；⑥designMap.isError→行内+模态
 *        两态错误文案在场。R1 回炉批（2026-10-08 门一双审 k1-W1/d1-W2）：
 *        ②追加 wrapper display=flex 断言（R1-a 高度链锚——fd-heatmap 根
 *        div 无高度样式，内层 svg height:100% 对 auto 父按宽高比自适应
 *        溢出 120px 容器；flex 容器 stretch 拉伸根 div 得确定高）；⑦⑧
 *        补 isPending 两分支加载文案锚（R1-b——1D 直渲/2D 第二轴选定产
 *        物未达，既有行为面用例对 HEAD 绿如实记非红面）；⑤注释勘正
 *        （R1-e/k1-N2：「第一轴 depth」→「第二轴 depth」）。2B7 批笔1
 *        （2026-10-08 用户裁决④）：⑨ 第二轴选定后 allowClear ✕ 清除→
 *        全复位重取 1D（回 1D 条形——mutateCalls[2]=[volume 单轴]+缩略
 *        消退+1D 产物达后 fd-bar 复现）。2B7 笔2（R1 回炉——门一双审
 *        k1-W1/d1-W1/k1-N2）：⑨ 追加显示态锚（✕ 清除后 .ant-select-
 *        clear null——值清空消隐直锚）+请求总数锚（mutateCalls.length
 *        =3 防清除路径多发请求静默）；⑩ 在途 2D+清除竞态帧（清除即令
 *        牌自增→旧 2D onSuccess 晚到被拦截——⑤切轴面外的清除面补锚）。
 *        2B8 笔1（2b8-20261008 N 级清扫）：⑨⑩ clear 钮查询收域面板域
 *        （fd-panel-volume 内查——k1-N1/d1-N2）+⑩ 补前置在场锚（k1-dN1
 *        ——对齐⑨形态，回归丢失时语义断言红）与请求总数锚（d1-dN1′）。
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FdInlinePanel } from "./FdInlinePanel";
import type { DesignMapResponse } from "../../../../shared/api/generated/model";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
if (typeof window.matchMedia !== "function") {
  window.matchMedia = (query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: () => {}, removeListener: () => {},
    addEventListener: () => {}, removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

/** 受控态位（vi.hoisted——useDesignMap mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  isPending: false,
  isError: false,
  error: null as unknown,
  mutateCalls: [] as { axes: { field_id: string }[] }[],
  onSuccessQueue: [] as ((product: unknown) => void)[],
}));

vi.mock("../api/useDesignMap", () => ({
  useDesignMap: () => ({
    mutate: (
      variables: { axes: { field_id: string }[] },
      options?: { onSuccess?: (product: unknown) => void },
    ) => {
      gate.mutateCalls.push(variables);
      if (options?.onSuccess) {
        gate.onSuccessQueue.push(options.onSuccess);
      }
    },
    isPending: gate.isPending,
    isError: gate.isError,
    error: gate.error,
  }),
}));

/** 连续参数夹具（range 在场 grid 缺席——isContinuousParam 判据面）。 */
const PARAMS = [
  { field_id: "volume", label_zh: "池容", dim: "VOLUME", default: null, range: { min: 100, max: 5000 }, grid: null },
  { field_id: "depth", label_zh: "水深", dim: "LENGTH", default: null, range: { min: 2, max: 6 }, grid: null },
  { field_id: "width", label_zh: "池宽", dim: "LENGTH", default: null, range: { min: 3, max: 9 }, grid: null },
];

/** 1D 产物（可行段 5~15——FeasibilityBar 渲染面）。 */
function map1D(fieldId: string): DesignMapResponse {
  return {
    unit_id: "u1",
    axes: [{ dim: "VOLUME", field_id: fieldId, label_zh: "池容", points: 21, range: { min: 0, max: 20 }, step: 1 }],
    axis_values: [[0, 5, 10, 15, 20]],
    constraint_coverage: "full",
    diagnosis: { axes: [], feasible_ratio: 0.6 },
    mask: null,
    segments: [{ start: 5, end: 15 }],
    stats: { feasible: 3, infeasible: 2, feasible_ratio: 0.6, total: 5 },
  };
}

/** 2D 产物（mask[0][0]=1 可行格——模态格点击回填断言源）。 */
function map2D(fieldA: string, fieldB: string): DesignMapResponse {
  return {
    unit_id: "u1",
    axes: [
      { dim: "VOLUME", field_id: fieldA, label_zh: "池容", points: 3, range: { min: 10, max: 30 }, step: 10 },
      { dim: "LENGTH", field_id: fieldB, label_zh: "水深", points: 3, range: { min: 1, max: 3 }, step: 1 },
    ],
    axis_values: [[10, 20, 30], [1, 2, 3]],
    constraint_coverage: "full",
    diagnosis: { axes: [], feasible_ratio: 0.5 },
    mask: [
      [1, 0, 1],
      [0, 1, 0],
      [1, 0, 1],
    ],
    segments: null,
    stats: { feasible: 5, infeasible: 4, feasible_ratio: 0.555, total: 9 },
  };
}

/** 渲染面（onBackfill spy——回填两键断言源）。 */
function renderPanel() {
  const onBackfill = vi.fn();
  const view = render(
    <FdInlinePanel
      projectId="p1"
      unitId="u1"
      fieldId="volume"
      params={PARAMS}
      onBackfill={onBackfill}
    />,
  );
  return { onBackfill, view };
}

/** 手动 flush onSuccess（act 内同步落 state——模拟请求晚到受控面）。 */
function flushOnSuccess(index: number, product: DesignMapResponse) {
  const onSuccess = gate.onSuccessQueue[index];
  if (onSuccess === undefined) {
    throw new Error(`onSuccess #${index} 未捕获（mutate 未发起）`);
  }
  act(() => {
    onSuccess(product);
  });
}

/** 选第二轴（antd v6 Select jsdom 交互：根 div〔data-testid 落点即
 *  .ant-select〕mouseDown 开下拉+点 option 文本——onChange 触发链实测）。 */
async function pickSecondAxis(optionText: string) {
  fireEvent.mouseDown(screen.getByTestId("fd-second-axis"));
  fireEvent.click(await screen.findByText(optionText));
}

beforeEach(() => {
  gate.isPending = false;
  gate.isError = false;
  gate.error = null;
  gate.mutateCalls.length = 0;
  gate.onSuccessQueue.length = 0;
});
afterEach(cleanup);

describe("FdInlinePanel fd 行内呈现（M2 D2 §F.2 ①+②组合）", () => {
  it("①未选第二轴→fd-bar 在场（1D 常驻锚）+挂载即取 1D", () => {
    renderPanel();
    expect(gate.mutateCalls).toEqual([{ axes: [{ field_id: "volume" }] }]);
    flushOnSuccess(0, map1D("volume"));
    expect(screen.getByTestId("fd-bar")).toBeTruthy();
  });

  it("②第二轴选定→fd-thumb 在场+wrapper pointerEvents=none+缩略 click→模态开", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    await pickSecondAxis("水深（depth）");
    expect(gate.mutateCalls[1]).toEqual({
      axes: [{ field_id: "volume" }, { field_id: "depth" }],
    });
    flushOnSuccess(1, map2D("volume", "depth"));
    const thumb = screen.getByTestId("fd-thumb");
    expect(thumb).toBeTruthy();
    // 格点击阻断面：内层 wrapper pointerEvents=none（jsdom 不模拟该 CSS——
    // DOM style 属性直断言，动线断言=缩略容器 click 开模态非格交互）
    const shield = thumb.querySelector('[data-testid="fd-heatmap"]')?.parentElement;
    expect(shield?.style.pointerEvents).toBe("none");
    // R1-a 高度链锚：wrapper display=flex（flex 容器 alignItems 默认
    // stretch→fd-heatmap 根 div〔无高度样式〕拉伸得 120px 确定高→内层
    // svg height:100% 解析为确定值+preserveAspectRatio meet 居中缩略；
    // jsdom 不能证伪渲染高——真浏览器高度实测归门二探针）
    expect(shield?.style.display).toBe("flex");
    fireEvent.click(thumb);
    // 模态开=fd-heatmap 双实例（缩略+模态 DOM 并存）
    await waitFor(() => {
      expect(screen.getAllByTestId("fd-heatmap").length).toBe(2);
    });
  });

  it("③模态内可行格点击→onBackfill 两键成对（volume=10+depth=1）", async () => {
    const { onBackfill } = renderPanel();
    flushOnSuccess(0, map1D("volume"));
    await pickSecondAxis("水深（depth）");
    flushOnSuccess(1, map2D("volume", "depth"));
    fireEvent.click(screen.getByTestId("fd-thumb"));
    await waitFor(() => {
      expect(screen.getAllByTestId("fd-heatmap").length).toBe(2);
    });
    // 模态实例=索引 1（Modal portal 挂 body 末尾——缩略实例在前）；
    // mask[0][0]=1 可行格→onPick(10, 1)→onBackfill 两键成对
    const modalCell = screen.getAllByTestId("fd-cell-0-0")[1];
    expect(modalCell).toBeDefined();
    fireEvent.click(modalCell!);
    expect(onBackfill).toHaveBeenCalledTimes(2);
    expect(onBackfill).toHaveBeenNthCalledWith(1, "volume", 10);
    expect(onBackfill).toHaveBeenNthCalledWith(2, "depth", 1);
  });

  it("④模态关→fd-thumb 仍在+不重取（mutate 计数不增——预裁决 9 新语义）", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    await pickSecondAxis("水深（depth）");
    flushOnSuccess(1, map2D("volume", "depth"));
    fireEvent.click(screen.getByTestId("fd-thumb"));
    await waitFor(() => {
      expect(screen.getAllByTestId("fd-heatmap").length).toBe(2);
    });
    const callsBefore = gate.mutateCalls.length;
    // Modal portal 挂 body 面板域外——close 钮 document 为正确域（与⑨⑩ Select clear 钮面板域收域不同）
    const closeBtn = document.querySelector(".ant-modal-close");
    expect(closeBtn).not.toBeNull();
    fireEvent.click(closeBtn!);
    // 关闭动线断言=ant-zoom-leave 类（antd Modal motion 在 jsdom 不触发
    // transition 完成回调——模态 DOM 退场不可达〔在册申报：真浏览器关闭
    // 保持语义由门二探针「模态→关闭保持」承载〕）；关闭后核心语义=缩略
    // 仍在（产物不清——R-1 病灶随行内 2D 面存在而消失）+零重取（旧语义
    // 「关闭清产物重取 1D」退役——预裁决 9）
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")?.classList.contains("ant-zoom-leave")).toBe(true);
    });
    expect(screen.getByTestId("fd-thumb")).toBeTruthy();
    expect(gate.mutateCalls.length).toBe(callsBefore);
  });

  it("⑤请求令牌=快速切轴旧 onSuccess 晚到不覆盖（R-1 A2-N-04 迁移锚）", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    // 第二轴 depth 请求发出（reqId=2）→未及回，改选 width（reqId=3）
    await pickSecondAxis("水深（depth）");
    await pickSecondAxis("池宽（width）");
    expect(gate.mutateCalls.length).toBe(3);
    // 旧 onSuccess（depth 产物）晚到→令牌不匹配被拦截（fd-thumb 不在场）
    flushOnSuccess(1, map2D("volume", "depth"));
    expect(screen.queryByTestId("fd-thumb")).toBeNull();
    // 新 onSuccess（width 产物）到达→产物落地
    flushOnSuccess(2, map2D("volume", "width"));
    expect(screen.getByTestId("fd-thumb")).toBeTruthy();
  });

  it("⑥designMap.isError→行内+模态两态错误文案在场", async () => {
    const { view } = renderPanel();
    flushOnSuccess(0, map1D("volume"));
    await pickSecondAxis("水深（depth）");
    flushOnSuccess(1, map2D("volume", "depth"));
    fireEvent.click(screen.getByTestId("fd-thumb"));
    await waitFor(() => {
      expect(screen.getAllByTestId("fd-heatmap").length).toBe(2);
    });
    gate.isError = true;
    gate.error = new Error("boom-502");
    view.rerender(
      <FdInlinePanel
        projectId="p1"
        unitId="u1"
        fieldId="volume"
        params={PARAMS}
        onBackfill={vi.fn()}
      />,
    );
    // 行内（fd-panel 内）+模态内两处错误文案俱在
    await waitFor(() => {
      expect(screen.getAllByText(/可行域求值失败：boom-502/).length).toBe(2);
    });
  });

  it("⑦isPending 直渲→「可行域求值中…」在场（1D 分支加载锚——R1-b）", () => {
    gate.isPending = true;
    renderPanel();
    expect(screen.getByText("可行域求值中…")).toBeTruthy();
    expect(screen.queryByTestId("fd-bar")).toBeNull();
  });

  it("⑧第二轴选定+产物未达+isPending→「可行域求值中…」在场（2D 分支加载锚——R1-b）", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    gate.isPending = true; // mutate#2 发出后持续 pending（产物未达）
    await pickSecondAxis("水深（depth）");
    // pickSecondAxis onChange→setState 重渲→mock 新读数 isPending 生效：
    // 2D 分支（fdSecond 非空）fdProduct 已清→加载文案在场+缩略缺席
    expect(screen.getByText("可行域求值中…")).toBeTruthy();
    expect(screen.queryByTestId("fd-thumb")).toBeNull();
  });

  it("⑨第二轴选定后 allowClear 清除→回 1D（用户裁决④ 2026-10-08）", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    await pickSecondAxis("水深（depth）");
    flushOnSuccess(1, map2D("volume", "depth"));
    expect(screen.getByTestId("fd-thumb")).toBeTruthy();
    // allowClear ✕ 在场（antd v6 rc-select clear 按钮——有值时渲染；
    // k1-N1 收域：Select 在面板内，面板域查询防他面误中）
    const clearBtn = screen.getByTestId("fd-panel-volume").querySelector(".ant-select-clear");
    expect(clearBtn).not.toBeNull();
    // jsdom 实测触发形=click（rc-select clear 按钮 onMouseDown 仅
    // preventDefault 保焦点不开下拉，清除动作挂 onClick——mouseDown 不
    // 触发 onChange，click 触发〔源码 node_modules/@rc-component/select
    // SelectInput/index.js clear button 实核〕）
    fireEvent.click(clearBtn!);
    // d1-W1 补锚——Select 值清空显示态（值清空→✕ 消隐——rc-select
    // useAllowClear 依 displayValues 空即不渲染 clear 按钮，显示态直锚
    // 非分支推断；d1-N2 收域同上——面板域查询 null）
    expect(screen.getByTestId("fd-panel-volume").querySelector(".ant-select-clear")).toBeNull();
    // 清除语义=onChange undefined→全复位重取 1D（与挂载即取同形——元素
    // 形同②mutateCalls[1] 口径：mock 落 push(variables) 对象非数组）
    expect(gate.mutateCalls[2]).toEqual({ axes: [{ field_id: "volume" }] });
    // k1-N2 补锚——请求总数（mount 1D+depth 2D+清除 1D=3 笔整——防未来
    // 清除路径多发请求静默；flushOnSuccess 只回调不发新请求，此后恒 3）
    expect(gate.mutateCalls.length).toBe(3);
    expect(screen.queryByTestId("fd-thumb")).toBeNull();
    flushOnSuccess(2, map1D("volume"));
    expect(screen.getByTestId("fd-bar")).toBeTruthy();
  });

  it("⑩在途 2D+清除竞态帧——旧 2D onSuccess 晚到被令牌丢弃（k1-W1 补锚）", async () => {
    renderPanel();
    flushOnSuccess(0, map1D("volume"));
    // 选 depth 后不 flush——2D 请求在途（reqId=2 未回）
    await pickSecondAxis("水深（depth）");
    // 清除即发 1D 重取（reqId=3 令牌自增——allowClear 属性本身零加请求；
    // 清除交互=一次 1D 重取，与挂载即取同形）
    const clearBtn = screen.getByTestId("fd-panel-volume").querySelector(".ant-select-clear");
    expect(clearBtn).not.toBeNull();
    fireEvent.click(clearBtn!);
    expect(gate.mutateCalls[2]).toEqual({ axes: [{ field_id: "volume" }] });
    // d1-dN1′ 补锚——请求总数（mount 1D+depth 2D+清除 1D=3 笔整——与⑨同口径）
    expect(gate.mutateCalls.length).toBe(3);
    // k1-W1 补锚——清除路径晚到拦截帧（⑤锚切轴面，本帧锚清除面）：旧 2D
    // onSuccess（depth 产物）晚到→reqId=2≠3 令牌不匹配被拦截。污染面直
    // 锚=fd-bar 不在场（清除帧 fdSecond 已 null，旧 2D 产物若落地会走 1D
    // 分支早产 fd-bar——该锚为本帧可证伪面）；fd-thumb 不在场为 prescribed
    // 锚（未选态结构恒真，保留呈序列完整）
    flushOnSuccess(1, map2D("volume", "depth"));
    expect(screen.queryByTestId("fd-thumb")).toBeNull();
    expect(screen.queryByTestId("fd-bar")).toBeNull();
    // 新 1D onSuccess 到达→fd-bar 复现（清除终态）
    flushOnSuccess(2, map1D("volume"));
    expect(screen.getByTestId("fd-bar")).toBeTruthy();
  });
});
