/**
 * canvasEditToolbar 决策面测试（P0-B——fix-plan 批2 落地件）。
 *
 * 输入:  decideRunCalc(dirty, body) 纯函数（提交计算动作分派）
 * 输出:  三态判定——只读态恒放行（P0-B 回归锚：旧实现 body 前置守卫
 *        把只读态静默吞掉，结果面九标签永远拿不到 done calc）；编辑
 *        态 dirty 区分「先存后算」与「数据未就绪阻断」。
 */
import { describe, expect, it } from "vitest";

import { decideRunCalc } from "./canvasEditToolbar";

describe("decideRunCalc（P0-B 只读态提交计算复活）", () => {
  it("只读态（dirty=false）body=null 恒放行——draft===null 属正常态", () => {
    // 只读态 draft===null ⇒ draftProjectRaw 通道不出体 ⇒ body=null：
    // 旧实现在此静默 return（零请求零反馈），P0-B 修复锚
    expect(decideRunCalc(false, null)).toBe("run");
  });

  it("只读态 body 有值同样放行（理论辅证面——只读态本无 body）", () => {
    expect(decideRunCalc(false, { design: {} })).toBe("run");
  });

  it("编辑态 dirty 且 body 就绪=先存后算（呈裁⑥ 链序不回归）", () => {
    expect(decideRunCalc(true, { design: {} })).toBe("save-run");
  });

  it("编辑态 dirty 且 body 未就绪=阻断并提示（保存需要体）", () => {
    expect(decideRunCalc(true, null)).toBe("block-unready");
  });
});
