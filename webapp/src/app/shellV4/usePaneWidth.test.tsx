/**
 * @vitest-environment jsdom
 *
 * v4 侧栏拖宽 hook 测试（v2-20261015 笔1——usePaneWidth 自 designZone 61-203
 * 提取后的行为冻结面：读宽钳位/非法值回退/拖拽往返与 localStorage 终值/
 * 零移动回落/cancel 一致/非主键忽略/卸载清理——D1 语义清单七条逐条锚）。
 *
 * 输入:  usePaneWidth（Harness 消费——aside width+柄 onPointerDown 接线）+
 *        localStorage Map 存根（jsdom 面无原生方法族——designZoneJointEntry
 *        .test 先例）
 * 输出:  断言族：①钳位三态（低于 min/高于 max/域内直通）②非法存储值回退
 *        fallback③拖拽往返（left=+delta/right=−delta）+拖中钳位+localStorage
 *        终值=onMove 记录值④零移动回落起点⑤cancel 终值与视觉一致⑥非主键
 *        忽略（无 cursor 置位/无宽度变/无持久写）⑦卸载清理（监听摘除+body
 *        cursor 复位）
 */
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePaneWidth, type PaneWidthConfig } from "./usePaneWidth";

/** localStorage 存根（jsdom 面无原生方法族——Map 薄壳三函数足量；
 *  broken 门=R1-N6 SecurityError 降级用例的受控抛错位）。 */
const storageBack = new Map<string, string>();
const storageCtl = { broken: false };
vi.stubGlobal("localStorage", {
  getItem: (key: string) => {
    if (storageCtl.broken) {
      throw new DOMException("The document is not permitted access", "SecurityError");
    }
    return storageBack.get(key) ?? null;
  },
  setItem: (key: string, value: string) => {
    if (storageCtl.broken) {
      throw new DOMException("The document is not permitted access", "SecurityError");
    }
    storageBack.set(key, value);
  },
  removeItem: (key: string) => void storageBack.delete(key),
});

/** 受测配置（drafting 左栏同值——190/140/420/left）。 */
const CONFIG: PaneWidthConfig = {
  key: "wp-v4-test-w",
  fallback: 190,
  min: 140,
  max: 420,
  side: "left",
};

/** Harness：hook 生产消费形最小复刻（aside width+柄 onPointerDown）。 */
function Harness({ config }: { config: PaneWidthConfig }) {
  const { width, onDragStart } = usePaneWidth(config);
  return (
    <aside data-testid="pane" style={{ width }}>
      <div data-testid="handle" onPointerDown={onDragStart} />
    </aside>
  );
}

function mount(config: PaneWidthConfig = CONFIG) {
  const view = render(<Harness config={config} />);
  return {
    view,
    pane: () => view.getByTestId("pane"),
    handle: () => view.getByTestId("handle"),
  };
}

/** jsdom 无 PointerEvent 构造器——MouseEvent 带 pointer* 类型串派发
 *  （button/clientX 经 MouseEvent init 真携带；designZone 拖拽面同口径）。 */
function pointerDownOn(
  el: Element,
  opts: { button?: number; clientX?: number; buttons?: number },
): void {
  el.dispatchEvent(
    new MouseEvent("pointerdown", {
      button: opts.button ?? 0,
      buttons: opts.buttons ?? 1,
      clientX: opts.clientX ?? 0,
      bubbles: true,
    }),
  );
}
function docMove(clientX: number, buttons = 1): void {
  document.dispatchEvent(new MouseEvent("pointermove", { clientX, buttons }));
}
function docUp(): void {
  document.dispatchEvent(new MouseEvent("pointerup"));
}
function docCancel(): void {
  document.dispatchEvent(new MouseEvent("pointercancel"));
}

beforeEach(() => {
  storageBack.clear();
  storageCtl.broken = false;
  document.body.style.cursor = "";
});
afterEach(cleanup);

describe("usePaneWidth·读宽面（D1 ①）", () => {
  it("钳位三态：低于 min 钳 min/高于 max 钳 max/域内直通", () => {
    storageBack.set(CONFIG.key, "100");
    expect(mount().pane().style.width).toBe("140px");
    cleanup();
    storageBack.set(CONFIG.key, "999");
    expect(mount().pane().style.width).toBe("420px");
    cleanup();
    storageBack.set(CONFIG.key, "260");
    expect(mount().pane().style.width).toBe("260px");
  });

  it("非法存储值回退 fallback（非数值/缺键）+空串=0 钳 min（样板 Number 语义零漂移锚）", () => {
    storageBack.set(CONFIG.key, "abc");
    expect(mount().pane().style.width).toBe("190px");
    cleanup();
    storageBack.delete(CONFIG.key);
    expect(mount().pane().style.width).toBe("190px");
    cleanup();
    // Number("")===0（有限值）——走钳位不走回退（样板 readWidth 同结果，
    // 提取零漂移锚：空串≠非法值分支）
    storageBack.set(CONFIG.key, "");
    expect(mount().pane().style.width).toBe("140px");
  });
});

describe("usePaneWidth·拖拽面（D1 ②③④⑤⑥⑦）", () => {
  it("left 往返：宽度=startWidth+delta+拖中钳位+localStorage 终值（onUp 落定）", () => {
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 300 });
    });
    expect(document.body.style.cursor).toBe("col-resize");
    act(() => {
      docMove(380);
    });
    expect(ui.pane().style.width).toBe("270px"); // 190+80
    act(() => {
      docMove(5000);
    });
    expect(ui.pane().style.width).toBe("420px"); // 拖中钳 max
    act(() => {
      docUp();
    });
    expect(ui.pane().style.width).toBe("420px");
    expect(storageBack.get(CONFIG.key)).toBe("420"); // 持久写只在 onUp
    expect(storageBack.size).toBe(1);
  });

  it("right 方向：宽度=startWidth−delta", () => {
    const ui = mount({ ...CONFIG, side: "right" });
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 300 });
    });
    act(() => {
      docMove(260); // delta=−40 → 宽度=190+40
    });
    expect(ui.pane().style.width).toBe("230px");
    act(() => {
      docUp();
    });
    expect(storageBack.get(CONFIG.key)).toBe("230");
  });

  it("零移动回落起点：down 后无 move 即 up=终值回起点（存储同值不改写漂移）", () => {
    storageBack.set(CONFIG.key, "200");
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 300 });
    });
    act(() => {
      docUp();
    });
    expect(ui.pane().style.width).toBe("200px");
    expect(storageBack.get(CONFIG.key)).toBe("200");
  });

  it("cancel 终值与视觉一致：拖中 cancel=终值=视觉宽度（非回落起点）", () => {
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 100 });
    });
    act(() => {
      docMove(150); // 190+50=240
    });
    expect(ui.pane().style.width).toBe("240px");
    act(() => {
      docCancel();
    });
    expect(ui.pane().style.width).toBe("240px"); // cancel 后视觉不变
    expect(storageBack.get(CONFIG.key)).toBe("240"); // 持久终值=onMove 记录值
  });

  it("非主键忽略：button≠0 无会话（无 cursor/无宽度变/无持久写）", () => {
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { button: 2, clientX: 300 });
    });
    expect(document.body.style.cursor).toBe("");
    act(() => {
      docMove(400);
    });
    expect(ui.pane().style.width).toBe("190px");
    act(() => {
      docUp();
    });
    expect(storageBack.has(CONFIG.key)).toBe(false);
  });

  it("卸载清理：监听摘除（pointermove/up/cancel 三摘）+body cursor 复位", () => {
    const removeSpy = vi.spyOn(document, "removeEventListener");
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 300 });
    });
    expect(document.body.style.cursor).toBe("col-resize");
    ui.view.unmount();
    expect(document.body.style.cursor).toBe(""); // 清理含 cursor 复位
    const removed = removeSpy.mock.calls
      .map(([type]) => type)
      .filter((type) => type.startsWith("pointer"));
    expect(removed.sort()).toEqual(["pointercancel", "pointermove", "pointerup"]);
    removeSpy.mockRestore();
  });
});


describe("usePaneWidth·窗外释放与存储降级（R1-W2/R1-N6）", () => {
  it("窗外释放终结：move buttons=0 → 会话终结+持久终值=最后持按宽度+其后移动零效果", () => {
    const ui = mount();
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 300 });
    });
    act(() => {
      docMove(350); // 190+50=240（持按中）
    });
    expect(ui.pane().style.width).toBe("240px");
    expect(document.body.style.cursor).toBe("col-resize");
    act(() => {
      docMove(500, 0); // 指针窗外释放后回归——无按键移动=终结会话
    });
    expect(document.body.style.cursor).toBe("");
    expect(storageBack.get(CONFIG.key)).toBe("240"); // 终值=最后持按宽度
    expect(ui.pane().style.width).toBe("240px");
    act(() => {
      docMove(600); // 会话已清——零效果
    });
    expect(ui.pane().style.width).toBe("240px");
    expect(storageBack.get(CONFIG.key)).toBe("240");
  });

  it("存储访问降级：读抛 SecurityError=初始宽回退 fallback/写抛错被吞不炸", () => {
    storageCtl.broken = true;
    storageBack.set(CONFIG.key, "260"); // 读路径抛错——存储值不可达
    const ui = mount();
    expect(ui.pane().style.width).toBe("190px");
    act(() => {
      pointerDownOn(ui.handle(), { clientX: 100 });
    });
    act(() => {
      docMove(160); // 190+60=250
    });
    expect(ui.pane().style.width).toBe("250px");
    act(() => {
      docUp(); // setItem 抛错被吞——宽度状态面不受损
    });
    expect(ui.pane().style.width).toBe("250px");
    expect(storageBack.get(CONFIG.key)).toBe("260"); // 写未落（预置值未被 250 覆写）
  });
});
