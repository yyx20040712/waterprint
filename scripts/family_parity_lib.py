"""aao/cass 同族一致性门禁共享库：声明面 AST 解析层（纯函数）。

输入:  units_lib 单元包的 manifest.py+formulas_*.py 兄弟声明件
输出:  公式全表（含平账计数）与 out_dims 表（含条目计数）——供
       check_family_parity 消费（same_layer_lib 共享库先例拆件）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（G-1 治理小批）：check_family_parity.py 预算墙拆件——解析层
#   （AST 静态实读零依赖，手法沿 check_out_dims_consistency）独立
#   成库；平账计数（call_total/parsed_ok/entry_total）与解析同库，
#   「跳过形状」在计数层暴露由主件断言。静态读不变量：声明面须纯
#   字面量构造（FormulaSpec 位置参数+str 常量 ID/expression）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
from pathlib import Path


def _dim_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    """量纲表达式→DimKey 成员名（模块级别名 _D 或直书 DimKey.X）。"""
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _parse_aliases(tree: ast.Module) -> dict[str, str]:
    """模块级 `_D = DimKey.DIMENSIONLESS` 别名表。"""
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                name = _dim_name(node.value, {})
                if name is not None:
                    aliases[target.id] = name
    return aliases


def parse_formulas(pkg: Path) -> tuple[dict[str, dict[str, object]], int, int]:
    """单元包（manifest.py+formulas_*.py 兄弟件）→ 公式全表+平账计数。

    每条：expression/lhs/rhs/symbols（符号→dim 名）/output_dim。
    返回 (formulas, call_total, parsed_ok)——主件侧平账：call_total≠
    parsed_ok=非常规构造被跳过；parsed_ok≠len(formulas)=重复 ID 覆盖。
    """
    formulas: dict[str, dict[str, object]] = {}
    call_total = 0
    parsed_ok = 0
    sources = [pkg / "manifest.py", *sorted(pkg.glob("formulas_*.py"))]
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        aliases = _parse_aliases(tree)
        for node in ast.walk(tree):
            func = node.func if isinstance(node, ast.Call) else None
            if not (
                (isinstance(func, ast.Name) and func.id == "FormulaSpec")
                or (isinstance(func, ast.Attribute) and func.attr == "FormulaSpec")
            ):
                continue
            call_total += 1
            if not (
                len(node.args) >= 4
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                continue
            parsed_ok += 1
            fid = str(node.args[0].value)
            expression = str(node.args[1].value)
            symbols: dict[str, str] = {}
            if isinstance(node.args[2], ast.Dict):
                for key, value in zip(node.args[2].keys, node.args[2].values):
                    if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                        continue
                    if isinstance(value, ast.Tuple) and len(value.elts) == 2:
                        dim = _dim_name(value.elts[0], aliases)
                        if dim is not None:
                            symbols[str(key.value)] = dim
            output = _dim_name(node.args[3], aliases)
            lhs, _, rhs = expression.partition("=")
            formulas[fid] = {
                "expression": expression,
                "lhs": lhs.strip(),
                "rhs": rhs.strip(),
                "symbols": symbols,
                "output_dim": "" if output is None else output,
            }
    return formulas, call_total, parsed_ok


def parse_out_dims(pkg: Path) -> tuple[dict[str, str], int]:
    """manifest.py 的 load_manifest 调用 → out_dims field→dim 表+条目总数。

    返回 (out_dims, entry_total)——主件侧平账：entry_total≠len(out_dims)
    =非字面量/非 dict 条目被静默丢弃（门禁盲区必须消除）。
    """
    tree = ast.parse(
        (pkg / "manifest.py").read_text(encoding="utf-8"), filename=str(pkg / "manifest.py")
    )
    out_dims: dict[str, str] = {}
    entry_total = 0
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_manifest"
            and node.args
            and isinstance(node.args[0], ast.Dict)
        ):
            continue
        for key, value in zip(node.args[0].keys, node.args[0].values):
            if not (
                isinstance(key, ast.Constant)
                and key.value == "out_dims"
                and isinstance(value, ast.List)
            ):
                continue
            for entry in value.elts:
                entry_total += 1  # 非 dict 条目也计数（平账红，防逃逸）
                if not isinstance(entry, ast.Dict):
                    continue
                fields = {
                    k.value: v.value
                    for k, v in zip(entry.keys, entry.values)
                    if isinstance(k, ast.Constant)
                    and isinstance(v, ast.Constant)
                }
                if "field_id" in fields and "dim" in fields:
                    out_dims[str(fields["field_id"])] = str(fields["dim"])
    return out_dims, entry_total
