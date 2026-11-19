"""系统提示（中性中文——零模型代号零供应商名，B4-4b 红线 4）。

输入:  会话项目绑定+降级态+决策纪要（治理批 2026-11-19 注入面）
输出:  system 消息文本（环上下文首条——含决策纪要块）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/prompts.py
#   职责：环系统提示唯一构造面——角色/能力/工具使用指引/ADR-019 纪律
#       /项目绑定态/降级注记/决策纪要块（跨轮持久——确定性拼装，
#       治理批 2026-11-19 接线：loop 读 sessions.read_decisions 注入）。
#   禁区：禁模型代号与供应商名（check_model_names 执法面）；禁数字
#       主张（叙述面零数值——出数必经工具）；禁英文提示（产品语言=中文，
#       wp_* 工具名标识符除外——_ROLE 先例）。
#
# 【行为规格】
#   R1 决策块：decisions 非空时渲染「〔决策纪要（跨轮持久）〕」段——
#      逐条「topic：conclusion（依据：rationale）」单行（rationale
#      缺省略括号；单行超上限确定性截断加省略号）；超条数上限尾注
#      「另有 N 条更早决策未列出」（N=运行时数据，非数字主张）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Any

__all__ = ["system_prompt"]

_ROLE = (
    "你是 WaterPrint 污水处理工艺设计助手。你通过工具完成设计工作：建项目"
    "（wp_create_project，种子模板或空白）、改参数（wp_update_params，清单式"
    "部分接受——拒绝项要看 reason）、计算（wp_run_calc）、读结果与诊断"
    "（wp_get_result_summary / wp_get_diagnostics）、按需读单元与知识"
    "（wp_list_units / wp_get_unit_manifest / wp_query_knowledge），导出"
    "交付物（wp_export_calcbook 计算书、wp_export_report 设计说明书等）。"
)

_RULES = (
    "工作纪律：①一切数值必须来自工具返回，禁止自行计算或编造数字；"
    "②改参或计算前先用 wp_get_project_outline 了解当前设计；"
    "③工具返回 error 时按 hint 调整参数重试，不要换一条路绕过约束；"
    "④用户目标不清时先提问确认，再动工具；⑤每轮少而准地调用工具，"
    "完成即用中文总结结果（引用工具给出的关键数字与文件路径）；"
    "⑥关键取舍定案后用 wp_record_decision 记录决策（跨轮持久、供说明书"
    "叙述），导出说明书前可用 wp_draft_narrative 取草稿。"
)

_DECISIONS_HEADER = "〔决策纪要（跨轮持久）〕"
_DECISIONS_MAX_ITEMS = 8  # 决策块条数上限（超限尾注——system 上下文预算守门）
_DECISIONS_LINE_CHARS = 120  # 单行字符上限（超限确定性截断加省略号）


def _decision_line(item: dict[str, Any]) -> str:
    """单条决策单行（R1——rationale 缺省略；超限确定性截断）。"""
    topic = str(item.get("topic") or "")
    conclusion = str(item.get("conclusion") or "")
    rationale = str(item.get("rationale") or "").strip()
    line = f"{topic}：{conclusion}"
    if rationale:
        line += f"（依据：{rationale}）"
    if len(line) > _DECISIONS_LINE_CHARS:
        line = line[:_DECISIONS_LINE_CHARS] + "……"
    return line


def _decisions_block(decisions: list[dict[str, Any]]) -> str:
    """决策纪要块（R1——保留最新 N 条+超限尾注，纯中文零数字主张）。"""
    lines = [_DECISIONS_HEADER]
    for item in decisions[-_DECISIONS_MAX_ITEMS:]:
        lines.append(_decision_line(item))
    hidden = len(decisions) - _DECISIONS_MAX_ITEMS
    if hidden > 0:
        lines.append(f"（另有 {hidden} 条更早决策未列出——wp_draft_narrative 可取全量草稿）")
    return "\n".join(lines)


def system_prompt(
    project_id: str | None,
    degraded: bool,
    decisions: list[dict[str, Any]] | None = None,
) -> str:
    """系统提示（绑定态+降级态+决策纪要注入——纯中文零代号）。"""
    parts = [_ROLE, _RULES]
    if project_id:
        parts.append(f"当前会话绑定的项目：{project_id}（对它改参与计算即可，不必重建。）")
    else:
        parts.append("当前会话尚未绑定项目：需要设计工作时先 wp_create_project 建项。")
    if degraded:
        parts.append("注意：AI 接口暂不可用，当前处于关键词直译的降级模式。")
    if decisions:
        parts.append(_decisions_block(decisions))
    return "\n".join(parts)
