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
#      （字符串/数值/列表/映射）——外部输入先过 schema 再进 IPC。
#   R2 调用映射：kind → app L4 入口（calc→run_full_calc、enumerate→
#      run_enumeration、export_batch→export_artifact；一律经 waterprint.app
#      用例面不直连 L3 子系统，UF-33）；映射表集中一处，禁止散落 if。
#   R3 进度上报：阶段百分比 + condition_key（逐工况粒度）；大结果写
#      arrow 文件返回路径句柄（§16 A6）不整包过 pickle；落盘一律
#      临时文件+同分区 rename 原子写（GR-38，UF-38）。
#   R4 取消协作：每阶段/每批迭代检查令牌；置位 → 清理临时产物 →
#      返回 cancelled 状态（不写半途结果）。
#   R5 导入零副作用：import 不创建池/不连队列（Windows spawn 安全）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - 进度队列经池 initializer 注入模块全局 _PROGRESS_QUEUE（mp.Queue
#     不能过 submit 参数——Windows spawn 实测拒；直接调用面显式传第三参）。
#   - 取消令牌=标记文件路径（cancel_token 参数）：阶段边界轮询
#     _cancelled()（core run 内长计算无协作取消钩子——UF 记档）。
#   - RunEnv 装配：core app 面无 env 装配用例且 D7 禁直连 registry，
#     本文件以 CoefficientsView 协议适配器读 data_dir 数据包（registry
#     格式镜像装载，B4 双胞胎先例；追认点登记 undefined-features-register）。
#   - R1-1 二道闸（2026-08-26）：export_batch 的 kind 白名单+out_name
#     防逃逸（无分隔符/无 ..）——payload 直注 IPC 面防线。
#   - S2 D6（2026-08-30）：export_batch items 级透传——逐项
#     core.export_artifact 附 unit_id（批级共享）/condition_key（item
#     自有）kwargs，空串归一 None（exports 单产物路径对偶口径）。
#   - DEFAULT_ASSUMPTIONS 经 waterprint.app 模块面取用（UF-33"经 app"口径）。
#   - R2-C（2026-09-02 服务端安全批·交付2）：DWG 转换原语自 services.exports
#     下沉 jobs（层序禁 jobs→services 上行，services 反向引用合法〔TaskRequest
#     先例〕）；export_batch dxf 项落盘后双产物面=可选 DWG+边车登记
#     （item.sidecars=services 预构建边车文本，ExportMeta 单源 worker 仅
#     落盘；缺块=存量零边车行为——锁用例口径）。
#   - R-1（2026-09-02 A 二审六必改）：K-05 根因解决——转换域拆件
#     jobs/dwg.py（dwg_convert 原语+batch_dwg_artifact 闸面入口：
#     D-01 落位成功才置旗/K-03 开关×登记绑定/K-04 timeout 闸），本模块
#     import 同向合法；D-02 后缀闸入 _safe_out_name（产物名防线集中）；
#     K-03 sidecars 非映射二道闸+K-02 转换前取消检查入批量挂钩。
#   - SVRB（2026-09-05 服务端批量任务面）：D2 project_path 通道——批首
#     _load_project（calc 通道同款，失败形态照搬=core 异常原样上抛）+逐项
#     _build_drawing_kwargs（jobs/export_kwargs.py 共享真源，与单产物完全
#     等价）；D3 ifc 放行（_EXPORT_KINDS+_safe_out_name ifc 特判+ifc 项边车
#     落盘）；D4 部分失败协议（逐项 try/except 收集 failures 继续，部分失败
#     =done+failures/全失败=raise 聚合首条+计数）+stage 带 unit 段+cancelled
#     outcome 携已产 files/failures（manager 灌入 result——§2.3 缺陷收口）。
#
# 【测试要求】各 kind 映射、取消清理、大结果走文件、异常序列化。
#
# 【参照】重写计划 §12.2/§16 A6/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
import multiprocessing as mp
import os
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Final, Protocol

import structlog
import yaml
from waterprint import app as core
from waterprint.contracts.condition import ConditionSet, build_condition_set
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.result_schema import deserialize, serialize
from waterprint.contracts.run_env import RunEnv

from waterprint_server.jobs.dwg import batch_dwg_artifact
from waterprint_server.jobs.export_kwargs import _build_drawing_kwargs
from waterprint_server.settings import ENGINE_VERSION

# 进度队列模块全局（R5：仅 initializer 赋值，导入期为 None——零副作用）。
_PROGRESS_QUEUE: mp.Queue[Mapping[str, Any]] | None = None
_LOGGER = structlog.get_logger(__name__)  # 边车登记告警面（转换域已拆 jobs/dwg）


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
    *.yaml 条目按名排序；键全包唯一；数值有限性 GR-02）。
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
    """GR-38 原子写：同分区临时文件 + os.replace。

    M8-A/W3：tmp 名加 uuid 唯一化——K-01 跨进程面收口（calc_workers≥2 时
    两个同参任务固定 {name}.tmp 双写互覆=Linux 混合字节损坏产物；唯一名
    后并发双写各写各 tmp，末次 replace 胜出=完整旧或新，零混合）。
    """
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
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
    tmp = rows_file.with_name(f"{rows_file.name}.{uuid.uuid4().hex}.tmp")
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


_EXPORT_KINDS: Final[tuple[str, ...]] = ("calcbook", "audit", "dxf", "estimate", "ifc")

# SVRB D4：批量项级失败捕获面（_TRIGGER_FAILURES 现实异常族先例——grep
# 门禁禁 Exception 基类捕获字面）。批共因族（InvalidSitePlanError/Invalid
# ResultError/InvalidTemplateError）有意不在项内捕获：上抛保 error_type
# 诊断映射（DOMAIN_ERROR_CODES 面）。
_ITEM_FAILURES: Final[tuple[type[BaseException], ...]] = (
    OSError, RuntimeError, ValueError, KeyError, TypeError, core.ArtifactKindNotReady,
)
_FAILURE_TEXT_LIMIT: Final[int] = 2 * 10**2  # failures error 截断长度（幂底式 200——SVRB D4）


def _safe_out_name(name: str, kind: str) -> str:
    """R1-1 二道闸：产物文件名防逃逸（无分隔符/无 .. /非空——payload 直注
    IPC 面防线；服务面已过白名单，本闸防绕过服务层直构 payload，§18）。
    D-02（R-1）：kind=dxf 强制 .dxf 后缀——防 out_name="foo.dwg" 时转换
    产物 with_suffix 同路径覆盖已交付 DXF；SVRB D3：ifc 同款单特判。"""
    if (
        not name
        or "/" in name
        or "\\" in name
        or ".." in name
        or name in {".", ".."}
        or (kind == "dxf" and not name.endswith(".dxf"))
        or (kind == "ifc" and not name.endswith(".ifc"))
    ):
        raise InvalidTaskPayloadError(
            f"导出产物名非法：{name!r}（R1-1 二道闸——无路径分隔符/无父段"
            "引用；dxf/ifc 项产物名须对应后缀〔D-02 防转换同路径覆盖〕；"
            "exports_dir 内落盘是唯一合法位置）"
        )
    return name


def _write_sidecar_text(exports_dir: Path, file_name: str, text: str) -> None:
    """R2-C：批量产物边车落盘（GR-38 原子写；文本=services 预构建）。"""
    sidecar = exports_dir / f"{file_name}.meta.json"
    tmp = sidecar.with_name(f"{sidecar.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, sidecar)
    except OSError as exc:  # WP0 R-1/G1-01 同族：登记失败不回滚已交付产物
        _LOGGER.warning(
            "export_sidecar_skipped", source=file_name, reason=f"write failed: {exc!r}"
        )


def _run_export_batch(
    payload: Mapping[str, Any], cancel_token: object, progress: _ProgressSink | None
) -> Mapping[str, Any]:
    """export_batch → app.export_artifact（逐项迭代轮询取消 R4；SVRB D2/D3/D4——头部注记）。"""
    task_id = str(payload["task_id"])
    exports_dir = Path(str(payload["exports_dir"]))
    items = list(payload.get("items", ()))
    total = max(len(items), 1)
    # SVRB D2：project_path 通道——worker 侧 load_project（calc 同款；失败
    # 形态照搬=core 异常原样上抛，任务 failed 诊断不吞）。
    project = _load_project(payload)
    files: list[str] = []
    failures: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if _cancelled(cancel_token):  # 每批迭代检查（R4：取消后无新产物落地）
            return {"state": "cancelled", "files": tuple(files), "failures": tuple(failures)}
        kind = str(item.get("kind", ""))
        if kind not in _EXPORT_KINDS:  # R1-1 二道闸：kind 白名单（IPC 面）
            raise InvalidTaskPayloadError(
                f"导出 kind {kind!r} 不在合法面 {_EXPORT_KINDS}（R1-1 二道闸）"
            )
        out_name = _safe_out_name(str(item.get("out_name", "")), kind)  # D-02 后缀闸随行
        # S2 D6+DS-06：items 级透传（空串归一 None 单产物对偶；str(x or "")
        # 防显式 None 经 str(None)="None" 透传——IPC 面不可信）。
        unit_id = str(item.get("unit_id") or "") or None
        condition_key = str(item.get("condition_key") or "") or None
        _report(task_id, _StagePoint(  # SVRB D4：stage 带 unit 段（无-unit 项省略）
            f"export:{kind}:{unit_id}" if unit_id else f"export:{kind}", index, total
        ), progress, condition_key)
        try:  # SVRB D4：单项异常→failures 收集继续（部分失败=done+failures）
            plant = deserialize(Path(str(item["result_file"])).read_bytes())
            out = exports_dir / out_name
            tmp = out.with_name(f"{out.name}.{uuid.uuid4().hex}.tmp")
            core.export_artifact(  # SVRB D2：kwargs 经 jobs/export_kwargs（单产物等价）
                kind, plant, Path(str(item["template"])), tmp,
                unit_id=unit_id, condition_key=condition_key,
                **_build_drawing_kwargs(kind, project),
            )
            os.replace(tmp, out)  # GR-38：渲染落临时文件后原子替换
            files.append(str(out))
        except _ITEM_FAILURES as exc:
            failures.append({  # error 截 _FAILURE_TEXT_LIMIT 字符（清单体积面）
                "index": index, "unit_id": unit_id, "condition_key": condition_key,
                "error": f"{type(exc).__name__}: {exc}"[:_FAILURE_TEXT_LIMIT]})
            continue
        # R2-C/R-1：dxf 批量项双产物面——sidecars 二道闸（K-03）+DXF 恒登记
        # 边车+可选 DWG（jobs.dwg 转换入口闸面集中；缺块=存量零边车行为）。
        raw_sidecars = item.get("sidecars")
        if raw_sidecars is not None and not isinstance(raw_sidecars, Mapping):
            raise InvalidTaskPayloadError(  # K-03：非映射拒（不再裸 ValueError 炸）
                f"sidecars 须为映射：{type(raw_sidecars).__name__}（IPC 面不可信"
                "——与产物名闸同防线，K-03）"
            )
        sidecars = dict(raw_sidecars or {})
        if kind == "dxf" and sidecars.get("dxf"):
            if _cancelled(cancel_token):  # K-02：转换前取消（取消后零新边车零转换）
                return {"state": "cancelled", "files": tuple(files), "failures": tuple(failures)}
            _write_sidecar_text(exports_dir, out_name, str(sidecars["dxf"]))
            dwg = batch_dwg_artifact(payload, sidecars, out)
            if dwg is not None:
                _write_sidecar_text(exports_dir, dwg.name, str(sidecars["dwg"]))
        if kind == "ifc" and sidecars.get("ifc"):  # SVRB D3：ifc 项边车（无 dwg 面）
            _write_sidecar_text(exports_dir, out_name, str(sidecars["ifc"]))
    if failures and not files:  # SVRB D4：全失败=failed（诚实性——零产物不报 done）
        raise RuntimeError(
            f"export_batch 全部 {len(failures)} 项失败——首错：{failures[0]['error']}"
        )
    return {
        "state": "done", "files": tuple(files), "failures": tuple(failures),
        "project_id": payload.get("project_id", ""),
        "design_digest": str(payload.get("design_digest", "")),  # SVRB D2 快照留痕
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
