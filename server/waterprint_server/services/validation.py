"""validation 服务用例：最近完成结果集 → 校验观测（maint.* 三面投影）+两源警告聚合。

输入:  项目 id（路径）——plant 件（summary maint.* 键族=源 B+conditions
       offline dims）+val 件（源 A 声明级报告）+diag 件（kb_injected）+
       kb 目录（读时推导真源——list_constraints 缓存单例）
输出:  ValidationObservationResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（2A1 消费批 2a1-20261005 §3 D3；镜像测试
#   server/tests/services/test_validation.py）
#
# 【公开接口】
#   build_validation_observation(ctx, project_id) -> ValidationObservationResponse
#       （校验观测+聚合数据通道服务面正门——GET /api/calc/validation/{project_id}）
#   ValidationObservationResponse/NodeObservation/NodeMaintenanceFace/
#   AggregatedWarning（响应模型面——routers response_model 直用，trust/
#   sensitivity「服务层 pydantic 冻结模型」先例：禁协议层重复声明漂移面）
#   ValidationSourceNotFoundError（404 面）
#
# 【行为规格】（实现契约=docs/warning-aggregation.md 冻结规格——§1~§4
#   十一条款逐条绑定，规格冲突=本件返工）：
#   R1 取数（最近完成结果集，零重算）：read_project→latest_calc_result
#      （not_found=ValidationSourceNotFoundError——trust 404 家族同制，
#      main 域错误类名义表登记）；plant 件缺失/损坏同归 404 面（裸 500
#      禁）；val 件三态降级（缺键/缺文件/损坏→validation_available=
#      False——trust _load_diagnostics 同款，禁伪造空报告冒充）；diag
#      件缺席→kb_injected=None（禁伪造 False——trust 先例）。
#   R2 kb 推导真源=list_constraints(data_dir)（路径缓存单例——与 GET
#      /api/constraints 同源；calc 后 kb 升版=推导随现库，响应携 plant.
#      repro data_version 供版本漂移对照，不伪造 calc 时点）。
#   R3 源 B 三元组推导链（§4）：code=kb_warning_code(键中段)（键↔码
#      双向可逆单源——contracts.validation R1）；param_key=kb 条目
#      expression 首子句字段（expression_fields[0] 语义——源 A input_band
#      同链；实现=服务面 DSL 镜像解析〔site.py 先例，server 禁 import
#      solution 层序〕）；scope=maint 键节点段；severity=kb 条目 severity。
#   R4 聚合（§3 全条款）：命中=越门实例（源 B 仅 0.0 计入、1.0 通过
#      不入聚合入观测面〔§3-B1〕）；源 A 命中清单=∅ 空序列哨兵（声明级
#      一次不参与 ≥2 计数不混排）；去重键=(code,param_key,scope) 三元
#      （message/severity 不入键〔§2〕）；同键双源现→message 取源 A
#      实例（序轴前置）+清单=源 B 工况清单（源 A ∅ 并入不产项〔§2/§3〕）；
#      severity=max over 命中实例（源 A 实例与源 B kb 条目之上取最严重
#      ——ERROR>WARN>INFO）；命中工况清单序=record condition_keys 迭代
#      序过滤（序轴唯一源=ConditionSet 迭代序；存量旧记录缺键=字典序
#      兜底——A5 测试锁定）；any_fail 汇总键不入去重键族（§4）；kb 条目
#      缺席（版本漂移）不入聚合行、观测面保留原值（fail-visible——A2）；
#      B-only 行 message 合成（A1：三要素=条目键+表达式原文+首命中工况
#      offline dims 实际值；字段缺席无值形态）；unit_api.Warning 第三
#      警告面不入聚合（§4 v1 边界冻结——本件零消费快照 warnings）；
#      响应行排序=(scope,code,param_key) 确定性冻结（A3——视图分区/
#      重排归 FE）。
#   R5 观测投影（UF-61① FE 面数据源）：nodes 逐节点×逐工况三面——kb:
#      dict[constraint_key,bool]（1.0/0.0→passed 语义升级——A6，artifact
#      原 float 面=core 契约不动）/any_fail: bool/ratio: dict[field,float]
#      （分化键原值）/fixgeom_min: float|None；any_fail/ratio/fixgeom
#      不入 warnings 聚合面（§4——仪表灯与观测面，非违规聚合）。
#      命名注记（回炉 d1-W5 主控裁定）：NodeMaintenanceFace.condition_key
#      =工况轴单义（所属工况键）——与聚合面 condition_keys[] 同轴不同形、
#      非影响面 scope；保留名依据=unit_api.Warning UF-17 冻结先例（工况键
#      单义同形同义非双义；spec §1 禁双义入 API 非禁单义）。
#   R6 新鲜度：stale=result_is_stale（trust/sensitivity 同口径）；repro
#      三元组+task_id 回显（结果溯源面）。
#   R7 确定性：同结果集同响应（节点序字典序/face kb·ratio 键字典序/
#      warnings 行 (scope,code,param_key) 排序——双跑字节同端点测试
#      常驻断言）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 _PASS_VALUE/
#   _FAIL_VALUE（kb 门内/越门极性——core app_maintenance _PASS/_FAIL
#   语义常量镜像）。
#
# 【测试要求】§3 十语义逐条（∅ 哨兵/≥2 入聚/单工况直通/同键双源
#   message 取源 A/1.0 不入/any_fail 不入/kb 缺席降级/val 缺席降级/
#   kb_injected None/序=迭代序）+B-only 合成两形态+行排序+观测三面
#   投影+三态降级+200/404 家族+AU-1+双跑确定性（test_validation.py）。
#
# 【参照】docs/warning-aggregation.md（冻结实现契约）；services/trust.py
#   （降级三态/404 家族先例）；services/sensitivity.py（服务同构先例）；
#   services/constraints.py（kb 目录真源）；core app_maintenance.py
#   （maint.* 键族产出面——本件消费不重算）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.result_schema import (
    InvalidResultError,
    PlantResult,
    deserialize,
)
from waterprint.contracts.trust import (
    DiagnosticsReport,
    InvalidDiagnosticsError,
    deserialize_diag,
)
from waterprint.contracts.unit_api import Severity
from waterprint.contracts.validation import (
    InvalidValidationError,
    PlantWarning,
    ValidationReport,
    deserialize_validation,
    kb_warning_code,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.constraints import ConstraintEntry, list_constraints
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "AggregatedWarning",
    "NodeMaintenanceFace",
    "NodeObservation",
    "ValidationObservationResponse",
    "ValidationSourceNotFoundError",
    "build_validation_observation",
]

# maint.* 键族解析常量（core app_maintenance 键构造面镜像——core 无导出
# 常量，解析面镜像注记〔GR-20 同款纪律，webapp jointView 键族镜像先例〕）
_KEY_PREFIX: str = "maint."
_KB_INFIX: str = ".kb."
_RATIO_INFIX: str = ".ratio."
_FIXGEOM_SUFFIX: str = ".fixgeom.min"
_ANY_FAIL_KEY: str = "any_fail"  # 汇总键保留字（core 装载器保留字镜像）
_PASS_VALUE: float = 1.0  # kb 门内极性（core _PASS 语义常量镜像）
_FAIL_VALUE: float = 0.0  # kb 越门极性（core _FAIL 语义常量镜像）
# kb 判据口径注记（回炉 k1-N3b）：passed⟺值==_PASS_VALUE、hit⟺值==
# _FAIL_VALUE——域外值（0.5 等）core 不产（app_maintenance _PASS/_FAIL
# 常量单源两值域）；node_id 无点约定（全仓 unit_id 命名域——GR-26 字符
# 集）为 _split_maint_key 三段解析的前提绑定，core 键构造面同约定。
# severity max 分级序（§3——ERROR>WARN>INFO；元组 index 承载零数值字面量）
_SEVERITY_ASC: tuple[Severity, ...] = (Severity.INFO, Severity.WARN, Severity.ERROR)
# DSL 首子句字段头镜像（core solution.constraints._CLAUSE 的 field+op 段
# ——server 禁 import solution〔lint_imports 层序〕，解析面镜像注记：site.py
# kb expression 服务面解析先例同制；镜像面=首子句 field_id，形态越界
# fail-visible 拒〔constraints R2 同精神〕）
_CLAUSE_FIELD: re.Pattern[str] = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<=|>=|<|>|∈)"
)


class ValidationSourceNotFoundError(Exception):
    """校验观测源不可得（项目无结果集/结果文件损坏）——404 面。"""


class NodeMaintenanceFace(BaseModel):
    """单节点×单工况检修观测三面（R5——kb bool 语义升级 A6）。

    condition_key=**工况轴单义**（所属工况键——与聚合面 condition_keys[]
    同轴不同形，非影响面 scope；保留名依据=unit_api.Warning UF-17 冻结
    先例：工况键单义同形同义非双义，spec §1 禁双义入 API 非禁单义
    〔回炉 d1-W5〕）。"""

    model_config = ConfigDict(frozen=True)

    condition_key: str
    kb: dict[str, bool]
    any_fail: bool
    ratio: dict[str, float]
    fixgeom_min: float | None


class NodeObservation(BaseModel):
    """单节点观测（faces=该节点有 maint 键的工况——序轴迭代序）。"""

    model_config = ConfigDict(frozen=True)

    node_id: str
    faces: tuple[NodeMaintenanceFace, ...]


class AggregatedWarning(BaseModel):
    """聚合警告行（§3 行 schema——去重键三元组+命中清单+severity 分级；
    API 字段名硬约束 scope+condition_keys[]，禁 condition_key 双义〔§1〕）。"""

    model_config = ConfigDict(frozen=True)

    code: str
    param_key: str
    scope: str
    message: str
    condition_keys: tuple[str, ...]  # 源 A=∅ 哨兵；源 B=越门工况（序轴迭代序）
    severity: Severity


class ValidationObservationResponse(BaseModel):
    """校验观测报告（观测面+聚合两面——R1~R7）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    task_id: str
    stale: bool
    design_hash: str
    engine_version: str
    data_version: str
    kb_injected: bool | None  # diag 缺席=None（禁伪造 False——trust 先例）
    validation_available: bool  # val 件缺席（存量旧结果）=False
    conditions: tuple[str, ...]  # record condition_keys 投影（迭代序）
    nodes: tuple[NodeObservation, ...]
    warnings: tuple[AggregatedWarning, ...]


_NO_DIAGNOSTICS: DiagnosticsReport | None = None


def _load_diagnostics(latest: Mapping[str, Any]) -> DiagnosticsReport | None:
    """诊断件读取（trust 同款三态降级：缺键/缺文件/损坏 → None）。"""
    diag_file = latest.get("diag_file")
    if not isinstance(diag_file, str) or not diag_file:
        return _NO_DIAGNOSTICS
    try:
        return deserialize_diag(Path(diag_file).read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return _NO_DIAGNOSTICS


def _load_validation(latest: Mapping[str, Any]) -> ValidationReport | None:
    """val 件读取（R1 三态降级：缺键/缺文件/损坏 → None=
    validation_available False——源 A 面缺席如实，禁伪造空报告冒充）。"""
    val_file = latest.get("val_file")
    if not isinstance(val_file, str) or not val_file:
        return None
    try:
        return deserialize_validation(Path(val_file).read_bytes())
    except (OSError, InvalidValidationError):
        return None


def _condition_order(
    latest: Mapping[str, Any], plant: PlantResult
) -> tuple[str, ...]:
    """序轴唯一源（§3）+并集口径（回炉 d1-W3/k1-N5）：record condition_keys
    迭代序在前（现役 worker 写入=ConditionSet 迭代序）+summary-only 键字典
    序尾 append（record 子集/异形不静默丢键——两面共此轴不丢工况）；缺键
    或空列表=plant.summary 键域字典序兜底（A5——测试锁定）。"""
    raw = latest.get("condition_keys")
    if (
        not isinstance(raw, list)
        or not raw
        or not all(isinstance(item, str) for item in raw)
    ):
        return tuple(sorted(plant.summary))  # 缺键/空列表=视同缺键走兜底
    record_order = tuple(raw)
    return record_order + tuple(sorted(set(plant.summary) - set(record_order)))


def _split_maint_key(
    key: str,
) -> tuple[str, str, str] | None:
    """maint 键族分面解析：返回 (node, 面, 尾段)——kb 键→(node,"kb",
    constraint_key)、ratio 键→(node,"ratio",field)、fixgeom 键→(node,
    "fixgeom",尾段)；非 maint 键=None（core app_maintenance 键构造镜像）。
    未识别形态（maint. 前缀而三面中缀皆不中）=core 键族契约外——静默跳过
    （观测/聚合零消费；升格可见化〔计数/诊断标记〕归 T3/P1 后续批裁量
    ——回炉 d1-N2 注记）。"""
    if not key.startswith(_KEY_PREFIX):
        return None
    rest = key[len(_KEY_PREFIX):]
    for face, infix in (("kb", _KB_INFIX), ("ratio", _RATIO_INFIX)):
        node, sep, tail = rest.partition(infix)
        if sep and node and tail:
            return node, face, tail
    node, sep, tail = rest.partition(".")
    if sep and node and f".{tail}" == _FIXGEOM_SUFFIX:
        return node, "fixgeom", tail
    return None


def _expression_first_field(entry: ConstraintEntry) -> str:
    """expression 首子句字段（R3 推导链单源——源 A input_band 同链；
    镜像解析 fail-visible：形态越界=数据缺陷显式拒非静默跳过）。"""
    match = _CLAUSE_FIELD.match(entry.expression)
    if match is None:
        raise RuntimeError(
            f"kb 条目 {entry.key!r} expression 首子句形态非法："
            f"{entry.expression!r}（形如 field_id (</<=/>/>=/∈) 常数——"
            "受限 DSL 镜像解析，fail-visible）"
        )
    return match.group(1)


def _kb_context(
    entry: ConstraintEntry,
) -> tuple[str, Severity]:
    """源 B 三元组推导链参数面（R3）：param_key=expression 首子句字段；
    severity=kb 条目 severity（单条目单子句单字段=一键一值唯一〔§4〕）。"""
    return _expression_first_field(entry), Severity(entry.severity)


def _max_severity(left: Severity, right: Severity) -> Severity:
    """severity 分级取最严重（§3：max over 命中实例——ERROR>WARN>INFO；
    元组 index 分级，零数值字面量）。"""
    if _SEVERITY_ASC.index(left) >= _SEVERITY_ASC.index(right):
        return left
    return right


def _observations(
    plant: PlantResult, condition_order: tuple[str, ...]
) -> tuple[NodeObservation, ...]:
    """观测投影（R5）：逐工况×逐节点三面收集——kb bool 语义升级（A6）+
    any_fail 独立面+ratio 分化键原值+fixgeom_min（缺席 None）；节点序
    字典序、face 序=序轴迭代序、kb/ratio 键字典序（R7 确定性）。"""
    nodes: dict[str, dict[str, dict[str, Any]]] = {}
    for condition_key in condition_order:
        for key, raw in plant.summary.get(condition_key, {}).items():
            parsed = _split_maint_key(key)
            if parsed is None:
                continue
            node, face_kind, tail = parsed
            value = float(raw)
            face = nodes.setdefault(node, {}).setdefault(
                condition_key,
                {"kb": {}, "any_fail": False, "ratio": {}, "fixgeom_min": None},
            )
            if face_kind == "kb":
                if tail != _ANY_FAIL_KEY:
                    face["kb"][tail] = value == _PASS_VALUE  # 1.0→passed（A6）
                else:
                    # 汇总键独立面；core 不变量（回炉 k1-N3a 绑定注记）：
                    # applicable 非空才发 any_fail 且随行发条目键
                    # （app_maintenance L137-147）——「仅 any_fail 无条目键」
                    # 面不存在，face 非空判据无需含 any_fail。
                    face["any_fail"] = value == _PASS_VALUE
            elif face_kind == "ratio":
                face["ratio"][tail] = value  # 分化键原值
            else:
                face["fixgeom_min"] = value  # fixgeom 归一裕度（缺席=None 不造键）
    return tuple(
        NodeObservation(
            node_id=node,
            faces=tuple(
                NodeMaintenanceFace(
                    condition_key=condition_key,
                    kb=dict(sorted(face["kb"].items())),
                    any_fail=face["any_fail"],
                    ratio=dict(sorted(face["ratio"].items())),
                    fixgeom_min=face["fixgeom_min"],
                )
                for condition_key, face in sorted(
                    per_condition.items(),
                    key=lambda item: condition_order.index(item[0]),
                )
                if face["kb"] or face["ratio"] or face["fixgeom_min"] is not None
            ),
        )
        for node, per_condition in sorted(nodes.items())
    )


def _merge_source_b(
    plant: PlantResult,
    condition_order: tuple[str, ...],
    catalog: Mapping[str, ConstraintEntry],
    grouped: dict[tuple[str, str, str], dict[str, Any]],
) -> None:
    """源 B 并入（§3/§4——分支预算拆段〔回炉轮 PLR0912〕）：序轴迭代序
    （命中清单序=此序过滤）×越门判据（仅 0.0 计入）×kb 条目在场门
    （A2 缺席不入行）；同键并入既有桶（清单=源 B 工况清单）。"""
    for condition_key in condition_order:
        for key, raw in plant.summary.get(condition_key, {}).items():
            parsed = _split_maint_key(key)
            if parsed is None:
                continue
            node, face_kind, constraint_key = parsed
            if (
                face_kind != "kb"
                or constraint_key == _ANY_FAIL_KEY  # ⑩汇总键不入去重键族
                or float(raw) != _FAIL_VALUE  # ②命中=越门（1.0 通过不入聚合）
                or constraint_key not in catalog  # kb 条目缺席（A2）不入聚合行
            ):
                continue
            entry = catalog[constraint_key]
            param_key, severity = _kb_context(entry)
            dedup = (kb_warning_code(constraint_key), param_key, node)  # R3 推导链
            record = grouped.get(dedup)
            if record is None:
                grouped[dedup] = {
                    "source_a": None, "entry": entry, "node": node,
                    "hits": [condition_key], "severity": severity,
                }
            else:
                record["hits"].append(condition_key)  # 同键双源现：清单=源 B 工况清单
                if record["entry"] is None:
                    record["entry"] = entry


def _aggregated_warnings(
    plant: PlantResult,
    condition_order: tuple[str, ...],
    val_report: ValidationReport | None,
    catalog: Mapping[str, ConstraintEntry],
) -> tuple[AggregatedWarning, ...]:
    """两源聚合（R4——§3 全条款）：源 A 行（∅ 哨兵）+源 B 越门行（kb 条目
    在场才入）按 (code,param_key,scope) 分组合并——message 源 A 优先/
    B-only 合成（A1）；清单=源 B 工况清单（序轴迭代序）；severity=max。"""
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for warning in val_report.warnings if val_report else ():  # 源 A：报告序（首例语义载体）
        dedup = (warning.code, warning.param_key, warning.condition_key)
        record = grouped.get(dedup)
        if record is None:
            grouped[dedup] = {
                "source_a": warning, "entry": None, "node": warning.condition_key,
                "hits": [], "a_severity": warning.severity,
            }
        else:  # 回炉 d1-W2：同键多实例=首例保序（§2 message 按首例）+severity 累积 max
            record["a_severity"] = _max_severity(record["a_severity"], warning.severity)
    _merge_source_b(plant, condition_order, catalog, grouped)
    warnings: list[AggregatedWarning] = []
    # A3 响应行排序=(scope,code,param_key) 确定性冻结（≠去重键序——视图
    # 分区/重排归 FE；scope=元组第 3 位，显式 key 重排）
    for dedup in sorted(grouped, key=lambda key: (key[2], key[0], key[1])):
        code, param_key, scope = dedup
        record = grouped[dedup]
        source_a: PlantWarning | None = record["source_a"]
        hits: list[str] = record["hits"]
        hit_entry: ConstraintEntry | None = record["entry"]
        if source_a is not None:
            message = source_a.message  # ⑦同键双源现取源 A 实例（序轴前置）
            severity = record["a_severity"]  # 回炉 d1-W2：源 A 实例累积 max（非末例覆盖）
        else:
            assert hit_entry is not None  # B-only 行必有 kb 条目（A2 缺席不入行）
            message = _synthesized_message(plant, record["node"], hit_entry, hits[0])
            severity = record["severity"]
        if hit_entry is not None and source_a is not None:
            severity = _max_severity(severity, Severity(hit_entry.severity))
        warnings.append(
            AggregatedWarning(
                code=code,
                param_key=param_key,
                scope=scope,
                message=message,
                condition_keys=tuple(hits),  # ③源 A ∅ 并入不产项
                severity=severity,
            )
        )
    return tuple(warnings)


def _synthesized_message(
    plant: PlantResult, node: str, entry: ConstraintEntry, first_hit: str
) -> str:
    """B-only 行 message 合成（A1——三要素：条目键+表达式原文+首命中工况
    offline dims 实际值；字段缺席=无值形态）。"""
    field, _ = _kb_context(entry)
    snapshot = plant.conditions.get(first_hit, {}).get(node)
    value = snapshot.dims.get(field) if snapshot is not None else None
    if value is None:
        return f"kb 越门：{entry.key}——违反 {entry.expression}"
    return f"kb 越门：{entry.key}——{field}={value!r} 违反 {entry.expression}"


def build_validation_observation(
    ctx: ServiceContext, project_id: str
) -> ValidationObservationResponse:
    """校验观测正门：项目校验 → 结果集取数 → 观测投影+两源聚合（R1~R7）。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    task_id, latest = latest_calc_result(
        ctx, project_id, not_found=ValidationSourceNotFoundError
    )
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise ValidationSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    val_report = _load_validation(latest)
    diagnostics = _load_diagnostics(latest)
    condition_order = _condition_order(latest, plant)
    catalog = {
        entry.key: entry for entry in list_constraints(ctx.settings.data_dir).entries
    }
    return ValidationObservationResponse(
        project_id=project_id,
        task_id=task_id,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        engine_version=plant.repro.engine_version,
        data_version=plant.repro.data_version,
        kb_injected=diagnostics.kb_injected if diagnostics else None,
        validation_available=val_report is not None,
        conditions=condition_order,
        nodes=_observations(plant, condition_order),
        warnings=_aggregated_warnings(plant, condition_order, val_report, catalog),
    )
