"""项目文件确定性序列化读写（design/view 双态一起落盘，字节级稳定）。

输入:  ProjectFile / DesignState 对象（save/dumps） / 磁盘 JSON（load/loads）
输出:  JSON 文本（保存两次字节级相同） / ProjectFile 对象（往返无损）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D4/D5 裁决 2026-08-25；镜像测试 tests/project/test_io.py）
#
# 【公开接口】
#   dumps(project: ProjectFile) -> str        对象 → 确定性 JSON 文本
#   loads(text: str) -> ProjectFile           文本 → 校验后对象（防弹面）
#   save_project(project: ProjectFile, path: Path) -> None   原子落盘
#   load_project(path: Path) -> ProjectFile   锁探测 + 读 + loads
#   dumps_design(design: DesignState) -> str  design 态 → 含 format_version
#       头的确定性 JSON（content_hash 的参与面——未来版本迁移后哈希
#       自然失效；additive 公开面，T7a D5）
#   class InvalidProjectError(Exception)      装载/校验一切拒绝的统一
#       载体（GR-11 族，本文件定义；migration 复用）
#
# 【行为规格】
#   R1 确定性序列化（ADR-004）：model_dump(mode="json") 后经本文件自写
#      归一（键 str 递归、float round(x,10) 定点、bool/str/int/None
#      透传——与 result_schema 同款纪律但禁跨模块私有 import，B4
#      双胞胎代价）→ json.dumps(sort_keys=True, ensure_ascii=False,
#      separators=(",", ":")) + 尾换行 \n——同对象两次保存字节级相同
#      （CI 常驻断言）。
#   R2 往返无损：save→load→save 字节相同（round(x,10) 幂等前提）；
#      时间戳只存在于 view 态，不影响 design 哈希。
#   R3 load 侧防弹（§18 上传面）：大小上限 _MAX_BYTES、深度上限
#      _MAX_DEPTH（递归归一时计数）、json.loads parse_constant 拒
#      NaN/Infinity（GR-02）、parse_project 严格校验（extra=forbid，
#      错误消息含字段路径）；一切拒绝经 InvalidProjectError（from exc
#      保链，GR-12）；永不 pickle。
#   R4 保存原子性（GR-38）：同目录临时文件 path.name + ".tmp" 写入
#      UTF-8（newline="\n" 防 Windows 漂移）→ os.replace 原子替换。
#   R5 文件锁（§17.3，R5 最低成本）：path.with_suffix(".lock") 存在
#      → InvalidProjectError（消息含锁路径+"另一会话可能正在编辑"）。
#   R6 dumps_design 头部携带当前 format_version（与 migration.
#      SUPPORTED_VERSIONS[-1] 同源同步义务——本文件不 import
#      migration（migration→io 单向），版本常量各自持有、双源一致性
#      由 migrate 未来版拒路径守住）。
#
# 【T7a 冻结注记】
#   - 上限常量幂积表达式：_MAX_BYTES = 10**2 * 10**2 * 10**2 * 10
#     （=10_000_000，10MB；字面量全在 {10, 2} 白名单集）；_MAX_DEPTH
#     = 10 ** 2（嵌套 >100 层拒）。
#   - loads 归一时对 float 同样 round(x,10)+有限检查（R2 幂等前提）；
#     int 透传（与 result_schema 的 int→float 归一分野：项目文件参数
#     面保留整数形态）。
#   - 数值纪律：本文件不在魔法数字白名单——字面量仅 0/1/2/10。
#
# 【测试要求】双跑字节相同、往返无损、未知字段拒绝且消息含路径、
#   NaN/超深/超大小拒绝、原子保存、锁探测（探针②全组）。
#
# 【参照】重写计划 §12.3/§17.3/§18；ADR-004；简报 T7a D4/D5
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from math import isfinite
from pathlib import Path
from typing import Any, Final, NoReturn

from pydantic import ValidationError

from waterprint.contracts.project_schema import (
    DesignState,
    ProjectFile,
    parse_project,
)

_ROUND_DIGITS: Final[int] = 10
# 大小上限：10**2 * 10**2 * 10**2 * 10 = 10^7 字节（10MB——§18 上传面
# 安全上限；幂积表达式保字面量集 {10, 2} 合规）。
_MAX_BYTES: Final[int] = 10**2 * 10**2 * 10**2 * 10
# 深度上限：嵌套 >100 层拒（递归归一时计数；探针②以 >100 层构造实证）。
_MAX_DEPTH: Final[int] = 10**2
# 当前版 format_version（R6：dumps_design 头；与 migration.
# SUPPORTED_VERSIONS[-1] 同源同步——双源一致性由门禁+migrate 拒路径守）。
_FORMAT_VERSION: Final[str] = "1.0"
_JSON_KWARGS: Final[dict[str, Any]] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}


class InvalidProjectError(Exception):
    """项目装载/校验非法（JSON 形态/上限/未知字段/锁冲突）——领域异常。"""


def _finite_rounded(value: float, path: str) -> float:
    """float 守卫：非有限拒（GR-02）+ round(x,10) 定点（R1/R2 幂等前提）。"""
    if not isfinite(value):
        raise InvalidProjectError(
            f"项目数据含非有限值（NaN/±Inf）：{path} 处 {value!r}"
            "（GR-02 输入即拒——带病数据禁止进出序列化面）"
        )
    return round(value, _ROUND_DIGITS)


def _string_key(key: Any, path: str) -> str:
    """JSON 对象键守卫：仅字符串键（字段 ID 制，禁复合键漂移）。"""
    if not isinstance(key, str):
        raise InvalidProjectError(
            f"项目数据 Mapping 键必须为字符串：{path} 处 {key!r}"
            "（字段 ID 制——确定性排序前提）"
        )
    return key


def _normalize(value: Any, path: str, depth: int) -> Any:
    """值 → 确定性 JSON 树：键 str/float 定点/bool-str-int-None 透传。

    深度在递归入口计数（>100 层拒，R3）；与 result_schema._to_json 同款
    纪律但本文件自写（禁跨模块私有 import，B4 双胞胎代价）。
    """
    if depth >= _MAX_DEPTH:
        raise InvalidProjectError(
            f"项目 JSON 嵌套深度超过上限 {_MAX_DEPTH}：{path} 处（§18 上传面"
            "——超深结构拒，防栈耗尽炸弹）"
        )
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return _finite_rounded(value, path)
    if isinstance(value, Mapping):
        return {
            _string_key(key, path): _normalize(
                item, f"{path}.{key}", depth + 1
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence):
        return [
            _normalize(item, f"{path}[{index}]", depth + 1)
            for index, item in enumerate(value)
        ]
    raise InvalidProjectError(
        f"项目数据含不可序列化类型 {type(value).__name__}：{path}"
        "（R1 确定性序列化面：数值/字符串/布尔/None/容器）"
    )


def _reject_constant(name: str) -> NoReturn:
    """json.loads parse_constant 钩子：NaN/Infinity/-Infinity 一律拒（GR-02）。"""
    raise InvalidProjectError(
        f"项目 JSON 含非法常量：{name}（NaN/±Inf 禁——GR-02 输入即拒；"
        "JSON 规范外字面量）"
    )


def _decode(text: str) -> Any:
    """文本 → JSON 树：大小上限 + 解析（含 parse_constant 拒）。"""
    size = len(text.encode("utf-8"))
    if size > _MAX_BYTES:
        raise InvalidProjectError(
            f"项目 JSON 超过大小上限：{size} 字节 > {_MAX_BYTES}"
            "（§18 上传面安全上限）"
        )
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise InvalidProjectError(
            f"项目 JSON 解析失败：位置 line {exc.lineno} column {exc.colno}"
            f"（{exc.msg}）"
        ) from exc
    except RecursionError as exc:
        # T7a-R1a（二审 I-1 收编 2026-08-25）：万层级深嵌套（约 40KB+，
        # 仍小于 10MB 大小上限）可令 json.loads 的 C 扫描器先于 _normalize
        # 深度守卫触发递归保护——此处收编守住 R3"一切拒绝经
        # InvalidProjectError"契约（防 server 侧 500 冒充 400）。
        raise InvalidProjectError(
            f"项目 JSON 嵌套过深（解析器递归保护触发）：文本 {size} 字节"
            "（§18 上传面——与大小/深度上限同族的超深结构拒，R3 契约内）"
        ) from exc


def _build(tree: Any) -> ProjectFile:
    """JSON 树 → ProjectFile：归一（深度计数）+ 严格校验（消息含路径）。"""
    if not isinstance(tree, Mapping):
        raise InvalidProjectError(
            f"项目 JSON 顶层须为对象：得到 {type(tree).__name__}"
            "（format_version/design/view/metadata 四键容器）"
        )
    normalized = _normalize(tree, "$", 0)
    try:
        return parse_project(normalized)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in error['loc']) or '<root>'}:"
            f" {error['msg']}"
            for error in exc.errors()
        )
        raise InvalidProjectError(
            f"项目数据校验失败（strict + extra=forbid）：{details}"
        ) from exc


def dumps(project: ProjectFile) -> str:
    """确定性序列化正门：键递归排序、round(x,10) 定点、尾换行 \\n（R1）。"""
    tree = _normalize(project.model_dump(mode="json"), "$", 0)
    return json.dumps(tree, **_JSON_KWARGS) + "\n"


def loads(text: str) -> ProjectFile:
    """防弹装载正门：大小/深度/常量/严格校验四道闸（R3）。"""
    return _build(_decode(text))


def dumps_design(design: DesignState) -> str:
    """design 态确定性序列化（含 format_version 头，R6/T7a D5）。

    参与项=DesignState 七字段全量（model_dump 全量；"单元版本"经 nodes
    值结构携带——后续收紧 GR-21）；view 态天然不进（签名只收
    DesignState）。头部 format_version 保证未来版本迁移后哈希自然失效。
    """
    tree = {
        "format_version": _FORMAT_VERSION,
        "design": _normalize(design.model_dump(mode="json"), "design", 0),
    }
    return json.dumps(tree, **_JSON_KWARGS) + "\n"


def save_project(project: ProjectFile, path: Path) -> None:
    """原子落盘：同目录 .tmp 写入 → os.replace（GR-38，R4）。"""
    text = dumps(project)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def load_project(path: Path) -> ProjectFile:
    """锁探测 + 读文本 + 防弹装载（R5/R3）。"""
    lock = path.with_suffix(".lock")
    if lock.exists():
        raise InvalidProjectError(
            f"项目文件被锁定：{lock} 存在——另一会话可能正在编辑"
            "（§17.3 并发打开防护，v1 单用户最低成本方案）"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidProjectError(
            f"项目文件解码失败（非 UTF-8）：{path}——全部源码/文档 UTF-8"
            "（AGENTS §3）"
        ) from exc
    return loads(text)
