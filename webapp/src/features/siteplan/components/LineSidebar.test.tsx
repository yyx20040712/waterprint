/**
 * @vitest-environment jsdom
 *
 * LineSidebar 组件测试（M3 批 D6——管网定线挂起位载体注记三态+标题行
 * 身份文案+删除三回调透传；feature 族组件测试首例 jsdom 面——契约头
 * 制式照 WindRose.test.tsx，环境面沿 modelTree.test.tsx 口径）。
 *
 * 输入:  LineSidebar（selection 三态 fixture[corridor/boundary/road]+
 *        removeOpen 受控+三回调 spy——jsdom 直渲，ConfigProvider 镜像
 *        providers.tsx button.autoInsertSpace=false[F10 收口——按 钮
 *        空插不变文案]）
 * 输出:  断言组：①corridor 选中=载体块在场（wp-pending-network-carrier
 *        锚+「管网定线预留」Tag+共用说明行全文）；②boundary 选中=载体块
 *        在场（共用一份文案——不分案，全文常量 CARRIER_NOTE 单源同锚）；
 *        ③road 选中=载体块不在场（道路非管线载体——mapping「红线/走廊
 *        折线」字面）；④选中标题行身份（「选中管线走廊 #1」序数=索引+1/
 *        「选中边界红线（单例）」/「选中道路 #3」三态全覆盖）；
 *        ⑤删除钮 onRequest 上行携 selection+Popconfirm 受控开态确认/
 *        取消回调透传（onConfirmRemove/onCancelRemove——props 直测形态）。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ConfigProvider } from "antd";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LineSidebar } from "./LineSidebar";
import type { RemovableSelection } from "../store/siteplanStore";

// jsdom 环境缺口补丁（沿 modelTree.test.tsx 口径——仅补 jsdom 未提供的
// 宿主 API，非组件 mock 面）：antd v6 Popconfirm 挂载期消费 ResizeObserver
// （overlay 定位测量），jsdom 无实现。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

const corridor: RemovableSelection = { kind: "corridor", index: 0 };
const boundary: RemovableSelection = { kind: "boundary" };
const road: RemovableSelection = { kind: "road", index: 2 };

/** 载体说明行全文（corridor/boundary 共用一份——M3 回炉 R2 单源常量，
 *  corridor/boundary 两用例同锚全文）。 */
const CARRIER_NOTE =
  "管网定线将挂起于红线/管线走廊折线——定线·水力计算·平纵图纸随后续管网批（挂起展示，不实现）";

/** 三回调 spy 集（每渲染一份——断言面互不串扰）。 */
function renderSidebar(selection: RemovableSelection, removeOpen = false) {
  const callbacks = {
    onRequest: vi.fn(),
    onConfirmRemove: vi.fn(),
    onCancelRemove: vi.fn(),
  };
  render(
    <ConfigProvider button={{ autoInsertSpace: false }}>
      <LineSidebar selection={selection} removeOpen={removeOpen} {...callbacks} />
    </ConfigProvider>,
  );
  return callbacks;
}

describe("LineSidebar（M3 D1——管网定线挂起位载体注记）", () => {
  afterEach(cleanup);

  it("corridor 选中=载体块在场（testid+管网定线预留 Tag+共用说明行全文）", () => {
    renderSidebar(corridor);
    const carrier = screen.getByTestId("wp-pending-network-carrier");
    expect(screen.getByText("管网定线预留")).toBeTruthy();
    expect(carrier.textContent).toContain(CARRIER_NOTE);
  });

  it("boundary 选中=载体块在场（与 corridor 共用一份文案——全文常量同锚）", () => {
    renderSidebar(boundary);
    const carrier = screen.getByTestId("wp-pending-network-carrier");
    expect(screen.getByText("管网定线预留")).toBeTruthy();
    expect(carrier.textContent).toContain(CARRIER_NOTE);
  });

  it("road 选中=载体块不在场（道路非管线载体——queryByTestId null）", () => {
    renderSidebar(road);
    expect(screen.queryByTestId("wp-pending-network-carrier")).toBeNull();
    expect(screen.queryByText("管网定线预留")).toBeNull();
  });

  it("选中标题行身份：corridor #1（序数=索引+1）；boundary 单例；road #3", () => {
    renderSidebar(corridor);
    expect(screen.getByText("选中管线走廊 #1")).toBeTruthy();
    cleanup();
    renderSidebar(boundary);
    expect(screen.getByText("选中边界红线（单例）")).toBeTruthy();
    cleanup();
    renderSidebar(road);
    expect(screen.getByText("选中道路 #3")).toBeTruthy();
  });

  it("删除钮 onRequest 上行携 selection+Popconfirm 确认/取消回调透传（受控 removeOpen）", () => {
    const callbacks = renderSidebar(corridor, true);
    fireEvent.click(screen.getByText("删除选中走廊"));
    expect(callbacks.onRequest).toHaveBeenCalledWith(corridor);
    fireEvent.click(screen.getByText("确认删除"));
    expect(callbacks.onConfirmRemove).toHaveBeenCalled();
    fireEvent.click(screen.getByText("取消"));
    expect(callbacks.onCancelRemove).toHaveBeenCalled();
  });
});
