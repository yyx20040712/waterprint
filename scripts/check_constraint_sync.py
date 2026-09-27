"""约束同源性对拍门禁（AUD-W9 闭项——wave6 §批6h⑤，防线变更 Rulings 呈报）。

输入:  units_lib 各单元包 constraints.py（ConstraintDecl 声明面）+
       同包 manifest.py constraint_refs + data/coefficients/factors.yaml +
       data/constraint_kb/constraints.json（value_basis 数值投影面）
输出:  三份拷贝对拍结果（退出码 0=全绿，1=漂移/形状破相）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AUD-W9（audit-norms 20260925）——ConstraintDecl 声明运行期零
# import（死声明）+同一带限三份拷贝（声明表/manifest refs/系数库数值）
# 无机器对拍，静默分叉无门禁。本门禁补齐三向对拍：
#   C1 每单元包：constraints.py CONSTRAINTS 键集 ↔ manifest
#      constraint_refs 键集双向恒等（含 bashi_jiliangcao 双侧动态
#      构造面——f-string×字面量 GRADES 静态求值，零 import 零依赖）；
#   C2 声明表达式引用的 factor.* 键必须在 factors.yaml 在场（死声明
#      亦不得引用死键——数值真源唯一锚）；
#   C3 kb 条目 value_basis 投影：`factor.X.min/max` 引用的两键值必须
#      与表达式内联常数恒等（kb README「数值真源在系数库」承诺的
#      机器执法——系数库升版不同步 kb 即红）；单键 `factor.X.max`
#      同款；非 factor 溯源条目（geometry_guard=b3a 卷宗源）计数
#      呈现不 FAIL（覆盖面诚实汇报）。
# 形状绊线：包有 constraints.py 但 CONSTRAINTS 键解析为 0（构造形态
# 演进脱离本门禁解析面）=FAIL 强制人工对拍，禁静默跳过。
# 解析器为零依赖受限求值：仅 Constant/JoinedStr(f-string)/For 循环
# 追加/ListComp 两目标枚举/同包或同仓字面量名字解析，不 exec 任意代码。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UNITS_LIB = REPO / "core" / "waterprint" / "units_lib"
FACTORS_PATH = REPO / "data" / "coefficients" / "factors.yaml"
KB_PATH = REPO / "data" / "constraint_kb" / "constraints.json"
_FACTOR_REF = re.compile(r"factor\.[A-Za-z0-9_.]+")
_KB_BASIS = re.compile(r"factor\.[A-Za-z0-9_.]+\.(?:min/max|max|min)")
_KB_CONST = re.compile(r"(?:<=|>=|<|>)\s*(-?[0-9.]+(?:[eE][-+]?[0-9]+)?)")


def _literal_assign(tree: ast.Module, name: str) -> object | None:
    """模块级字面量赋值求值（GRADES 等名字真源——literal_eval 安全面；
    覆盖 Assign 与 AnnAssign 两形态——GRADES: tuple[str, ...] = (...)）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
            value = node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(value)  # type: ignore[possibly-undefined]
                except (ValueError, SyntaxError):
                    return None
    return None


def _resolve_name(name: str, local: dict[str, object], module_tree: ast.Module,
                  module_path: Path) -> object | None:
    """名字解析：局部绑定 → 本模块字面量 → 同包 manifest 字面量。"""
    if name in local:
        return local[name]
    direct = _literal_assign(module_tree, name)
    if direct is not None:
        return direct
    for node in ast.walk(module_tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            src = module_path.parent / f"{node.module.rsplit('.', 1)[-1]}.py"
            if src.is_file():
                try:
                    peer = ast.parse(src.read_text(encoding="utf-8"))
                except SyntaxError:
                    continue
                for alias in node.names:
                    if alias.name == name:
                        return _literal_assign(peer, name)
    return None


def _eval_fstring(node: ast.expr, local: dict[str, object]) -> str | None:
    """f-string 受限求值：字段=常量或单名字绑定（bashi 形态）。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    out: list[str] = []
    for part in node.values:
        if isinstance(part, ast.Constant):
            out.append(str(part.value))
        elif isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name):
            bound = local.get(part.value.id)
            if bound is None:
                return None
            out.append(str(bound))
        else:
            return None
    return "".join(out)


def _kw(node: ast.Call, kw: str, local: dict[str, object]) -> str | None:
    for arg in node.keywords:
        if arg.arg == kw:
            return _eval_fstring(arg.value, local)
    return None


def _decls_from_constraints(path: Path) -> tuple[dict[str, str], str | None]:
    """CONSTRAINTS 声明面静态求值（字面量直读+For 内 append 两形态）。

    返回 (key→expression 映射, 形态错误说明)。解析面外的构造形态
    返回错误说明（门禁 FAIL 逼人工对拍），不静默空集。
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return {}, f"constraints.py 语法不可解析：{exc}"
    decls: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        tgt = node.target
        if not isinstance(tgt, ast.Name):
            return {}, f"For 目标非单名字（L{node.lineno}）——需人工对拍"
        iterable: object = None
        if isinstance(node.iter, ast.Name):
            iterable = _resolve_name(node.iter.id, {}, tree, path)
        elif isinstance(node.iter, (ast.List, ast.Tuple)):
            try:
                iterable = ast.literal_eval(node.iter)
            except (ValueError, SyntaxError):
                iterable = None
        if iterable is None:
            return {}, (f"For 追加面迭代源不可静态解析（L{node.lineno}）——"
                        "构造形态脱离门禁解析面，需人工对拍")
        append_calls = [
            call for stmt in node.body if isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "append"
            for call in (stmt.value,)
            if isinstance(call.func.value, ast.Name)
        ] + [
            call for stmt in node.body if isinstance(stmt, ast.Assign)
            and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute)
            and stmt.value.func.attr == "append"
            for call in (stmt.value,)
            if isinstance(call.func.value, ast.Name)
        ]
        for call in append_calls:
            if not (isinstance(call.func, ast.Attribute) and isinstance(call.args, list)
                    and call.args and isinstance(call.args[0], ast.Call)):
                return {}, f"For 追加面调用形态超出解析面（L{call.lineno}）——需人工对拍"
            decl_call = call.args[0]
            if not (isinstance(decl_call.func, ast.Name)
                    and decl_call.func.id.endswith("ConstraintDecl")):
                return {}, f"For 追加面非 ConstraintDecl 构造（L{decl_call.lineno}）——需人工对拍"
            for item in iterable if isinstance(iterable, (list, tuple)) else ():
                local = {tgt.id: item}
                key = _kw(decl_call, "key", local)
                expr = _kw(decl_call, "expression", local)
                if key is None or expr is None:
                    return {}, (f"ConstraintDecl key/expression 含不可静态求值面"
                                f"（L{decl_call.lineno}）——需人工对拍")
                decls[key] = expr
    # 模块级直读（非循环面）：CONSTRAINTS = (ConstraintDecl(...), ...)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id.endswith("ConstraintDecl") and not _in_for(node, tree):
            key = _kw(node, "key", {})
            expr = _kw(node, "expression", {})
            if key and expr is not None:
                decls[key] = expr
    return decls, None


def _in_for(node: ast.AST, tree: ast.Module) -> bool:
    """节点是否位于任一 For 体内（循环面去重——外层已收）。"""
    for parent in ast.walk(tree):
        if isinstance(parent, ast.For):
            for stmt in parent.body:
                if any(child is node for child in ast.walk(stmt)):
                    return True
    return False


def _refs_from_manifest(path: Path) -> tuple[list[str], str | None]:
    """constraint_refs 静态求值：load_manifest({...}) 字典键下的字面量列表
    或双目标 ListComp（bashi 形态）。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [], f"manifest.py 语法不可解析：{exc}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value in zip(node.keys, node.values):
            if not (isinstance(key_node, ast.Constant) and key_node.value == "constraint_refs"):
                continue
            if isinstance(value, ast.ListComp):
                return _eval_listcomp(value, tree, path)
            if isinstance(value, (ast.List, ast.Tuple)):
                if all(isinstance(item, ast.Constant) for item in value.elts):
                    return [item.value for item in value.elts], None  # type: ignore[index]
                if len(value.elts) == 1 and isinstance(value.elts[0], ast.ListComp):
                    return _eval_listcomp(value.elts[0], tree, path)
                return [], "constraint_refs 列表元素含不可静态求值面——需人工对拍"
            return [], f"constraint_refs 非列表形态（{type(value).__name__}）——需人工对拍"
    return [], None  # 无 refs 声明=空集（对拍自然红或空对空）


def _eval_listcomp(node: ast.ListComp, tree: ast.Module,
                   path: Path) -> tuple[list[str], str | None]:
    """受限 ListComp：elt=f-string、生成器迭代源=字面量名字（≤2 目标）。"""
    names: dict[str, object] = {}
    for gen in node.generators:
        src: object = None
        if isinstance(gen.iter, ast.Name):
            src = _resolve_name(gen.iter.id, names, tree, path)
        elif isinstance(gen.iter, (ast.List, ast.Tuple)):
            try:
                src = ast.literal_eval(gen.iter)
            except (ValueError, SyntaxError):
                src = None
        if src is None:
            return [], "ListComp 迭代源不可静态解析——需人工对拍"
        tgt = gen.target
        if not isinstance(tgt, ast.Name):
            return [], "ListComp 目标非单名字——需人工对拍"
        names[tgt.id] = src
    materialized: list[str] = []

    def render(elt: ast.expr, binding: dict[str, object]) -> str | None:
        return _eval_fstring(elt, binding)

    # 逐生成器笛卡尔展开（≤2 目标覆盖 bashi 形态；更多=解析面外）
    gens = node.generators
    if len(gens) > 2:
        return [], "ListComp 生成器 >2——需人工对拍"
    for v1 in _iterable(names, gens[0]):
        b1 = {gens[0].target.id: v1} if isinstance(gens[0].target, ast.Name) else {}
        if len(gens) == 1:
            got = render(node.elt, b1)
            if got is None:
                return [], "ListComp elt 含不可求值面——需人工对拍"
            materialized.append(got)
        else:
            for v2 in _iterable(names, gens[1]):
                b2 = dict(b1)
                if isinstance(gens[1].target, ast.Name):
                    b2[gens[1].target.id] = v2
                got = render(node.elt, b2)
                if got is None:
                    return [], "ListComp elt 含不可求值面——需人工对拍"
                materialized.append(got)
    return materialized, None


def _iterable(names: dict[str, object], gen: ast.comprehension) -> tuple[object, ...]:
    src = names.get(gen.target.id if isinstance(gen.target, ast.Name) else "")
    return tuple(src) if isinstance(src, (list, tuple)) else ()


def _load_factors() -> dict[str, float]:
    """factors.yaml 键→值（行式受限解析——零 yaml 依赖）。"""
    out: dict[str, float] = {}
    key: str | None = None
    for line in FACTORS_PATH.read_text(encoding="utf-8").splitlines():
        hit = re.match(r'^- key: "([^"]+)"', line)
        if hit:
            key = hit.group(1)
            continue
        val = re.match(r"^  value: (-?[0-9.]+(?:[eE][-+]?[0-9]+)?)", line)
        if val and key:
            out[key] = float(val.group(1))
            key = None
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    factors = _load_factors()
    problems: list[str] = []
    packages = 0
    decl_total = 0
    for constraints in sorted(UNITS_LIB.glob("*/*/constraints.py")):
        packages += 1
        unit = constraints.parent
        name = f"{unit.parent.name}/{unit.name}"
        decls, shape_err = _decls_from_constraints(constraints)
        if shape_err:
            problems.append(f"[{name}] 声明面形状：{shape_err}")
            continue
        refs, ref_err = _refs_from_manifest(unit / "manifest.py")
        if ref_err:
            problems.append(f"[{name}] refs 面：{ref_err}")
            continue
        decl_total += len(decls)
        only_decl = sorted(set(decls) - set(refs))
        only_refs = sorted(set(refs) - set(decls))
        if only_decl:
            problems.append(f"[{name}] 声明键不在 manifest refs：{only_decl}")
        if only_refs:
            problems.append(f"[{name}] manifest refs 无声明对应：{only_refs}")
        if not decls and not refs:
            problems.append(f"[{name}] 双面零键——形状绊线（需人工核）")
        dead_keys: list[str] = []
        for key, expr in decls.items():
            for ref in _FACTOR_REF.findall(expr):
                if ref not in factors:
                    dead_keys.append(f"{key}→{ref}")
        if dead_keys:
            problems.append(f"[{name}] 声明引用死键（factors.yaml 缺席）：{dead_keys}")
    # C3：kb 投影对拍
    entries = json.loads(KB_PATH.read_text(encoding="utf-8"))["entries"]
    projected = 0
    uncovered = 0
    for entry in entries:
        basis = entry.get("value_basis", "")
        expr = entry.get("expression", "")
        cited = _KB_BASIS.findall(basis)
        if not cited:
            if "factor." in basis:
                problems.append(f"[kb:{entry['key']}] value_basis 引用 factor 但形态不可解析：{basis!r}")
            else:
                uncovered += 1
            continue
        anchor = cited[0]
        constants = [float(c) for c in _KB_CONST.findall(expr)]
        if anchor.endswith(".min/max"):
            family = anchor[: -len(".min/max")]
            pair = [factors.get(f"{family}.min"), factors.get(f"{family}.max")]
            if None in pair:
                problems.append(f"[kb:{entry['key']}] 溯源键缺席 factors.yaml：{family}.min/max")
                continue
            projected += 1
            if sorted(constants) != sorted(pair):  # type: ignore[type-var, arg-type]
                problems.append(
                    f"[kb:{entry['key']}] 数值投影漂移：表达式 {sorted(constants)} "
                    f"≠ factors {sorted(pair)}（{family}.min/max）")
        else:
            family = anchor[: -len(".max")] if anchor.endswith(".max") else anchor[: -len(".min")]
            single = factors.get(f"{family}.max" if anchor.endswith(".max") else f"{family}.min")
            if single is None:
                problems.append(f"[kb:{entry['key']}] 溯源键缺席 factors.yaml：{anchor}")
                continue
            projected += 1
            if not constants or not any(abs(c - single) < 1e-12 for c in constants):
                problems.append(
                    f"[kb:{entry['key']}] 数值投影漂移：表达式 {constants} "
                    f"不含 factors {single}（{anchor}）")
    if problems:
        print(f"[FAIL] 约束同源门禁：{len(problems)} 处漂移/形状破相：")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"[OK] 约束同源门禁：{packages} 单元包 {decl_total} 声明键三向对拍恒等；"
          f"kb 数值投影 {projected} 条恒等（{uncovered} 条非 factor 溯源不入投影面）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
