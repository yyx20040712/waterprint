/**
 * canvasEditToolbar 决策面测试（P0-B——fix-plan 批2 落地件；F3 扩参数草稿闸）。
 *
 * 输入:  decideRunCalc(dirty, body, paramDraftCount) 纯函数（提交计算动作
 *        分派）+ paramDraftBlockMessage(count) 拦截文案
 * 输出:  判定组——只读态恒放行（P0-B 回归锚：旧实现 body 前置守卫把只读
 *        态静默吞掉，结果面九标签永远拿不到 done calc）；编辑态 dirty
 *        区分「先存后算」与「数据未就绪阻断」；F3/A-1：参数草稿计数
 *        非零=block-param-draft（先于存/算——handler 该态零 mutate 出
 *        指路提示；交互面归主控无头复验，与 P0-B 同口径）。
 */
import { describe, expect, it } from "vitest";

import { decideRunCalc, paramDraftBlockMessage } from "./canvasEditToolbar";

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

describe("参数草稿闸（F3 A-1——提交计算拦截未提交参数草稿）", () => {
  it("draftHint>0 恒 block-param-draft：只读/编辑 dirty 态均先于存与算拦截", () => {
    // 工单 A-1 根因：工具条保存不携带参数草稿，直算=用陈旧参数裸失败
    // （InvalidNodeError 实录）——闸不区分编辑态（草稿计数与图面 dirty 正交）
    expect(decideRunCalc(false, null, 2)).toBe("block-param-draft");
    expect(decideRunCalc(false, { design: {} }, 1)).toBe("block-param-draft");
    expect(decideRunCalc(true, { design: {} }, 3)).toBe("block-param-draft");
  });

  it("拦截文案指路正门：计数+『提交重算』+「保存不携带」三要素齐备（禁含糊）", () => {
    expect(paramDraftBlockMessage(2)).toBe(
      "参数面板有 2 项未提交——请先在参数面板点『提交重算』（工具条保存不携带参数草稿）",
    );
  });

  it("draftHint=0 照常提交（既有 T5 场景不回归——三态判定原样）", () => {
    expect(decideRunCalc(false, null, 0)).toBe("run");
    expect(decideRunCalc(false, { design: {} }, 0)).toBe("run");
    expect(decideRunCalc(true, { design: {} }, 0)).toBe("save-run");
    expect(decideRunCalc(true, null, 0)).toBe("block-unready");
  });
});
