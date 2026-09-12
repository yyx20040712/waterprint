"""out_dims.dim 三写面对账门禁：manifest out_dims.dim 必须是量纲真源的镜像。

输入:  core units_lib 全单元 manifest（out_dims 声明+FormulaSpec 公式表）
       +四行业 drawing_projection 冻结表（dim_of）——AST 静态实读
       （声明面纯字面量，AST=运行时读等价；零依赖门禁不 import core）
输出:  冲突清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：工况面 UX 反馈批件 4（2026-09-12 用户质询「单一真相源」审计
#   收口）——量纲三写面对账：
#   ① FormulaSpec.output_dim（公式表——量纲真源）
#   ② drawing_projection dim_of（M3D1 冻结取数表）
#   ③ manifest out_dims.dim（消费投影——本门禁对象）
#   结构裁定（批内推荐项执行+批尾呈裁追认）：③非第二真源——对每个
#   声明键：①公式 lhs 域有值→③必须=①；①无声明的构造/圆整/聚合键
#   →③必须=②；①②皆无→FAIL（登记豁免须人工扩本脚本 EXEMPT）。
#   label_zh 真源单归 out_dims（本门禁不管）；扫描面=units_lib/**
#   /manifest.py 全单元——其余单元随 out_dims 声明扩面自动纳入。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UNITS_LIB = REPO / "core" / "waterprint" / "units_lib"
PROJECTION_FILES = (
    "drawing_projection_conveyance.py",
    "drawing_projection_mine.py",
    "drawing_projection_municipal.py",
    "drawing_projection_sludge.py",
)

# ①②皆无基准的键（登记豁免——人工维护，逐键述因）
EXEMPT: dict[str, tuple[str, ...]] = {}


def dim_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    """量纲表达式→DimKey 成员名（模块级别名 _D 或直书 DimKey.X）。"""
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def parse_module_aliases(tree: ast.Module) -> dict[str, str]:
    """模块级 `_D = DimKey.DIMENSIONLESS` 别名表。"""
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                name = dim_name(node.value, {})
                if name is not None:
                    aliases[target.id] = name
    return aliases


def parse_manifest(path: Path) -> tuple[str, dict[str, str], dict[str, str]]:
    """单单元 manifest →（unit_id，公式 lhs→output_dim，out_dims field→dim）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases = parse_module_aliases(tree)
    # 模块级字符串常量表（unit_id: UNIT_ID 引用形态解析）
    consts: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (
                isinstance(target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                consts[target.id] = node.value.value
    formulas: dict[str, str] = {}
    out_dims: dict[str, str] = {}
    unit_id = ""
    for node in ast.walk(tree):
        # _FORMULAS 元组内 FormulaSpec(...)：位置参 (id, expression,
        # symbols, output_dim, norm_ref)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "FormulaSpec"
            and len(node.args) >= 4
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            expression: str = node.args[1].value
            lhs = expression.split("=", 1)[0].strip()
            output = dim_name(node.args[3], aliases)
            if lhs and output is not None:
                formulas[lhs] = output
        # load_manifest({...}) 调用：unit_id 字段+out_dims 列表
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_manifest"
            and node.args
            and isinstance(node.args[0], ast.Dict)
        ):
            for key, value in zip(node.args[0].keys, node.args[0].values):
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    continue
                if key.value == "unit_id":
                    if isinstance(value, ast.Constant):
                        unit_id = str(value.value)
                    elif isinstance(value, ast.Name):
                        unit_id = consts.get(value.id, "")
                if key.value == "out_dims" and isinstance(value, ast.List):
                    for entry in value.elts:
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
    return unit_id, formulas, out_dims


def parse_projection(path: Path) -> dict[str, dict[str, str]]:
    """单行业投影文件 → unit_id→dim_of 键表（含模块级 _*_DIM_OF 引用）。"""
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases = parse_module_aliases(tree)
    named: dict[str, dict[str, str]] = {}
    for node in tree.body:
        value = getattr(node, "value", None)
        if (
            isinstance(value, ast.Dict)
            and isinstance(getattr(node, "target", None), ast.Name)
        ):
            table: dict[str, str] = {}
            for key, dim in zip(value.keys, value.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    name = dim_name(dim, aliases)
                    if name is not None:
                        table[key.value] = name
            named[node.target.id] = table
    projections: dict[str, dict[str, str]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "MappingProxyType"
            and node.args
            and isinstance(node.args[0], ast.Dict)
        ):
            for unit_node, proj in zip(node.args[0].keys, node.args[0].values):
                if not (isinstance(unit_node, ast.Constant) and isinstance(proj, ast.Call)):
                    continue
                table: dict[str, str] = {}
                for keyword in getattr(proj, "keywords", []):
                    if keyword.arg != "dim_of":
                        continue
                    if isinstance(keyword.value, ast.Dict):
                        for key, dim in zip(keyword.value.keys, keyword.value.values):
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                name = dim_name(dim, aliases)
                                if name is not None:
                                    table[key.value] = name
                    elif isinstance(keyword.value, ast.Name):
                        table.update(named.get(keyword.value.id, {}))
                projections[str(unit_node.value)] = table
    return projections


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    projections: dict[str, dict[str, str]] = {}
    for name in PROJECTION_FILES:
        projections.update(
            parse_projection(REPO / "core" / "waterprint" / "contracts" / name)
        )
    declared = 0
    failures: list[str] = []
    for path in sorted(UNITS_LIB.glob("*/*/manifest.py")):
        unit_id, formulas, out_dims = parse_manifest(path)
        if not out_dims:
            continue
        declared += len(out_dims)
        dim_of = projections.get(unit_id, {})
        exempt = EXEMPT.get(unit_id, ())
        for field, dim in sorted(out_dims.items()):
            if field in exempt:
                continue
            base = formulas.get(field)
            base_src = "①公式表 output_dim"
            if base is None:
                base = dim_of.get(field)
                base_src = "②projection dim_of"
            if base is None:
                failures.append(
                    f"{unit_id}.{field}={dim}：①②皆无基准（豁免须登记 EXEMPT 述因）"
                )
            elif base != dim:
                failures.append(
                    f"{unit_id}.{field}={dim} ≠ {base_src}的 {base}"
                )
    if failures:
        print(f"[FAIL] out_dims.dim 对账 {len(failures)} 键冲突：")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(
        f"[OK] out_dims.dim 对账：{declared} 条声明全为量纲真源镜像"
        "（①公式表 output_dim 优先/②projection dim_of 兜底）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
