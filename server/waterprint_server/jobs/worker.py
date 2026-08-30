"""进程池工作函数入口：序列化边界 + core 调用 + 进度上报（零业务逻辑）。

输入:  TaskRequest payload（JSON 可序列化）+ 取消令牌 + 进度队列
输出:  任务结果（JSON 可序列化）+ 进度消息序列
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/jobs/test_worker.py）
#
# 【公开接口】
#   run_task(payload: Mapping, cancel_token, progress_queue) -> Mapping
#       进程池 submit 的顶层函数（pickle 边界上的唯一函数面）
#
# 【行为规格】
#   R1 序列化边界（§18 IPC 行）：payload/结果只含经校验的基本类型
#      （字符串/数值/列表/映射）——外部输入先过 schema 再进 IPC，
#      永不 pickle 任意对象图。
#   R2 调用映射：kind → app L4 入口（calc→run_full_calc、enumerate→
#      run_enumeration、export_batch→export_artifact；SENS-B 2026-08-23
#      UF-33——一律经 waterprint.app 用例面，不直连 L3 子系统）；
#      映射表集中一处，禁止散落 if。
#   R3 进度上报：阶段百分比 + condition_key（逐工况粒度）；
#      大结果写 arrow 文件返回路径句柄（§16 A6），不整包过 pickle；
#      落盘一律临时文件+同分区 rename 原子写（GR-38，SENS-B
#      2026-08-23 UF-38）。
#   R4 取消协作：每阶段/每批迭代检查令牌；置位 → 清理临时产物 →
#      返回 cancelled 状态（不写半途结果）。
#   R5 导入零副作用：本模块 import 不创建池/不连队列（Windows
#      spawn 重复导入安全，AGENTS §1）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - 进度队列经进程池 initializer（_init_progress_queue）注入模块全局
#     _PROGRESS_QUEUE（mp.Queue 不能过 submit 参数——Windows spawn 标准
#     pickle 实测拒；R5 导入零副作用不受扰：全局在初始化期而非导入期
#     赋值）。直接调用面（单元测试）可显式传第三参。
#   - 取消令牌=标记文件路径（cancel_token 参数）：阶段边界轮询
#     _cancelled()（core run 内长计算无协作取消钩子——UF 记档）。
#   - RunEnv 装配：core app 面无 env 装配用例且 D7 禁直连 registry，
#     本文件以 CoefficientsView 协议适配器（L0 契约协议面）读
#     data_dir 数据包（registry 格式镜像装载，B4 双胞胎先例）——
#     追认点已登记 undefined-features-register（SERVER 批）。
#   - R1-1 二道闸（2026-08-26）：export_batch 的 kind 白名单+
#     out_name 防逃逸（无分隔符/无 ..）——payload 直注 IPC 面防线。
#   - S2 D6（2026-08-30 落盘化批）：export_batch items 级 options
#     透传——逐项 core.export_artifact 附 unit_id/condition_key kwargs
#     （空串归一 None——exports 单产物路径 condition_key or None 对偶
#     口径；payload items 每项带 unit_id 批级共享+condition_key item
#     自有，exports.create_export 批量路径同批收口）。
#   - DEFAULT_ASSUMPTIONS 经 waterprint.app 模块面取用（app 为
#     _engine_params 已装载的同名属性——UF-33"经 app"口径）。
#
# 【测试要求】各 kind 映射、取消清理、大结果走文件、异常序列化
#   （领域异常诊断字段完整）。
#
# 【参照】重写计划 §12.2/§16 A6/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
import multiprocessing as mp
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Final, Protocol

import yaml
from waterprint import app as core
from waterprint.contracts.condition import ConditionSet, build_condition_set
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.result_schema import deserialize, serialize
from waterprint.contracts.run_env import RunEnv

from waterprint_server.settings import ENGINE_VERSION

# 进度队列模块全局（R5：仅 initializer 赋值，导入期为 None——零副作用）。
_PROGRESS_QUEUE: mp.Queue[Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class _StagePoint:
    """进度点位（R3）：阶段名 + 序号 + 阶段总数。"""

    stage: str
    index: int
    total: int


# 阶段表（进度分母=len(阶段表)，percent 幂商式——ADR-009 白名单 {0,1,2,10}）。
_STAGES: Final[dict[str, tuple[str, ...]]] = {
    "calc": ("load", "run", "serialize"),
    "enumerate": ("load", "run", "rows"),
}
# 引擎版本标识：settings.ENGINE_VERSION（与 pyproject version 同源）


class InvalidTaskPayloadError(ValueError):
    """任务 payload 非法（未知 kind/缺键）——领域异常（GR-11 族）。"""


class DataPackError(ValueError):
    """数据包装载非法（manifest/条目形态）——领域异常（GR-11 族）。"""


def _init_progress_queue(queue: mp.Queue[Mapping[str, Any]]) -> None:
    """进程池 initializer 入口：进度队列注入（Windows spawn 正门，R3）。"""
    global _PROGRESS_QUEUE  # noqa: PLW0603  # 池 initializer 注入口（R5 唯一写者）
    _PROGRESS_QUEUE = queue


class _CoefficientEntry:
    """系数条目视图（CoefficientsView.get 的返回协议面：value/unit/source/note）。"""

    def __init__(self, value: float, unit: str, source: str, note: str) -> None:
        self.value = value
        self.unit = unit
        self.source = source
        self.note = note


class _YamlCoefficients:
    """CoefficientsView 协议适配器：registry 数据包格式镜像装载（B4 双胞胎）。

    只实现 L0 协议查询面（data_version/get/keys/require_keys）——装载
    语义与 registry.load_coefficients 同款（manifest.yaml 版本头 + 其余
    *.yaml 条目文件按名排序；键全包唯一；数值有限性 GR-02）。
    """

    def __init__(self, directory: Path) -> None:
        manifest = directory / "manifest.yaml"
        if not manifest.is_file():
            raise DataPackError(f"系数包缺 manifest.yaml：{directory}（装载面只认数据包目录）")
        manifest_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest_data, Mapping) or not isinstance(
            manifest_data.get("data_version"), str
        ):
            raise DataPackError(f"系数包 manifest.yaml 形态非法（缺 data_version）：{manifest}")
        self.data_version = manifest_data["data_version"]
        self._entries: dict[str, _CoefficientEntry] = {}
        for entry_file in sorted(directory.glob("*.yaml")):
            if entry_file.name == "manifest.yaml":
                continue
            raw = yaml.safe_load(entry_file.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise DataPackError(f"条目文件须为列表：{entry_file}")
            for item in raw:
                if not isinstance(item, Mapping):
                    raise DataPackError(f"条目须为对象：{entry_file} 内 {item!r}")
                key = item.get("key")
                value = item.get("value")
                if not isinstance(key, str) or not key or not isinstance(value, (int, float)):
                    raise DataPackError(f"条目缺 key/value 基本字段：{entry_file} 内 {item!r}")
                if isinstance(value, float) and not isfinite(value):
                    raise DataPackError(f"条目数值非有限（GR-02）：{key}={value!r}")
                if key in self._entries:
                    raise DataPackError(f"系数键重复（键全包唯一）：{key}（{entry_file.name}）")
                self._entries[key] = _CoefficientEntry(
                    float(value),
                    str(item.get("unit", "")),
                    str(item.get("source", "")),
                    str(item.get("note", "")),
                )
        if not self._entries:
            raise DataPackError(f"系数包无条目文件（GR-14 空集显式拒）：{directory}")

    def get(self, key: str) -> _CoefficientEntry:
        """键查询（缺键=KeyError——与 registry.Coefficients 同语义）。"""
        return self._entries[key]

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """前缀键枚举（排序确定性）。"""
        return tuple(sorted(key for key in self._entries if key.startswith(prefix)))

    def require_keys(self, keys: object) -> None:
        """在册断言（协议面）。"""
        if isinstance(keys, (list, tuple)):
            for key in keys:
                if key not in self._entries:
                    raise DataPackError(f"系数键在册断言失败：{key!r}")


class _ProgressSink(Protocol):
    """进度接收面（mp.Queue 或测试替身，结构 {task_id, percent, stage}）。"""

    def put(self, message: Mapping[str, Any]) -> None: ...


def _report(
    task_id: str, point: _StagePoint, queue: _ProgressSink | None,
    condition_key: str | None = None,
) -> None:
    """阶段进度上报（R3：percent=(index+1)/(total+1) 幂商式，UF-28 口径挂账）。"""
    if queue is None:
        return
    queue.put(
        {
            "task_id": task_id,
            "percent": (point.index + 1) / (point.total + 1),
            "stage": point.stage,
            "condition_key": condition_key,
        }
    )


def _cancelled(cancel_token: object) -> bool:
    """取消令牌轮询（R4：标记文件存在=已请求取消）。"""
    return isinstance(cancel_token, (str, Path)) and Path(cancel_token).exists()


def _atomic_write_bytes(path: Path, data: bytes) -> Path:
    """GR-38 原子写：同分区临时文件 + os.replace。"""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return path


def _load_project(payload: Mapping[str, Any]) -> ProjectFile:
    """项目装载（经 app 正门——D2 双闸与 M-3 版本门随之生效）。"""
    return core.load_project(Path(str(payload["project_path"])))


def _build_env(data_dir: Path, project: ProjectFile) -> RunEnv:
    """RunEnv 装配（系数适配器 + 假设合成视图 + UF-10 版本聚合）。"""
    coefficients = _YamlCoefficients(data_dir / "coefficients")
    versions = {"coefficients": coefficients.data_version}
    price_manifest = data_dir / "unit_prices" / "manifest.yaml"
    if price_manifest.is_file():
        raw = yaml.safe_load(price_manifest.read_text(encoding="utf-8"))
        if isinstance(raw, Mapping) and isinstance(raw.get("price_data_version"), str):
            versions["unit_prices"] = raw["price_data_version"]
    assumptions = {entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS}
    assumptions.update(project.design.assumption_overrides)
    return RunEnv(
        engine_version=ENGINE_VERSION,
        data_version="+".join(
            f"{name}@{versions[name]}" for name in sorted(versions)
        ),
        assumptions=assumptions,
        coefficients=coefficients,
        price_book={},  # M3 单价包装载后收紧（GR-21 注记，RunEnv 规格）
        trace_sink=None,
        engine_params={},  # app._completed_env 按缺 loop.* 补齐（UF-08 投影）
    )


def _run_calc(
    payload: Mapping[str, Any], cancel_token: object, progress: _ProgressSink | None
) -> Mapping[str, Any]:
    """calc → app.run_full_calc（结果 serialize 落盘返句柄，R3）。"""
    task_id = str(payload["task_id"])
    stages = _STAGES["calc"]
    _report(task_id, _StagePoint("load", 0, len(stages)), progress)
    project = _load_project(payload)
    env = _build_env(Path(str(payload["data_dir"])), project)
    conditions = build_condition_set([str(u) for u in payload.get("conditions", ())])
    if _cancelled(cancel_token):
        return {"state": "cancelled"}
    _report(task_id, _StagePoint("run", 1, len(stages)), progress)
    bundle = core.run_full_calc(project, conditions, env)
    if _cancelled(cancel_token):  # 结果落地前检查（R4：不写半途结果）
        return {"state": "cancelled"}
    _report(task_id, _StagePoint("serialize", 2, len(stages)), progress)
    result_file = _atomic_write_bytes(
        Path(str(payload["artifacts_dir"])) / f"calc-{task_id}.json",
        serialize(bundle.plant),
    )
    return {
        "state": "done",
        "result_file": str(result_file),
        "design_hash": bundle.repro.design_hash,
        "engine_version": bundle.repro.engine_version,
        "data_version": bundle.repro.data_version,
        "condition_keys": [ConditionSet.key(c) for c in conditions.iter_all()],
        "project_id": payload.get("project_id", ""),
    }


def _run_enumerate(
    payload: Mapping[str, Any], cancel_token: object, progress: _ProgressSink | None
) -> Mapping[str, Any]:
    """enumerate → app.run_enumeration（万级行落 arrow 文件返路径句柄，R3）。"""
    task_id = str(payload["task_id"])
    stages = _STAGES["enumerate"]
    _report(task_id, _StagePoint("load", 0, len(stages)), progress)
    project = _load_project(payload)
    env = _build_env(Path(str(payload["data_dir"])), project)
    conditions = build_condition_set([str(u) for u in payload.get("conditions", ())])
    raw_options = payload.get("options") or {}
    options = core.EnumerationOptions(
        constraints=tuple(
            core.Constraint(
                key=str(item["key"]),
                expression=str(item["expression"]),
                source=str(item["source"]),
            )
            for item in raw_options.get("constraints", ())
        ),
        sort_by=str(raw_options.get("sort_by", "margin_min")),
        ascending=bool(raw_options.get("ascending", False)),
        limit=int(raw_options["limit"]) if raw_options.get("limit") is not None else None,
    )
    if _cancelled(cancel_token):
        return {"state": "cancelled"}
    _report(task_id, _StagePoint("run", 1, len(stages)), progress)
    outcome = core.run_enumeration(
        project, str(payload["unit_id"]), conditions, env, options
    )
    if _cancelled(cancel_token):  # 行文件落地前检查（R4）
        return {"state": "cancelled"}
    _report(task_id, _StagePoint("rows", 2, len(stages)), progress)
    rows_file = Path(str(payload["artifacts_dir"])) / f"enum-{task_id}.feather"
    tmp = rows_file.with_name(rows_file.name + ".tmp")
    outcome.rows.to_feather(tmp)
    os.replace(tmp, rows_file)
    diagnosis = None
    if outcome.diagnosis is not None:  # 无解交付：done + feasible_count=0 合法（R4）
        diagnosis = {
            "minimal_conflicts": [
                sorted(conflict) for conflict in outcome.diagnosis.minimal_conflicts
            ],
            "fail_counts": dict(outcome.diagnosis.fail_counts),
            "suggestions": [dataclasses.asdict(s) for s in outcome.diagnosis.suggestions],
        }
    return {
        "state": "done",
        "rows_file": str(rows_file),
        "total_feasible": int(outcome.total_feasible),
        "feasible_count": int(outcome.total_feasible),
        "truncated": bool(outcome.truncated),
        "diagnosis": diagnosis,
        "columns": [str(column) for column in outcome.rows.columns],
        "grid_fields": list(outcome.grid.fields),
        "project_id": payload.get("project_id", ""),
    }


_EXPORT_KINDS: Final[tuple[str, ...]] = ("calcbook", "audit", "dxf", "estimate")


def _safe_out_name(name: str) -> str:
    """R1-1 二道闸：产物文件名防逃逸（无分隔符/无 .. /非空——payload 直注防线）。

    服务面已过 _deterministic_name 四分量白名单；本闸防的是绕过服务层
    直构 payload 的 IPC 面（worker 是 pickle 边界，入参即不可信——§18）。
    """
    if (
        not name
        or "/" in name
        or "\\" in name
        or ".." in name
        or name in {".", ".."}
    ):
        raise InvalidTaskPayloadError(
            f"导出产物名非法：{name!r}（R1-1 二道闸——无路径分隔符/无父段"
            "引用；exports_dir 内落盘是唯一合法位置）"
        )
    return name


def _run_export_batch(
    payload: Mapping[str, Any], cancel_token: object, progress: _ProgressSink | None
) -> Mapping[str, Any]:
    """export_batch → app.export_artifact（逐项迭代间轮询取消，R4）。"""
    task_id = str(payload["task_id"])
    exports_dir = Path(str(payload["exports_dir"]))
    items = list(payload.get("items", ()))
    total = max(len(items), 1)
    files: list[str] = []
    for index, item in enumerate(items):
        if _cancelled(cancel_token):  # 每批迭代检查（R4：取消后无新产物落地）
            return {"state": "cancelled", "files": tuple(files)}
        kind = str(item.get("kind", ""))
        if kind not in _EXPORT_KINDS:  # R1-1 二道闸：kind 白名单（IPC 面）
            raise InvalidTaskPayloadError(
                f"导出 kind {kind!r} 不在合法面 {_EXPORT_KINDS}（R1-1 二道闸）"
            )
        out_name = _safe_out_name(str(item.get("out_name", "")))
        _report(
            task_id,
            _StagePoint(f"export:{kind}", index, total),
            progress,
        )
        plant = deserialize(Path(str(item["result_file"])).read_bytes())
        out = exports_dir / out_name
        tmp = out.with_name(out.name + ".tmp")
        # S2 D6：items 级透传——unit_id（批级共享，空串归一 None=core
        # unit_id-None 闸「全厂总图归 M5 site_plan」诚实 501 面）+
        # condition_key（item 自有，空串归一 None=core 缺省 design 档
        # +UserWarning）——exports.create_export 单产物路径同款口径。
        # R2 R3（DS-06）：str(x or "") 先归一——防 payload 显式 None 经
        # str(None)="None" 透传（IPC 面不可信原则）。
        core.export_artifact(
            kind,
            plant,
            Path(str(item["template"])),
            tmp,
            unit_id=str(item.get("unit_id") or "") or None,
            condition_key=str(item.get("condition_key") or "") or None,
        )
        os.replace(tmp, out)  # GR-38：渲染落临时文件后原子替换
        files.append(str(out))
    return {
        "state": "done",
        "files": tuple(files),
        "project_id": payload.get("project_id", ""),
    }


# kind → 用例映射表（R2：集中一处；一律经 waterprint.app，UF-33）。
_TaskRunner = Callable[[Mapping[str, Any], object, _ProgressSink | None], Mapping[str, Any]]
_KIND_RUNNERS: Final[dict[str, _TaskRunner]] = {
    "calc": _run_calc,
    "enumerate": _run_enumerate,
    "export_batch": _run_export_batch,
}


def run_task(
    payload: Mapping[str, Any],
    cancel_token: object = None,
    progress_queue: _ProgressSink | None = None,
) -> Mapping[str, Any]:
    """进程池顶层唯一函数面（pickle 边界；R1 结果只含基本类型）。"""
    progress = progress_queue if progress_queue is not None else _PROGRESS_QUEUE
    if _cancelled(cancel_token):
        return {"state": "cancelled"}
    kind = payload.get("kind")
    runner = _KIND_RUNNERS.get(str(kind)) if isinstance(kind, str) else None
    if runner is None:
        raise InvalidTaskPayloadError(
            f"未知任务 kind：{kind!r}（合法面 {sorted(_KIND_RUNNERS)}）"
        )
    return runner(payload, cancel_token, progress)
