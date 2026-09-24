"""系统提示（中性中文——零模型代号零供应商名，B4-4b 红线 4）。

输入:  会话项目绑定+降级态
输出:  system 消息文本（环上下文首条）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/prompts.py
#   职责：环系统提示唯一构造面——角色/能力/工具使用指引/ADR-019 纪律
#       /项目绑定态/降级注记。
#   禁区：禁模型代号与供应商名（check_model_names 执法面）；禁数字
#       主张（叙述面零数值——出数必经工具）；禁英文提示（产品语言=中文）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

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
    "完成即用中文总结结果（引用工具给出的关键数字与文件路径）。"
)


def system_prompt(project_id: str | None, degraded: bool) -> str:
    """系统提示（绑定态+降级态注入——纯中文零代号）。"""
    parts = [_ROLE, _RULES]
    if project_id:
        parts.append(f"当前会话绑定的项目：{project_id}（对它改参与计算即可，不必重建。）")
    else:
        parts.append("当前会话尚未绑定项目：需要设计工作时先 wp_create_project 建项。")
    if degraded:
        parts.append("注意：AI 接口暂不可用，当前处于关键词直译的降级模式。")
    return "\n".join(parts)
