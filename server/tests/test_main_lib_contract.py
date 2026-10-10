"""main_lib 横向口白名单上限负例契约（批6g R1 结转——批6h 落地）。

输入:  server/waterprint_server/main_lib.py 源码（AST 静态实读）+其导入面
输出:  横向口契约断言（白名单集合恒等+routers 负例+异常类语义口）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：批6g 拆件把 R2 异常映射域迁 main_lib.py——UF-33 forbidden 契约
# 只拦 server→core 越层外跳，waterprint_server 包内横向口（→services
# 等）无机器强制（批6g Rulings R1 挂账）。本契约三断言：
#   A1 白名单集合恒等：waterprint_server.* 导入模块集 == 冻结白名单
#      （增侧=新横向口必须显式过审扩表；减侧=白名单腐化同步修）；
#   A2 routers 负例：main_lib 禁 import waterprint_server.routers
#      （路由层是 main 的消费面，伴生件反向即层序倒挂）；
#   A3 异常类语义口：自 services.*/jobs.*/auth 导入的每个名字必须是
#      Exception 子类或模块名（模块=表内点访问异常类的命名空间导入
#      ——jobs.worker 先例；函数/常量即语义越界，红）。
# 维护仪式：合法新增异常源模块=同步扩本文件白名单+commit 注记（本
# 契约红=口扩大未经对拍，非误报）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

MAIN_LIB = Path(__file__).resolve().parents[1] / "waterprint_server" / "main_lib.py"

_WHITELIST: frozenset[str] = frozenset({
    "waterprint_server.auth",
    "waterprint_server.jobs",
    "waterprint_server.jobs.manager",
    "waterprint_server.services.ai_connection",
    "waterprint_server.services.calculation",
    "waterprint_server.services.compare",
    "waterprint_server.services.cost",
    "waterprint_server.services.design_map",
    "waterprint_server.services.elevation",
    "waterprint_server.services.enumeration",
    "waterprint_server.services.exports",
    "waterprint_server.services.joint_enumeration",
    "waterprint_server.services.project_lifecycle",
    "waterprint_server.services.projects",
    "waterprint_server.services.report",  # B6（2026-10-09）计算书 Markdown 装配——白名单同步=J 项用户授权 2026-10-10
    "waterprint_server.services.report_pdf",  # B6（2026-10-09）Typst PDF 计算书导出——同上
    "waterprint_server.services.scene",
    "waterprint_server.services.sensitivity",
    "waterprint_server.services.site",
    "waterprint_server.services.trust",
    "waterprint_server.services.unit_detail",  # B2（2026-10-09）逐单元结果端点服务——白名单同步=J 项用户授权 2026-10-10
    "waterprint_server.services.validation",
    "waterprint_server.sse_limits",
})

_LATERAL_PREFIXES = ("waterprint_server.services", "waterprint_server.jobs", "waterprint_server.auth")
# 命名空间导入白名单（W7 收死 2026-09-27——auditor-readonly 审：防「是模块即过」退化；
# 在册唯一形态=jobs.worker〔表内点访问 worker.InvalidTaskPayloadError〕）
_NAMESPACE_ALLOWED: frozenset[tuple[str, str]] = frozenset({("waterprint_server.jobs", "worker")})


def _lateral_imports() -> dict[str, set[str]]:
    """main_lib 的 waterprint_server.* 导入面：模块 → 导入名集合。"""
    tree = ast.parse(MAIN_LIB.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("waterprint_server"):
            out.setdefault(node.module, set()).update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("waterprint_server"):
                    out.setdefault(alias.name, set())
    return out


def test_a1_whitelist_set_equality() -> None:
    """A1：横向导入模块集与冻结白名单恒等（增减两侧都红）。"""
    imported = set(_lateral_imports())
    assert imported == set(_WHITELIST), (
        f"main_lib 横向口漂移：新增={sorted(imported - set(_WHITELIST))} "
        f"移除={sorted(set(_WHITELIST) - imported)}——扩口须过审并同步本契约白名单"
        "（批6g R1/批6h 负例契约）"
    )


def test_a2_routers_forbidden() -> None:
    """A2：负例——main_lib 禁 import routers（层序倒挂）。"""
    assert not any(
        module == "waterprint_server.routers" or module.startswith("waterprint_server.routers.")
        for module in _lateral_imports()
    ), "main_lib 导入 routers——路由层是 main 消费面，伴生件反向即倒挂"


def test_a3_lateral_names_are_exceptions() -> None:
    """A3：横向口语义=异常类基或其命名空间（函数/常量即红）。"""
    offenders: list[str] = []
    for module, names in _lateral_imports().items():
        if not module.startswith(_LATERAL_PREFIXES):
            continue
        loaded = importlib.import_module(module)
        for name in names:
            obj = getattr(loaded, name, None)
            if obj is None:
                offenders.append(f"{module}.{name}=不可解析")
            elif inspect.isclass(obj):
                if not issubclass(obj, Exception):
                    offenders.append(f"{module}.{name}=非异常类")
            elif inspect.ismodule(obj):
                if (module, name) not in _NAMESPACE_ALLOWED:
                    offenders.append(f"{module}.{name}=命名空间导入不在显式白名单")
            else:
                offenders.append(f"{module}.{name}={type(obj).__name__} 非异常类/命名空间")
    assert not offenders, (
        f"main_lib 横向口导入非异常名字（正当性=异常映射表类基）：{offenders}"
    )
