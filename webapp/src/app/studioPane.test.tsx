/**
 * @vitest-environment jsdom
 *
 * studio 槽装配件测试（M1 批——D9 轻量面：子面条五项+五子面懒装载统一+
 * mount-on-first-activation+display 保持；M6 批 2026-10-07 随迁改写：
 * study 占位断言退役→studyPane 懒装载面断言〔CONTENT_FACES 头插 study
 * ——五子面全懒装载；jsdom 不真装载 chunk 面，断言装载容器/标签面〕）。
 *
 * 输入:  StudioPane（renderLazyPane 注入 stub——零真 chunk 拉取）
 * 输出:  断言组：①子面条五项在场（研究/图纸/概算/对比/可信度）；②study
 *        懒装载壳在场（lazy:方案研究——装载容器/标签面）；③懒装载面未
 *        到访零挂载（lazy:图纸预览 不在场）；④onChange 目标序列化（点击
 *        图纸 → onSubfaceChange("drawings")——与 projectParam 断言互补）；
 *        ⑤mount-on-first-activation（subface=drawings 后 lazy:图纸预览
 *        在场）+display 切换保持（切回 study 后已挂载面仍在场+study 装载
 *        壳回归可见）。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StudioPane } from "./studioPane";

/** 懒装载壳注入 stub（标记文本——挂载即「lazy:<label>」在场）。 */
function stubLazyPane(label: string): React.ReactNode {
  return <div>lazy:{label}</div>;
}

function renderPane(subface: "study" | "drawings") {
  return render(
    <StudioPane
      subface={subface}
      onSubfaceChange={vi.fn()}
      renderLazyPane={(label) => stubLazyPane(label)}
    />,
  );
}

describe("StudioPane 子面条（M1——Segmented 五项受控）", () => {
  afterEach(cleanup);

  it("五项在场：研究/图纸/概算/对比/可信度", () => {
    renderPane("study");
    for (const label of ["研究", "图纸", "概算", "对比", "可信度"]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
    expect(screen.getByTestId("wp-studio-subface")).toBeTruthy();
  });

  it("study 懒装载壳在场（M6 随迁——lazy:方案研究 装载容器/标签面）", () => {
    renderPane("study");
    expect(screen.getByText("lazy:方案研究")).toBeTruthy();
  });
});

describe("子面内容装配（mount-on-first-activation+display 保持）", () => {
  afterEach(cleanup);

  it("未到访子面零挂载：初始 study——lazy:图纸预览 不在场（study 自面已装载）", () => {
    renderPane("study");
    expect(screen.queryByText("lazy:图纸预览")).toBeNull();
    expect(screen.queryByText("lazy:概算")).toBeNull();
    expect(screen.getByText("lazy:方案研究")).toBeTruthy();
  });

  it("onChange 目标序列化：点击「图纸」→ onSubfaceChange(\"drawings\")", () => {
    const onSubfaceChange = vi.fn();
    render(
      <StudioPane
        subface="study"
        onSubfaceChange={onSubfaceChange}
        renderLazyPane={(label) => stubLazyPane(label)}
      />,
    );
    fireEvent.click(screen.getByText("图纸"));
    expect(onSubfaceChange).toHaveBeenCalledWith("drawings");
  });

  it("到访后挂载（lazy:图纸预览 在场）+切回 study 保持已挂载面（display 不卸载+study 壳回归）", () => {
    const onSubfaceChange = vi.fn();
    const view = render(
      <StudioPane
        subface="study"
        onSubfaceChange={onSubfaceChange}
        renderLazyPane={(label) => stubLazyPane(label)}
      />,
    );
    expect(screen.queryByText("lazy:图纸预览")).toBeNull();
    // 到访 drawings（深链/切面）→ 首激活挂载
    view.rerender(
      <StudioPane
        subface="drawings"
        onSubfaceChange={onSubfaceChange}
        renderLazyPane={(label) => stubLazyPane(label)}
      />,
    );
    expect(screen.getByText("lazy:图纸预览")).toBeTruthy();
    // 切回 study：已挂载面 display:none 保持在场（状态不丢）+study 装载壳回归
    view.rerender(
      <StudioPane
        subface="study"
        onSubfaceChange={onSubfaceChange}
        renderLazyPane={(label) => stubLazyPane(label)}
      />,
    );
    expect(screen.getByText("lazy:图纸预览")).toBeTruthy();
    expect(screen.getByText("lazy:方案研究")).toBeTruthy();
  });
});
