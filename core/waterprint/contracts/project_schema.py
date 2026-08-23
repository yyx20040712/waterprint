"""项目文件 design/view 双态 schema（可复算与 git 友好的分界，ADR-004）。

输入:  项目 JSON（磁盘/网络边界）
输出:  ProjectFile 校验模型（pydantic 严格模式：未知字段拒绝）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T3 冻结；镜像测试 tests/contracts/test_project_schema.py）
#
# 【公开接口】
#   class DesignState(BaseModel)：参与 content-hash 与可复算的一切——
#       nodes: dict[str → dict[str, Any]]（单元实例 → 参数覆盖等，值结构
#           留后续任务只增收紧，GR-21/D7）
#       edges: list[dict[str, Any]]
#       constraint_choices: dict[str → str]（约束选择）
#       checked_units: list[str]（工况受检单元）
#       assumption_overrides: dict[str → float]（假设覆盖：键→值）
#       influent: dict[str, Any]（进水绑定）
#       standard_binding: dict[str → str]（标准绑定）
#       ——全部 default 空容器（design={} 必须过，D7 最小态）
#   class ViewState(BaseModel)：不参与哈希——
#       layout: dict[str → Any] = {}（画布布局）
#       camera: dict[str → Any] = {}（相机位姿）
#       windows: dict[str → Any] = {}（窗口布局）
#       timestamp: str = ""（时间戳；非空必须 UTC ISO 8601——GR-19，
#           禁本地时间字符串；空串 = 无时间戳的最小态 view={}）
#   class Metadata(BaseModel)：format_version / content_hash /
#       engine_version / data_version（全 str 必填——可复算三元组 +
#       版本，R3）
#   class ProjectFile(BaseModel)：format_version: str + design + view +
#       metadata（顶层 format_version 为权威源；metadata.format_version
#       缺省回填自顶层、冲突拒绝——双写单源，测试锁定 hasattr 面）
#   parse_project(data: Mapping[str, Any]) -> ProjectFile   严格校验正门
#
# 【行为规格】
#   R1 双态分界是 R10 病灶的根除：view 任何变化不算 dirty、不触发重算、
#      不进 content_hash；design 变化才产生新 hash（§12.3）。
#   R2 pydantic strict + extra="forbid"：未知字段、错误类型、深度/大小
#      超限（安全上限，server 层配置）一律拒绝（§18 文件上传面）。
#   R3 可复算三元组记录在 metadata：content_hash(design) + engine_version
#      + data_version；三者任一变化 = 全部结果过期（§16 A8）。
#   R4 项目内禁止随机 ID/时间戳进入 design 态（确定性序列化前提，
#      序列化规则在 project/io.py 执行，本文件只定义 schema）。
#   R5 format_version 迁移由 project/migration.py 链式处理，本 schema
#      永远只描述当前版。
#
# 【T3 冻结注记】（总控简报 D7 裁决，2026-08-23）
#   - 全模型 ConfigDict(strict=True, extra="forbid")——类型不 coerce、
#     未知键拒（安全面与漂移面双杀）。
#   - design/view 各字段值结构本任务只立容器形态（D7：留后续只增收紧，
#     GR-21）；timestamp 非空值按 GR-19 强制 UTC ISO 8601（tz 必在——
#     naive 串 = 本地时间字符串，拒）。
#   - 数值纪律：本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】view 变更不改 content_hash（与 project/io 联合，后续窗）、
#   未知字段拒绝、序列化往返无损（与 project/io 联合，后续窗）、
#   design={} 最小态通过、metadata 三元组四件齐备。
#
# 【参照】重写计划 §12.3/§11 R10；ADR-004；GR-19/GR-21；简报 T3 D7
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_STRICT_FORBID = ConfigDict(strict=True, extra="forbid")


class DesignState(BaseModel):
    """design 态：参与 content_hash 与可复算的一切（R1/R4）。"""

    model_config = _STRICT_FORBID

    nodes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    constraint_choices: dict[str, str] = Field(default_factory=dict)
    checked_units: list[str] = Field(default_factory=list)
    assumption_overrides: dict[str, float] = Field(default_factory=dict)
    influent: dict[str, Any] = Field(default_factory=dict)
    standard_binding: dict[str, str] = Field(default_factory=dict)


class ViewState(BaseModel):
    """view 态：不参与哈希的展示层状态（R1）。"""

    model_config = _STRICT_FORBID

    layout: dict[str, Any] = Field(default_factory=dict)
    camera: dict[str, Any] = Field(default_factory=dict)
    windows: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""

    @field_validator("timestamp")
    @classmethod
    def _timestamp_utc_iso(cls, value: str) -> str:
        """GR-19：非空时间戳必须 UTC ISO 8601 且带时区（禁本地时间串）。"""
        if not value:
            return value
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"view.timestamp 必须为 UTC ISO 8601：{value!r}（GR-19——"
                "本地时间字符串跨机排序错序，禁）"
            ) from exc
        if parsed.tzinfo is None:
            raise ValueError(
                f"view.timestamp 缺时区：{value!r}（GR-19——naive 串即本地时间"
                "字符串，必须带 UTC/偏移时区）"
            )
        return value


class Metadata(BaseModel):
    """metadata：可复算三元组 + 当前版描述（R3/R5）。"""

    model_config = _STRICT_FORBID

    format_version: str
    content_hash: str
    engine_version: str
    data_version: str


class ProjectFile(BaseModel):
    """项目文件：顶层 format_version（权威源）+ 双态 + metadata。"""

    model_config = _STRICT_FORBID

    format_version: str
    design: DesignState = Field(default_factory=DesignState)
    view: ViewState = Field(default_factory=ViewState)
    metadata: Metadata

    @model_validator(mode="before")
    @classmethod
    def _sync_format_version(cls, data: Any) -> Any:
        """metadata.format_version 回填自顶层权威源；双写冲突 = 拒。"""
        if not isinstance(data, Mapping) or not isinstance(
            data.get("metadata"), Mapping
        ):
            return data
        top = data.get("format_version")
        inner = data["metadata"].get("format_version")
        if inner is None:
            if top is None:
                return data
            synced = dict(data["metadata"])
            synced["format_version"] = top
            merged = dict(data)
            merged["metadata"] = synced
            return merged
        if top is not None and inner != top:
            raise ValueError(
                f"format_version 双写冲突：顶层 {top!r} vs metadata {inner!r}"
                "（顶层为权威源——迁移链只读顶层，R5）"
            )
        return data


def parse_project(data: Mapping[str, Any]) -> ProjectFile:
    """严格校验正门：strict + extra=forbid，未知字段/类型漂移一律拒（R2）。"""
    return ProjectFile.model_validate(dict(data))
