"""AI 演示版入口（B4-4a）：一句话意图解析→确定性管线编排（只编排不算数）。

输入:  CLI 话术（python -m waterprint_agent.demo "<话术>"）或 run_demo() 调用；
       LLM 三元组环境变量（可选——缺省/失败/断网自动规则回退）
输出:  演示结果 dict（达标判定+六指标+吨水指标+双报告落盘路径）+终端摘要
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4a 2026-09-20；镜像测试 tests/test_demo_{rules,llm,pipeline}.py）
#   路径：agent/waterprint_agent/demo.py
#   职责：NL 意图解析（LLM 单步+规则回退双通道）→ tools impl 函数族确定性
#       编排（建项目→改参→全厂计算→导出双报告）→终端摘要。
#   禁区：零新增计算逻辑（ADR-019 只编排不算数——计算全部经 core 正门
#       _run_calc_impl；数值面仅限 R3 入参量纲适配与终端展示派生换算
#       [吨水电耗=总能耗/流量——core 无现成键，展示层派生并如实注记]）；
#       顶层零重依赖（懒加载铁律——仅 stdlib）；零外部服务商标识字样
#       （配置键中性命名，端点/密钥/模型名全由环境变量承载——协议面
#       仅以「兼容 chat/completions 协议」描述，B4-2c 卫生小记③纪律）。
#
# 【公开接口】
#   DemoIntent（frozen dataclass——utterance/seed/name/scale_m3_d/
#       parse_source/parse_note）
#   parse_with_rules(utterance) -> DemoIntent（关键词规则表——离线通道）
#   parse_intent(utterance, *, offline=False) -> DemoIntent
#       （LLM 优先+失败回退规则：解析失败/违例/断网/缺配置四态一律回退，
#       parse_source 诚实标注不冒充）
#   run_demo(utterance, *, offline=False) -> dict（管线编排+结果组装）
#   main(argv) -> int（CLI：--offline 断网开关+--json 机器输出）
#
# 【行为规格】
#   R1 种子路由（规则表）：矿井→mine_43836；中水回用/再生→recycle；
#      回流/回路→loop；缺省→municipal_34760。
#   R2 规模抽取：N 万吨→N*10000 m³/d（含「每天 N 万吨/N 万吨每天/日处理
#      N 万吨」变体）；未提及→None（种子原规模零 patch）。
#   R3 规模改参量纲异构（B4-2b 在册「流量键异构」）：municipal 族
#      inlet.q_avg_daily 单位 m³/s（值=round(m³/d/86400,10)）；mine 族
#      mine_water_input.q_avg_daily 单位 m³/d（值直填）。
#   R4 LLM 调用：兼容 chat/completions 协议端点单步 POST（stdlib urllib，
#      10s 超时）；环境变量三元组 WATERPRINT_DEMO_LLM_BASE_URL/_API_KEY/
#      _MODEL 缺一即不发起；响应宽容提取首段 JSON 对象；schema 校验
#      （seed 白名单+scale 正数）违例即回退。
#   R5 管线步骤：create→(scale 非空)update_params→run_calc→result_summary
#      →export_calcbook+export_report；计算步失败=硬失败可解释返回；
#      规模 patch 任一条被 params_guard 拒收（值域外等）=硬失败可解释
#      返回（防静默携模板规模继续算——门一 W3 处置）；双导出步互相独立
#      （一侧 core 既有缺口不阻断另一侧——缺口可解释回显，
#      test_e2e_golden.py:25-28 记档面）。
#
# 【错误与边界】话术空串→规则缺省路由；LLM 任何异常（网络/超时/非 JSON/
#   违例）→规则回退；patch 被拒（值域外）→硬失败+逐条 reason 透传。
#
# 【测试要求】三话术全链（①③绿/②矿井案既有缺口可解释）+规则表变体
#   +LLM 四失败态回退+offline 零调用。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

__all__ = [
    "DemoIntent",
    "main",
    "parse_intent",
    "parse_with_rules",
    "run_demo",
]

_SEEDS: tuple[str, ...] = (
    "municipal_34760",
    "municipal_loop_34760",
    "municipal_recycle_34760",
    "mine_43836",
)
# 种子 → （进水声明节点, q_avg_daily 量纲）——量纲异构映射（R3）
_INLET_OF: dict[str, tuple[str, str]] = {
    "municipal_34760": ("inlet", "m3_s"),
    "municipal_loop_34760": ("inlet", "m3_s"),
    "municipal_recycle_34760": ("inlet", "m3_s"),
    "mine_43836": ("mine_water_input", "m3_d"),
}
_SECONDS_PER_DAY = 86400.0  # m³/d → m³/s 换算（municipal 族量纲面）
_SCALE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*万吨")
_LLM_TIMEOUT_S = 10.0

_LLM_SYSTEM_PROMPT = (
    "你是污水处理设计工具的参数解析模块。把用户的一句话设计需求解析为一个 JSON 对象，"
    "只输出该 JSON 对象，不要输出其他任何文字。\n"
    'JSON 结构：{"seed": "<模板标识>", "scale_m3_d": <正数或 null>, '
    '"note": "<一句话说明>"}\n'
    "seed 取值规则（按用户描述匹配）：\n"
    '- "municipal_34760"：市政污水处理厂（常规生化工艺，含 AAO 等）\n'
    '- "municipal_loop_34760"：市政污水+内部回流回路模板\n'
    '- "municipal_recycle_34760"：市政污水+中水回用/再生利用\n'
    '- "mine_43836"：矿井水处理（高浊度矿井水）\n'
    "scale_m3_d：日处理规模（立方米/天），用户说 N 万吨则填 N*10000，未提及填 null。\n"
    "note：解析要点一句话。"
)


@dataclass(frozen=True)
class DemoIntent:
    """解析结果（种子+规模+溯源）——管线编排的唯一输入面。"""

    utterance: str
    seed: str
    name: str
    scale_m3_d: float | None
    parse_source: str  # "llm" | "rules"——诚实标注（回退不冒充）
    parse_note: str


def _route_seed(utterance: str) -> str:
    """种子路由（R1 关键词表——命中优先级：矿井>回用>回路>市政缺省）。"""
    if "矿井" in utterance or "矿" in utterance:
        return "mine_43836"
    if "回用" in utterance or "再生" in utterance:
        return "municipal_recycle_34760"
    if "回流" in utterance or "回路" in utterance:
        return "municipal_loop_34760"
    return "municipal_34760"


def _demo_name(seed: str, scale_m3_d: float | None) -> str:
    """项目显示名（确定性：种子短名+规模——沙箱内项目可辨识）。"""
    short = {
        "mine_43836": "矿井",
        "municipal_34760": "市政",
        "municipal_loop_34760": "市政回路",
        "municipal_recycle_34760": "市政回用",
    }.get(seed, seed)
    scale = f"{scale_m3_d / 10000:g}万吨" if scale_m3_d is not None else "模板规模"
    return f"演示-{short}{scale}"


def parse_with_rules(utterance: str) -> DemoIntent:
    """规则通道（R1/R2 关键词表——零外部依赖，断网演示正道）。"""
    seed = _route_seed(utterance)
    scale_m3_d: float | None = None
    if match := _SCALE_RE.search(utterance):
        scale_m3_d = float(match.group(1)) * 10000.0
    note = f"规则解析：种子={seed}"
    if scale_m3_d is not None:
        note += f"，规模={scale_m3_d:g} m³/d"
    return DemoIntent(
        utterance=utterance,
        seed=seed,
        name=_demo_name(seed, scale_m3_d),
        scale_m3_d=scale_m3_d,
        parse_source="rules",
        parse_note=note,
    )


def _llm_settings() -> tuple[str, str, str] | None:
    """LLM 三元组环境变量（R4——缺一即 None，调用面零发起）。"""
    import os

    base_url = os.environ.get("WATERPRINT_DEMO_LLM_BASE_URL")
    api_key = os.environ.get("WATERPRINT_DEMO_LLM_API_KEY")
    model = os.environ.get("WATERPRINT_DEMO_LLM_MODEL")
    if not (base_url and api_key and model):
        return None
    return base_url, api_key, model


def _llm_call(utterance: str) -> str:
    """单步意图解析（R4：兼容 chat/completions 协议端点 POST——异常上抛由回退链收编）。"""
    import urllib.request

    settings = _llm_settings()
    if settings is None:
        raise RuntimeError("LLM 三元组环境变量未配置")
    base_url, api_key, model = settings
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _LLM_SYSTEM_PROMPT},
            {"role": "user", "content": utterance},
        ],
    }
    request = urllib.request.Request(  # 固定 JSON POST（URL=用户环境变量配置）
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_LLM_TIMEOUT_S) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload["choices"][0]["message"]["content"])


def _intent_from_llm_content(content: str, utterance: str) -> DemoIntent | None:
    """LLM 响应→Intent（宽容提取首段 JSON+schema 校验——违例返回 None）。"""
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match is None:
        return None
    try:
        parsed = json.loads(match.group(0))
    except ValueError:
        return None
    if not isinstance(parsed, dict):
        return None
    seed = parsed.get("seed")
    scale = parsed.get("scale_m3_d")
    if seed not in _SEEDS:
        return None
    if scale is not None and (type(scale) not in (int, float) or scale <= 0):
        return None
    scale_m3_d = float(scale) if scale is not None else None
    note = str(parsed.get("note") or "").strip() or "LLM 解析"
    return DemoIntent(
        utterance=utterance,
        seed=str(seed),
        name=_demo_name(str(seed), scale_m3_d),
        scale_m3_d=scale_m3_d,
        parse_source="llm",
        parse_note=f"LLM 解析：{note}",
    )


def parse_intent(utterance: str, *, offline: bool = False) -> DemoIntent:
    """意图解析正门（R4 回退链：LLM 优先→四失败态规则兜底）。"""
    fallback = parse_with_rules(utterance)
    if offline or _llm_settings() is None:
        return fallback  # offline=显式断网；缺配置=正常规则通道（非失败回退）
    try:
        intent = _intent_from_llm_content(_llm_call(utterance), utterance)
    except Exception as exc:  # LLM 面兜底：网络/超时/响应异常一律回退（可解释）
        return DemoIntent(
            **{
                **fallback.__dict__,
                "parse_note": f"{fallback.parse_note}（LLM 调用失败已回退：{type(exc).__name__}）",
            }
        )
    if intent is not None:
        return intent
    return DemoIntent(
        **{**fallback.__dict__, "parse_note": f"{fallback.parse_note}（LLM 响应违例已回退）"}
    )


def _inlet_patch(seed: str, scale_m3_d: float) -> dict[str, Any]:
    """规模改参 patch（R3 量纲异构映射——seed 分派单位面）。"""
    unit_id, dim = _INLET_OF[seed]
    value = round(scale_m3_d / _SECONDS_PER_DAY, 10) if dim == "m3_s" else float(scale_m3_d)
    return {"unit_id": unit_id, "key": "q_avg_daily", "value": value}


def run_demo(utterance: str, *, offline: bool = False) -> dict[str, Any]:
    """演示管线正门：解析→建项→改参→计算→摘要→双导出（R5）。"""
    from waterprint_agent import context as agent_context
    from waterprint_agent import sandbox
    from waterprint_agent.tools.calc import _run_calc_impl
    from waterprint_agent.tools.exports import _export_impl, _export_report_impl
    from waterprint_agent.tools.projects import _create_impl, _update_params_impl
    from waterprint_agent.tools.results import _summary_impl

    intent = parse_intent(utterance, offline=offline)
    ctx = agent_context.build_context(sandbox.sandbox_root())
    run = agent_context.run_tool  # 工具面统一包装：异常兜底 dict+会话日志留痕
    created = run(
        ctx,
        "wp_create_project",
        {"name": intent.name, "seed": intent.seed},
        lambda: _create_impl(ctx, intent.name, intent.seed),
        hint="演示建项目",
    )
    if "error" in created:
        return _hard_failure("建项目", created, intent)
    project_id = created["project_id"]
    design_digest = created["design_digest"]
    if intent.scale_m3_d is not None:
        patches = [_inlet_patch(intent.seed, intent.scale_m3_d)]
        updated = run(
            ctx,
            "wp_update_params",
            {"project_id": project_id, "patches": patches},
            lambda: _update_params_impl(ctx, project_id, patches),
            hint="演示改规模",
        )
        if "error" in updated:
            return _hard_failure("改参", updated, intent, project_id)
        rejected = [r for r in updated.get("results", []) if not r.get("accepted", False)]
        if rejected:  # W3 处置：规模 patch 被拒=硬失败（防静默携模板规模继续算）
            return _hard_failure("规模改参被拒", {"rejected": rejected}, intent, project_id)
        design_digest = updated["design_digest"]
    calc = run(
        ctx,
        "wp_run_calc",
        {"project_id": project_id},
        lambda: _run_calc_impl(ctx, project_id, None),
        hint="演示全厂计算",
    )
    if "error" in calc:
        return _hard_failure("全厂计算", calc, intent, project_id)
    summary_view = run(
        ctx,
        "wp_get_result_summary",
        {"project_id": project_id},
        lambda: _summary_impl(ctx, project_id),
        hint="演示结果摘要",
    )
    if "error" in summary_view:
        return _hard_failure("结果摘要", summary_view, intent, project_id)
    exports: dict[str, dict[str, Any]] = {}
    for kind, label, tool, arguments, thunk in (
        (
            "calcbook",
            "计算书",
            "wp_export_calcbook",
            {"project_id": project_id},
            lambda: _export_impl(ctx, project_id, "calcbook", condition_key="design"),
        ),
        (
            "report",
            "说明书",
            "wp_export_report",
            {"project_id": project_id},
            lambda: _export_report_impl(ctx, project_id, "design", None),
        ),
    ):
        outcome = run(ctx, tool, arguments, thunk, hint=f"演示导出{label}")
        exports[kind] = (
            {"path": outcome["path"]}
            if "path" in outcome
            else {"error": str(outcome.get("error") or "未知错误")}
        )
    summary: dict[str, Any] = dict(calc["summary"])
    return {
        "utterance": utterance,
        "intent": {
            "seed": intent.seed,
            "name": intent.name,
            "scale_m3_d": intent.scale_m3_d,
            "parse_source": intent.parse_source,
            "parse_note": intent.parse_note,
        },
        "project_id": project_id,
        "design_digest": design_digest,
        "compliant": summary_view["compliant"],
        "effluent_design": summary_view["effluent_design"],
        "flow_m3_d": summary.get("influent_flow_m3_d"),
        "summary": summary,
        "exports": exports,
    }


def _hard_failure(
    step: str, detail: dict[str, Any], intent: DemoIntent, project_id: str = ""
) -> dict[str, Any]:
    """管线硬失败组装（可解释——步骤名+原错误透传）。"""
    return {
        "error": f"管线步骤「{step}」失败",
        "detail": detail,
        "intent": {
            "seed": intent.seed,
            "scale_m3_d": intent.scale_m3_d,
            "parse_source": intent.parse_source,
        },
        "project_id": project_id,
    }


_INDICATOR_LABELS: tuple[tuple[str, str], ...] = (
    ("CODCR", "COD"),
    ("BOD5", "BOD5"),
    ("SS", "SS"),
    ("NH3N", "NH3-N"),
    ("TN", "TN"),
    ("TP", "TP"),
)


def _format_text(result: dict[str, Any]) -> str:
    """终端人类可读摘要（展示派生换算仅吨水电耗=总能耗/流量——core 无现成键）。"""
    lines = ["════ WaterPrint 一句话设计演示 ════"]
    if "error" in result:
        lines.append(f"失败：{result['error']}")
        lines.append(f"细节：{json.dumps(result.get('detail', {}), ensure_ascii=False)[:200]}")
        return "\n".join(lines)
    intent = result["intent"]
    summary = result["summary"]
    scale = intent["scale_m3_d"]
    scale_text = f"{scale:g} m³/d" if scale is not None else "模板原规模"
    lines.append(f"话术：{result['utterance']}")
    lines.append(f"解析：种子={intent['seed']} 规模={scale_text}（{intent['parse_note']}）")
    lines.append(f"项目：{result['project_id']}（design {result['design_digest'][:10]}）")
    verdict = "✓ 达标" if result["compliant"] else "✗ 未达标"
    lines.append(f"达标判定：{verdict}（出水指标 {len(result['effluent_design'])} 项）")
    effluent = " / ".join(
        f"{label} {summary[key]:.2f}" for key, label in _INDICATOR_LABELS if key in summary
    )
    lines.append(f"出水指标（mg/L）：{effluent}")
    flow = result["flow_m3_d"]
    power = summary.get("power_total_kwh_d")
    if power is not None and flow:
        lines.append(f"能耗：总 {power:.0f} kWh/d（吨水电耗 {power / flow:.3f} kWh/m³）")
    carbon = summary.get("carbon_total_kgco2e_d")
    intensity = summary.get("carbon_intensity_kgco2e_m3")
    if carbon is not None:
        extra = f"（吨水碳强度 {intensity:.3f} kgCO2e/m³）" if intensity is not None else ""
        lines.append(f"碳排：总 {carbon:.0f} kgCO2e/d{extra}")
    opex = summary.get("cost_opex_yuan_a")
    if opex is not None:
        lines.append(f"成本：年运行 {opex:,.0f} 元/a")
    lines.append(
        f"警告：{summary.get('warnings_total', 0)} 条"
        f"（质量闭合偏差 {summary.get('mass_closure_design', '—')}）"
    )
    for kind, label in (("report", "说明书"), ("calcbook", "计算书")):
        entry = result["exports"][kind]
        if "path" in entry:
            lines.append(f"落盘·{label}：{entry['path']}")
        else:
            lines.append(f"落盘·{label}：未生成（{entry['error'][:80]}）")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：python -m waterprint_agent.demo "<话术>" [--offline] [--json]。"""
    parser = argparse.ArgumentParser(
        prog="waterprint_agent.demo",
        description="一句话设计演示：自然语言→全厂计算→设计说明书+计算书",
    )
    parser.add_argument("utterance", nargs="+", help="设计需求话术（一句话）")
    parser.add_argument(
        "--offline", action="store_true", help="跳过意图解析调用（规则表直跑——断网预案）"
    )
    parser.add_argument("--json", action="store_true", help="输出完整 JSON（默认人类可读摘要）")
    args = parser.parse_args(argv)
    utterance = " ".join(args.utterance)
    result = run_demo(utterance, offline=args.offline)
    text = json.dumps(result, ensure_ascii=False, indent=2) if args.json else _format_text(result)
    print(text)  # CLI 输出面
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
