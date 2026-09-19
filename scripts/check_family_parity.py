"""aao/cass 同族公式族结构恒等门禁：静默分叉变响红（G-1 治理小批）。

输入:  units_lib/municipal/aao 与 cass 两包（manifest.py+formulas_*.py 兄弟
       声明件）——AST 静态实读（声明面纯字面量，零依赖门禁不 import core）
输出:  分叉清单（退出码 1）或 OK 摘要（退出码 0）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（G-1 治理小批——用户直排工单①，2026-09-19 调度员增补九）：
#   aao/cass 同族公式族（需氧量/曝气/污泥/能耗+manifest 既有平移声明的
#   几何/容积族）结构恒等机器断言+显式 delta 清单。
#   断言五层：
#   ① 完整性——两包全部公式 ID 必须=族对 ∪ 独有清单（精确集合相等）：
#     新增/删除公式不同步本声明区即红（防分叉从「不登记」路径溜入）；
#   ② 恒等对——RHS 经变量别名归一+空白归一后必须相等；符号集（别名
#     归一）相等且逐符号 dim 相等；LHS 输出符号（别名归一）相等；
#     output_dim 相等——单侧改系数/改结构即红；
#   ③ delta 对——表达式豁免比对（已知结构差异显式登记），但双向符号
#     集差必须=声明的精确集合、交集符号 dim/LHS/output_dim 仍须相等，
#     且表达式若被改成归一恒等 → FAIL（delta 条目过期应退役）；
#   ④ out_dims 镜像——族对输出符号（别名归一到 cass 名）在两包
#     manifest out_dims 中 dim 必须相等；
#   ⑤ 声明区自检——族对 ID 无重复、别名表无自环/双向冲突。
#   维护工序：改动任一侧同族公式 → 同步另一侧保持恒等，或在本文件
#   DELTAS/SOLO_* 登记差异（理由随条目）——delta 与独有清单是「显式
#   的知情差异」，未登记的差异是分叉。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UNITS_LIB = REPO / "core" / "waterprint" / "units_lib"

# ── 声明区（单源：族对/别名/delta/独有清单——G-1 断言对象）──────────

# 同族对：(aao_id, cass_id, 族标签)。工单四族（需氧量/曝气/污泥/能耗）
# +manifest 头注既有「CASS 同族平移」声明的几何/容积族一并机器化。
_PAIRS: tuple[tuple[str, str, str], ...] = (
    # 容积平移族（负荷法主容积+HRT 区容积——manifest 平移声明面）
    ("AO-F1", "CA-F3", "容积平移"),
    ("AO-F3", "CA-F4", "容积平移"),
    # 污泥族
    ("AO-F6", "CA-F16", "污泥"),
    ("AO-F7", "CA-F17", "污泥"),
    ("AO-F8", "CA-F18", "污泥"),
    # 需氧量族
    ("AO-F9", "CA-F19", "需氧量"),
    ("AO-F10", "CA-F20", "需氧量"),
    ("AO-F11", "CA-F21", "需氧量"),
    ("AO-F12", "CA-F22", "需氧量"),
    # 曝气族（供气-风机链；曝气头个数=delta 对见 DELTAS）
    ("AO-F21", "CA-F29", "曝气"),
    ("AO-F22", "CA-F30", "曝气"),
    # 能耗族（搅拌日耗电；e_aeration/p_stir=delta 对见 DELTAS）
    ("AO-F25", "CA-F33", "能耗"),
    # 几何平移族（L7 池体图元批平移声明面）
    ("AO-F16", "CA-F24", "几何平移"),
    ("AO-F17", "CA-F25", "几何平移"),
    ("AO-F18", "CA-F26", "几何平移"),
)

# 结构 delta 对（不在 _PAIRS——表达式豁免恒等比对，差异面精确断言）：
# (aao_id, cass_id, 族标签, 差异理由, aao_only 符号, cass_only 符号)
_DELTAS: tuple[tuple[str, str, str, str, frozenset[str], frozenset[str]], ...] = (
    (
        "AO-F19", "CA-F11", "几何平移",
        "池体构造容积口径：AAO 圆整后长×宽×水深 vs CASS 水面面积×水深"
        "（L7 平移族——AO-F19 圆整口径注记）",
        frozenset({"l_pool", "b_pool"}), frozenset({"a_pool"}),
    ),
    (
        "AO-F20", "CA-F28", "曝气",
        "曝气头个数取面：AAO 好氧区容积法 v_o_series/(h2·f) vs CASS 主反应"
        "区面积扣选择区法 (a_pool−v_selector/(n_pool·h2))/f（ds 审 W-3 口径）",
        frozenset({"v_o_series"}), frozenset({"a_pool", "v_selector", "n_pool"}),
    ),
    (
        "AO-F23", "CA-F31", "能耗",
        "曝气日耗电运行制式：AAO 连续流 ×24 满时 vs CASS 周期曝气含 "
        "duty_ratio 占空比（4h 周期 2h 曝气档，R-B42a-1 用户审查）",
        frozenset(), frozenset({"duty_ratio"}),
    ),
    (
        "AO-F24", "CA-F32", "能耗",
        "搅拌容积取面：AAO 缺氧+厌氧双区（v_anaerobic 与 CASS 选择区 "
        "v_selector 同角色经别名归一）vs CASS 仅选择区——AAO 额外缺氧区"
        "（CA-F28 注记口径——选择区仅搅拌/微量曝气）",
        frozenset({"v_anoxic"}), frozenset(),
    ),
)

# 变量别名（aao 符号 → cass 符号；LHS/RHS 通用——同角色不同名）：
# v_o↔v_load=好氧区/主反应区容积、t_p↔t_selector=厌氧区/选择区 HRT、
# v_anaerobic↔v_selector=厌氧区/选择区容积、w_stir_bio↔w_stir=搅拌密度。
_ALIASES: dict[str, str] = {
    "v_o": "v_load",
    "t_p": "t_selector",
    "v_anaerobic": "v_selector",
    "w_stir_bio": "w_stir",
}

# 独有公式（工艺特有，无同族对应——显式知情清单，逐条一句角色注记）
_SOLO_AAO: dict[str, str] = {
    "AO-F2": "连续流好氧区 HRT（CASS 序批式无分区 HRT）",
    "AO-F4": "反硝化缺氧区容积（CASS 无独立缺氧区）",
    "AO-F5": "连续流缺氧区 HRT",
    "AO-F13": "外回流泵流量（CASS 无外回流）",
    "AO-F14": "内回流泵流量（CASS 无内回流）",
    "AO-F15": "连续流全池水面折面（CASS 走双控 max 取面）",
}
_SOLO_CASS: dict[str, str] = {
    "CA-F1": "每日周期数（序批特有）",
    "CA-F2": "单池单周期滗水容积",
    "CA-F5": "主反应区+选择区容积合成",
    "CA-F6": "滗水深度上限（1/3 池深）",
    "CA-F7": "滗水控制单池面积",
    "CA-F8": "负荷法单池面积",
    "CA-F9": "双控取大实取单池面积",
    "CA-F10": "实际滗水深度",
    "CA-F12": "全厂池容",
    "CA-F13": "周期时段和校核",
    "CA-F14": "滗水能力需求",
    "CA-F15": "滗水器台数",
    "CA-F23": "实际污泥负荷（v_bio/v_plant 折算）",
    "CA-F27": "池体混凝土量概算",
}

# ── 解析层（AST 静态实读——check_out_dims_consistency 同款手法）────


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


def parse_formulas(pkg: Path) -> dict[str, dict[str, object]]:
    """单元包（manifest.py+formulas_*.py 兄弟件）→ 公式全表。

    每条：expression/lhs/rhs/symbols（符号→dim 名）/output_dim。
    """
    formulas: dict[str, dict[str, object]] = {}
    sources = [pkg / "manifest.py", *sorted(pkg.glob("formulas_*.py"))]
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        aliases = _parse_aliases(tree)
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "FormulaSpec"
                and len(node.args) >= 4
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                continue
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
    return formulas


def _parse_out_dims(pkg: Path) -> dict[str, str]:
    """manifest.py 的 load_manifest 调用 → out_dims field→dim 表。"""
    tree = ast.parse(
        (pkg / "manifest.py").read_text(encoding="utf-8"), filename=str(pkg / "manifest.py")
    )
    aliases = _parse_aliases(tree)
    out_dims: dict[str, str] = {}
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
    return out_dims


# ── 比对层 ─────────────────────────────────────────────────────────


def _canonical(token: str) -> str:
    """aao 侧符号/表达式 → cass 侧规范形（别名替换+空白归一）。"""
    result = re.sub(r"\s+", "", token)
    for aao_name, cass_name in _ALIASES.items():
        result = re.sub(rf"\b{aao_name}\b", cass_name, result)
    return result


def _norm_symbols(symbols: dict[str, str]) -> dict[str, str]:
    """符号表键经别名归一（值 dim 不变）。"""
    return {_canonical(sym): dim for sym, dim in symbols.items()}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failures: list[str] = []
    aao = parse_formulas(UNITS_LIB / "municipal" / "aao")
    cass = parse_formulas(UNITS_LIB / "municipal" / "cass")
    aao_dims = _parse_out_dims(UNITS_LIB / "municipal" / "aao")
    cass_dims = _parse_out_dims(UNITS_LIB / "municipal" / "cass")

    # ⑤ 声明区自检
    pair_ids = [p[0] for p in _PAIRS] + [d[0] for d in _DELTAS]
    pair_ids_cass = [p[1] for p in _PAIRS] + [d[1] for d in _DELTAS]
    if len(set(pair_ids)) != len(pair_ids) or len(set(pair_ids_cass)) != len(pair_ids_cass):
        failures.append("声明区自检：族对 ID 重复登记")
    for aao_name, cass_name in _ALIASES.items():
        if aao_name == cass_name or _ALIASES.get(cass_name) == aao_name:
            failures.append(f"声明区自检：别名表自环/双向冲突 {aao_name}↔{cass_name}")

    # ① 完整性：全部公式 ID=族对 ∪ 独有清单（精确集合相等）
    for side, table, declared, solo in (
        ("aao", aao, pair_ids, _SOLO_AAO),
        ("cass", cass, pair_ids_cass, _SOLO_CASS),
    ):
        actual = set(table)
        expect = set(declared) | set(solo)
        for fid in sorted(actual - expect):
            failures.append(
                f"完整性[{side}]：{fid} 未登记（同族对/独有清单均无——新增或"
                "删除公式必须同步本门禁声明区）"
            )
        for fid in sorted(expect - actual):
            failures.append(f"完整性[{side}]：声明区登记的 {fid} 在源码中不存在")

    # ② 恒等对断言
    identical_n = 0
    for aao_id, cass_id, family in _PAIRS:
        fa, fc = aao.get(aao_id), cass.get(cass_id)
        if fa is None or fc is None:
            continue  # 完整性层已报
        tag = f"[{family}] {aao_id}↔{cass_id}"
        if _canonical(str(fa["rhs"])) != _canonical(str(fc["rhs"])):
            failures.append(
                f"{tag} 表达式分叉：RHS（别名归一）不等——\n"
                f"    aao : {fa['rhs']}\n    cass: {fc['rhs']}"
            )
        if _canonical(str(fa["lhs"])) != _canonical(str(fc["lhs"])):
            failures.append(f"{tag} 输出符号分叉：{fa['lhs']} vs {fc['lhs']}")
        sa, sc = _norm_symbols(fa["symbols"]), _norm_symbols(fc["symbols"])  # type: ignore[arg-type]
        if set(sa) != set(sc):
            only_a = sorted(set(sa) - set(sc))
            only_c = sorted(set(sc) - set(sa))
            failures.append(f"{tag} 符号集分叉：aao_only={only_a} cass_only={only_c}")
        for sym in sorted(set(sa) & set(sc)):
            if sa[sym] != sc[sym]:
                failures.append(f"{tag} 符号量纲分叉：{sym} {sa[sym]} vs {sc[sym]}")
        if fa["output_dim"] != fc["output_dim"]:
            failures.append(
                f"{tag} 输出量纲分叉：{fa['output_dim']} vs {fc['output_dim']}"
            )
        identical_n += 1

    # ③ delta 对断言（表达式豁免；符号集差精确=声明；量纲面仍全检）
    for aao_id, cass_id, family, reason, aao_only, cass_only in _DELTAS:
        fa, fc = aao.get(aao_id), cass.get(cass_id)
        if fa is None or fc is None:
            continue
        tag = f"[{family}·delta] {aao_id}↔{cass_id}"
        sa, sc = _norm_symbols(fa["symbols"]), _norm_symbols(fc["symbols"])  # type: ignore[arg-type]
        real_only_a = set(sa) - set(sc)
        real_only_c = set(sc) - set(sa)
        if real_only_a != aao_only or real_only_c != cass_only:
            failures.append(
                f"{tag} 符号集差与声明不符：声明 aao_only={sorted(aao_only)} "
                f"cass_only={sorted(cass_only)}，实际 aao_only={sorted(real_only_a)} "
                f"cass_only={sorted(real_only_c)}"
            )
        for sym in sorted(set(sa) & set(sc)):
            if sa[sym] != sc[sym]:
                failures.append(f"{tag} 交集符号量纲分叉：{sym} {sa[sym]} vs {sc[sym]}")
        if _canonical(str(fa["lhs"])) != _canonical(str(fc["lhs"])):
            failures.append(f"{tag} 输出符号分叉：{fa['lhs']} vs {fc['lhs']}")
        if fa["output_dim"] != fc["output_dim"]:
            failures.append(
                f"{tag} 输出量纲分叉：{fa['output_dim']} vs {fc['output_dim']}"
            )
        if _canonical(str(fa["rhs"])) == _canonical(str(fc["rhs"])):
            failures.append(
                f"{tag} delta 条目过期：表达式已被改成归一恒等——差异不复存在，"
                "应从 _DELTAS 退役并入 _PAIRS"
            )

    # ④ out_dims 镜像：族对输出符号（归一到 cass 名）两包 dim 相等
    mirror_n = 0
    for aao_id, cass_id, *_ in (*_PAIRS, *_DELTAS):
        fa, fc = aao.get(aao_id), cass.get(cass_id)
        if fa is None or fc is None:
            continue
        lhs_c = _canonical(str(fa["lhs"]))
        if lhs_c != str(fc["lhs"]):
            continue  # 输出符号分叉已在上层报
        da, dc = aao_dims.get(lhs_c), cass_dims.get(lhs_c)
        if da is not None and dc is not None:
            mirror_n += 1
            if da != dc:
                failures.append(
                    f"out_dims 镜像：输出键 {lhs_c}（{aao_id}↔{cass_id}）"
                    f"两包 dim 分叉 {da} vs {dc}"
                )

    if failures:
        print(f"[FAIL] aao/cass 同族一致性 {len(failures)} 处分叉：")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(
        f"[OK] aao/cass 同族一致性：恒等对 {identical_n}+delta 对 "
        f"{len(_DELTAS)}（显式清单）+独有 aao {len(_SOLO_AAO)}/cass "
        f"{len(_SOLO_CASS)}+out_dims 镜像 {mirror_n} 键——零静默分叉"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
