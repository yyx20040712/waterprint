/**
 * ViewerToolbar 剖切控件测试（F5 D3——工具条剖切入口）。
 *
 * 输入:  ViewerToolbar（剖切 Switch+高度 Slider——store 两动作接线）+
 *        viewer3dStore 模块替身（受控 state+动作 spy——mock store）+
 *        antd Switch 捕获替身（onChange 采集——SSR 事件面替身）
 * 输出:  剖切控件在场/开关态与高度值随 store 绑定断言+Switch 交互驱动
 *        toggleClipping/setClippingHeight 两动作（含开启滑移半高默认）
 *        +glideHeight 纯函数锚
 *
 * 形态说明（沿 TaskPanel.test.tsx SSR 先例——零 jsdom 红线：renderToString
 *   无 DOM 事件派发且 zustand SSR 走 getInitialState 快照，故 store 用
 *   模块替身（受控 state 直读）、antd Switch 用捕获替身（onChange 采集后
 *   测试直调=点击等价）；Slider 为真身（aria 值锚直断）。
 */
import { renderToString } from "react-dom/server";
import { createElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

/** 受控 store 替身（vi.hoisted——mock 工厂闭包同源读写）。 */
const storeMock = vi.hoisted(() => {
  const state = {
    cameraPreset: "iso",
    clippingEnabled: false,
    clippingHeight: 0,
    showGrass: true,
    showWater: true,
    showInternals: true,
    showAnnotations: true,
  };
  const actions = {
    setCameraPreset: vi.fn(),
    toggleClipping: vi.fn(),
    setClippingHeight: vi.fn(),
    toggleLayer: vi.fn(),
  };
  return { state, actions };
});

/** Switch onChange 采集位（捕获替身渲染时写入——测试直调=点击等价）。 */
const captured = vi.hoisted(() => ({ switchOnChange: null as null | (() => void) }));

vi.mock("../store/viewer3dStore", () => ({
  useViewer3dStore: (selector: (snapshot: unknown) => unknown) =>
    selector({ ...storeMock.state, ...storeMock.actions }),
}));
vi.mock("antd", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    Switch: (props: {
      checked?: boolean;
      checkedChildren?: unknown;
      onChange?: () => void;
      "aria-label"?: string;
    }) => {
      captured.switchOnChange = props.onChange ?? null;
      return createElement(
        "button",
        {
          type: "button",
          role: "switch",
          "aria-checked": props.checked ? "true" : "false",
          className: props.checked ? "ant-switch ant-switch-checked" : "ant-switch",
        },
        String(props.checkedChildren ?? ""),
      );
    },
  };
});

import { ViewerToolbar, glideHeight } from "./ViewerToolbar";

beforeEach(() => {
  storeMock.state.cameraPreset = "iso";
  storeMock.state.clippingEnabled = false;
  storeMock.state.clippingHeight = 0;
  storeMock.state.showGrass = true;
  storeMock.state.showWater = true;
  storeMock.state.showInternals = true;
  storeMock.state.showAnnotations = true;
  storeMock.actions.setCameraPreset.mockClear();
  storeMock.actions.toggleClipping.mockClear();
  storeMock.actions.setClippingHeight.mockClear();
  storeMock.actions.toggleLayer.mockClear();
  captured.switchOnChange = null;
});

describe("ViewerToolbar 剖切入口（F5 D3）", () => {
  it("剖切控件在场：Switch 关态+高度 Slider 挂（默认 store 态渲染）", () => {
    const html = renderToString(<ViewerToolbar clippingMaxHeight={6} />);
    expect(html).toContain("剖切");
    expect(html).toContain('role="switch"');
    expect(html).toContain('aria-checked="false"');
    // Slider 真身在场景：关态禁用+值 0（剖切域 [0..6]）
    expect(html).toContain("ant-slider-disabled");
    expect(html).toContain('aria-valuenow="0"');
    expect(html).toContain('aria-valuemax="6"');
  });

  it("store 开启态绑定：Switch checked+Slider 值随 store（受控 state→重渲染）", () => {
    storeMock.state.clippingEnabled = true;
    storeMock.state.clippingHeight = 2.5;
    const html = renderToString(<ViewerToolbar clippingMaxHeight={6} />);
    expect(html).toContain('aria-checked="true"');
    expect(html).toContain("ant-switch-checked");
    expect(html).toContain('aria-valuenow="2.5"');
    expect(html).not.toContain("ant-slider-disabled");
  });

  it("高度上限随 bounds 传入：aria-valuemax=取景 bounds 高度（F5 D1 同源）", () => {
    storeMock.state.clippingEnabled = true;
    storeMock.state.clippingHeight = 2.5;
    const html = renderToString(<ViewerToolbar clippingMaxHeight={5.3} />);
    expect(html).toContain('aria-valuemax="5.3"');
  });

  it("Switch 交互驱动两动作：关→开滑移半高默认（toggle+setClippingHeight[glide]）", () => {
    renderToString(<ViewerToolbar clippingMaxHeight={6} />);
    expect(captured.switchOnChange).not.toBeNull();
    captured.switchOnChange?.();
    expect(storeMock.actions.toggleClipping).toHaveBeenCalledTimes(1);
    // 开启且现行高度 0：滑移 glideHeight(6)=3（S5 半剖先例——0 高度全剖黑幕防线）
    expect(storeMock.actions.setClippingHeight).toHaveBeenCalledWith(3);
  });

  it("Switch 交互两动作：已开启再拨=仅 toggle（不重复滑移高度）", () => {
    storeMock.state.clippingEnabled = true;
    storeMock.state.clippingHeight = 3;
    renderToString(<ViewerToolbar clippingMaxHeight={6} />);
    captured.switchOnChange?.();
    expect(storeMock.actions.toggleClipping).toHaveBeenCalledTimes(1);
    expect(storeMock.actions.setClippingHeight).not.toHaveBeenCalled();
  });

  it("开启滑移默认高度 glideHeight=max 四舍五入半值（步 0.5 网格值）", () => {
    expect(glideHeight(6)).toBe(3);
    expect(glideHeight(5.3)).toBe(2.5);
    expect(glideHeight(0)).toBe(0);
  });
});
