/**
 * @vitest-environment jsdom
 *
 * 模型树静态骨架测试（M1 批——D4 面：六节点在场/管网定线挂起位/导航
 * 目标映射）。
 *
 * 输入:  ModelTree+onNavigate spy（jsdom 直渲——零取数面纯静态组件，
 *        无 mock 边界面）
 * 输出:  断言组：①六顶层节点在场（v3 B-1 逐字）+根区标题「模型」+
 *        静态计数；②管网定线默认折叠（挂起子节点不在场）+展开后挂起
 *        说明文案在场；③「管网预留」徽标锚（wp-pending-network）在场；
 *        ④onNavigate 目标映射（工艺流→canvas/研究→studio.study/结果.
 *        图纸→studio.drawings/结果.纵断→elevation）+静态节点零分派
 *        （项目.原始数据）；⑤过滤框本地过滤（命中链保留/无命中空态）。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ModelTree } from "./modelTree";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面：
// mock 边界纪律沿 paneDomainGate 头注，本处仅补 jsdom 未提供的宿主 API）：
// antd Tree 挂载期消费 ResizeObserver（虚拟列表高度测量），jsdom 无实现。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 顶层节点行定位（antd Tree 标题 span——文本命中即行）。 */
function nodeRow(title: string): HTMLElement {
  return screen.getByText(title).closest(".ant-tree-treenode") as HTMLElement;
}

describe("ModelTree 静态骨架（M1——六节点+根区标题）", () => {
  afterEach(cleanup);

  it("六顶层节点在场+根区标题「模型」+静态计数", () => {
    render(<ModelTree onNavigate={() => {}} />);
    for (const title of ["项目", "工艺流", "厂区布置", "管网定线", "研究", "结果"]) {
      expect(screen.getByText(title)).toBeTruthy();
    }
    expect(screen.getByText("全局假设")).toBeTruthy();
    expect(screen.getByText("模型")).toBeTruthy();
    expect(screen.getByText("6 节点")).toBeTruthy();
  });

  it("项目/结果子节点默认展开在场（defaultExpandedKeys 两键——沿 M1 默认态）", () => {
    render(<ModelTree onNavigate={() => {}} />);
    expect(screen.getByText("原始数据")).toBeTruthy();
    expect(screen.getByText("图纸")).toBeTruthy();
  });
});

describe("管网定线挂起位（判据 4 锚①——默认折叠+徽标+挂起说明）", () => {
  afterEach(cleanup);

  it("默认折叠：挂起子节点（定线/水力计算/平纵图纸）不在场", () => {
    render(<ModelTree onNavigate={() => {}} />);
    expect(screen.queryByText("定线（挂起）")).toBeNull();
    expect(screen.queryByText("水力计算（挂起）")).toBeNull();
    expect(screen.queryByText("平纵图纸（挂起）")).toBeNull();
  });

  it("「管网预留」徽标锚在场（wp-pending-network）", () => {
    render(<ModelTree onNavigate={() => {}} />);
    expect(screen.getByTestId("wp-pending-network")).toBeTruthy();
    expect(screen.getByText("管网预留")).toBeTruthy();
  });

  it("展开后挂起说明文案在场（rc-tree switcher 点击——受控 expandedKeys）", () => {
    render(<ModelTree onNavigate={() => {}} />);
    const row = nodeRow("管网定线");
    const switcher = row.querySelector(".ant-tree-switcher") as HTMLElement;
    expect(switcher).toBeTruthy();
    fireEvent.click(switcher);
    expect(screen.getByText("定线（挂起）")).toBeTruthy();
    expect(screen.getByText("平纵图纸（挂起）")).toBeTruthy();
  });
});

describe("onNavigate 目标映射（导航节点→TabTarget）", () => {
  afterEach(cleanup);

  it("工艺流→canvas；研究→studio.study；厂区布置→siteplan（父节点导航）", () => {
    const onNavigate = vi.fn();
    render(<ModelTree onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("工艺流"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "canvas" });
    fireEvent.click(screen.getByText("研究"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "studio", subface: "study" });
    fireEvent.click(screen.getByText("厂区布置"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "siteplan" });
  });

  it("结果.图纸→studio.drawings；结果.纵断→elevation（默认展开子节点）", () => {
    const onNavigate = vi.fn();
    render(<ModelTree onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("图纸"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "studio", subface: "drawings" });
    fireEvent.click(screen.getByText("纵断"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "elevation" });
  });

  it("结果.概算/对比/可信度→studio 同名子面（三行全映射）", () => {
    const onNavigate = vi.fn();
    render(<ModelTree onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("概算"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "studio", subface: "cost" });
    fireEvent.click(screen.getByText("对比"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "studio", subface: "compare" });
    fireEvent.click(screen.getByText("可信度"));
    expect(onNavigate).toHaveBeenLastCalledWith({ slot: "studio", subface: "trust" });
  });

  it("静态节点零分派：项目.原始数据（M1 无导航目标——后续批次接入）", () => {
    const onNavigate = vi.fn();
    render(<ModelTree onNavigate={onNavigate} />);
    fireEvent.click(screen.getByText("原始数据"));
    expect(onNavigate).not.toHaveBeenCalled();
  });
});

describe("过滤框（本地静态节点过滤——F-1 同款）", () => {
  afterEach(cleanup);

  it("命中子节点保留祖先链（「管网」→管网定线+挂起子节点自动展开）", () => {
    render(<ModelTree onNavigate={() => {}} />);
    fireEvent.change(screen.getByPlaceholderText("过滤节点/注记"), {
      target: { value: "管网" },
    });
    expect(screen.getByText("管网定线")).toBeTruthy();
    expect(screen.getByText("定线（挂起）")).toBeTruthy();
    expect(screen.queryByText("工艺流")).toBeNull();
  });

  it("无命中=空态（Empty 文案在场）", () => {
    render(<ModelTree onNavigate={() => {}} />);
    fireEvent.change(screen.getByPlaceholderText("过滤节点/注记"), {
      target: { value: "不存在的东西" },
    });
    expect(screen.getByText("无匹配节点")).toBeTruthy();
  });
});
