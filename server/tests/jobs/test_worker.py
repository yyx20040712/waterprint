"""jobs worker 镜像测试：序列化边界、取消协作、大结果走文件。

输入:  waterprint_server.jobs.worker 公开符号
输出:  进程边界契约断言（§18 IPC 行 / §16 A6）
"""

from __future__ import annotations

import importlib
import multiprocessing as mp
import shutil
from pathlib import Path

import pandas as pd
import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task")

pytestmark = [
    pytest.mark.skipif(
        run_task is None,
        reason="实现未就绪：waterprint_server.jobs.worker（服务层 M2）",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def _hh1_stale_closed_queue_residue():
    """HH1（1A7 批）防御锚：模块级残留=前序测试 manager.shutdown 后的
    worker._PROGRESS_QUEUE 全局形态（Manager.start 注入全局、shutdown 关
    队列不清全局——跨测试残留；jobs conftest per-test 前清隔离前，本模块
    直调 run_task(payload, None, None) 三件稳定踩「mp.Queue is closed」，
    即 exp-hygiene P7 在册组合子集 3 红实录的复现机制）。

    植入一个已关闭队列=持续施加历史故障条件：隔离（conftest 每测试前清
    None）在则本模块全绿；隔离被移除则直调件复红——防御断言钉死该序。"""
    stale = mp.Queue()
    stale.close()
    _mod._PROGRESS_QUEUE = stale  # noqa: SLF001  # 残留植入（隔离面红证载体）
    yield
    _mod._PROGRESS_QUEUE = None  # noqa: SLF001  # 模块收尾清位（不外泄）


def test_worker_entry_imports_without_side_effects() -> None:
    """R5 接线断言（骨架期即可验）：模块导入零副作用（Windows spawn 安全）。

    实现合入后本断言自动生效：导入 waterprint_server.jobs.worker 不得
    创建进程池/连接队列/打印输出。
    """
    import os
    import subprocess
    import sys

    code = "import waterprint_server.jobs.worker as w; assert callable(w.run_task)"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", f"导入期产生副作用输出: {result.stdout!r}"


def _cass_project_file(tmp_path: Path) -> Path:
    """CASS 项目落盘（worker 正门载荷——app.save_project 确定性序列化）。"""
    from waterprint import app as core
    from waterprint.contracts.project_schema import (
        DesignState,
        Metadata,
        ProjectFile,
        ViewState,
    )

    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "NH3N": 26.0,
                    "TN": 43.0,
                    "TP": 6.5,
                },
                "municipal_cass": {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                }
            ],
        ),
        view=ViewState(timestamp="2026-08-26T00:00:00Z"),
        metadata=Metadata(
            format_version="1.0",
            content_hash="0" * 64,
            engine_version="0",
            data_version="0",
        ),
    )
    path = tmp_path / "enum.wp.json"
    core.save_project(project, path)
    return path


def test_large_result_returns_file_handle_wiring(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R3 接线断言：万级枚举结果经 arrow 文件返回路径句柄（不整包过 pickle）。"""
    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "enumerate",
        "task_id": "rows-handle-probe",
        "project_id": "p",
        "project_path": str(_cass_project_file(tmp_path)),
        "unit_id": "municipal_cass",
        "conditions": [],
        "options": {},
        "data_dir": str(test_settings.data_dir),
        "artifacts_dir": str(artifacts),
    }
    outcome = run_task(payload, None, None)
    assert outcome["state"] == "done"
    assert "rows_file" in outcome and "feasible_count" in outcome  # 路径句柄面
    assert "rows" not in outcome  # 不整包内联（§16 A6：万级行禁过 pickle 大数组）
    rows_file = Path(str(outcome["rows_file"]))
    assert rows_file.is_file() and rows_file.suffix == ".feather"  # arrow 文件落盘
    frame = pd.read_feather(rows_file)  # 按需重载（分页消费面）
    assert len(frame) == outcome["feasible_count"]
    assert len(frame) >= 1  # CASS manifest 网格非空（数据面前提）


def test_enumerate_grid_fields_object_payload(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """B2②：grid_fields 载荷=对象数组 [{key,dim,label_zh}]（dim/label_zh 自该
    单元 manifest.params 按 field_id 查；label_zh 真源缺失=None 直传——禁
    field_id 降级填充，显示兜底归 webapp）。CASS 二维网格锚定值。"""
    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "enumerate",
        "task_id": "grid-fields-probe",
        "project_id": "p",
        "project_path": str(_cass_project_file(tmp_path)),
        "unit_id": "municipal_cass",
        "conditions": [],
        "options": {},
        "data_dir": str(test_settings.data_dir),
        "artifacts_dir": str(artifacts),
    }
    outcome = run_task(payload, None, None)
    assert outcome["state"] == "done"
    grid_fields = outcome["grid_fields"]
    assert [item["key"] for item in grid_fields] == ["n_pool", "t_cycle"]  # field_id 序
    assert all(set(item) == {"key", "dim", "label_zh"} for item in grid_fields)  # 三键恰等
    assert [(item["dim"], item["label_zh"]) for item in grid_fields] == [
        ("DIMENSIONLESS", "池数（格）"),
        # 参数面单位批（2026-09-12 用户裁定）：t_cycle 翻 TIME_H（h 档）
        ("TIME_H", "运行周期"),
    ]  # manifest 真源投影（dim=DimKey 枚举名；label_zh=C1 填充值）


def test_calc_job_injects_kb_constraints(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """kbwire：calc job 数据装配注入 constraint_kb——offline 工况 summary 含
    kb 键（fail-fast 全量 34 条注入，face 自筛；baseline 帧零 maint 键）。"""
    from waterprint.contracts.result_schema import deserialize

    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    outcome = run_task(
        {
            "kind": "calc",
            "task_id": "kb-inject-probe",
            "project_id": "p",
            "project_path": str(_cass_project_file(tmp_path)),
            "conditions": ["municipal_cass"],
            "data_dir": str(test_settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert outcome["state"] == "done"
    plant = deserialize(Path(str(outcome["result_file"])).read_bytes())
    offline = plant.summary["design_offline_municipal_cass"]
    assert any(key.startswith("maint.municipal_cass.kb.") for key in offline)
    assert "maint.municipal_cass.kb.any_fail" in offline  # 汇总键同域
    assert not any(key.startswith("maint.") for key in plant.summary["design"])


def test_calc_job_missing_kb_fails_as_data_defect(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R3（回炉 d1-W1）：calc 失败路径锚——缺 constraint_kb → InvalidConstraintError
    自 run_task 传播（manager failed 收编面=future.exception()→error_type=类名）。"""
    from waterprint.solution.constraints import InvalidConstraintError

    data_dir = tmp_path / "kb-less-data"
    shutil.copytree(test_settings.data_dir, data_dir, ignore=shutil.ignore_patterns("constraint_kb"))
    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "calc", "task_id": "kb-missing-probe", "project_id": "p",
        "project_path": str(_cass_project_file(tmp_path)), "conditions": [],
        "data_dir": str(data_dir), "artifacts_dir": str(artifacts)}
    with pytest.raises(InvalidConstraintError, match="constraint_kb 文件缺失"):
        run_task(payload, None, None)


def test_unknown_kind_rejected_at_serialization_boundary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """R1 镜像缺失收口：未知 kind 在 pickle 边界即拒（禁静默空结果）。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    with pytest.raises(InvalidTaskPayloadError, match="未知任务 kind"):
        run_task({"kind": "nonsense", "task_id": "x"}, None, None)


def test_export_batch_second_gate_rejects_escape_writing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """AU-1/R1-1 二道闸：payload 直注的 kind 穿越/out_name 逃逸在 worker 即拒。"""
    from waterprint_server.jobs.worker import InvalidTaskPayloadError

    project_path = str(_cass_project_file(tmp_path))  # SVRB D2：批首装载正门真源
    base = {
        "kind": "export_batch",
        "task_id": "gate",
        "project_path": project_path,
        "exports_dir": str(tmp_path / "gate-out"),
    }
    with pytest.raises(InvalidTaskPayloadError, match="二道闸"):  # kind 含路径段
        run_task(
            {**base, "items": [{"kind": "calcbook/../../evil", "out_name": "ok.xlsx"}]},
            None,
            None,
        )
    for evil_name in ("a/../../evil.xlsx", "..\\..\\evil.xlsx", "../../deep.xlsx", ""):
        with pytest.raises(InvalidTaskPayloadError, match="产物名非法"):
            run_task(
                {**base, "items": [{"kind": "calcbook", "out_name": evil_name}]},
                None,
                None,
            )
    assert not (tmp_path / "gate-out").exists()  # 二道闸拒于任何落盘之前


def test_export_batch_items_pass_unit_and_condition_to_core(
    test_settings, tmp_path, monkeypatch  # type: ignore[no-untyped-def]
) -> None:
    """S2 D6 接线断言：批量 items 逐项透传 unit_id/condition_key 到 core。

    空串归一 None（单产物路径同款口径——exports.create_export
    condition_key or None 对偶面）；deserialize 正门真跑（真 calc 结果
    文件作 result_file——R1 序列化边界实载荷面）。
    """
    from waterprint import app as core

    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    project_path = str(_cass_project_file(tmp_path))
    calc = run_task(
        {
            "kind": "calc",
            "task_id": "passthrough-calc",
            "project_id": "p",
            "project_path": project_path,
            "conditions": [],
            "data_dir": str(test_settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert calc["state"] == "done"
    captured: list[tuple[str, object, object]] = []

    def _fake_export(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口（core.export_artifact 公开面）
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        captured.append((kind, unit_id, condition_key))
        Path(out).write_bytes(b"artifact")  # 替身落占位（GR-38 rename 面由真码执行）

    monkeypatch.setattr(core, "export_artifact", _fake_export)
    out_dir = tmp_path / "out"
    out_dir.mkdir()  # worker 面不建 exports_dir（服务装配期 ensure_directories 正门）
    result = run_task(
        {
            "kind": "export_batch",
            "task_id": "passthrough-batch",
            # SVRB D2：project_path 通道（worker load_project——kwargs 组装真源）
            "project_path": project_path,
            "exports_dir": str(out_dir),
            "items": [
                {
                    "kind": "dxf",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "a.dxf",
                    "unit_id": "municipal_cass",
                    "condition_key": "design",
                },
                {
                    "kind": "calcbook",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "b.xlsx",
                    "unit_id": "",
                    "condition_key": "",
                },
                {
                    # exp-audit-20260930：显式 None 归一载体 audit→ifc 换载
                    # （audit 项改分流 flows.audit_render_flow 零 kwargs 面——
                    # 归一断言须在仍经 core.export_artifact 的 kind 上成立；
                    # audit 分流面归 routers/test_exports_audit.py E2E）。
                    "kind": "ifc",
                    "result_file": calc["result_file"],
                    "template": "unused",
                    "out_name": "c.ifc",
                    "unit_id": None,  # R2 R3（DS-06）：显式 None 防 str(None)="None" 透传
                    "condition_key": None,
                },
            ],
        },
        None,
        None,
    )
    assert result["state"] == "done"
    assert captured == [
        ("dxf", "municipal_cass", "design"),  # items 级透传（S2 D6）
        ("calcbook", None, None),  # 空串归一 None（单产物同款口径）
        ("ifc", None, None),  # 显式 None 归一 None（IPC 面不可信——DS-06；exp-audit 载体换载）
    ]
    assert sorted(str(path.name) for path in (tmp_path / "out").iterdir()) == [
        "a.dxf",
        "b.xlsx",
        "c.ifc",
    ]  # 原子替换落位（.tmp 已清）


def test_server_env_assembly_stamps_engine_version(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """W-5（批6l 回炉）：server 侧 RunEnv 装配恒盖 ENGINE_VERSION 章——
    防未来 app.load_run_env 新调用点漏传覆写位静默产 core 串致 golden 漂移
    （worker._build_env 与 services.design_map._env 两装配面同钉）。"""
    from waterprint_server.jobs import worker as worker_mod
    from waterprint_server.services import design_map as dm_mod
    from waterprint_server.settings import ENGINE_VERSION

    project = worker_mod.core.load_project(_cass_project_file(tmp_path))
    for env in (
        worker_mod._build_env(test_settings.data_dir, project),  # noqa: SLF001  # 装配面私有直测（test_site 先例）
        dm_mod._env(test_settings.data_dir, project),  # noqa: SLF001  # 同上
    ):
        assert env.engine_version == ENGINE_VERSION
        assert "coefficients@" in env.data_version  # UF-10 聚合面在场（design_map 收敛后补全）


def test_calc_job_writes_validation_artifact(test_settings, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """2A1 D2：calc 落第三并列 artifact calc-val-{task_id}.json+record 增
    val_file 键（ADR-012 D1 诊断并列件同款——同 task_id 命名绑定+原子写；
    源 A 报告内容锚=deserialize 往返+serialize 字节恒等〔回炉 d1-N6a：
    内容级断言非裸类型〕）。"""
    from waterprint.contracts.validation import (
        ValidationReport,
        deserialize_validation,
        serialize_validation,
    )

    artifacts = test_settings.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    outcome = run_task(
        {
            "kind": "calc",
            "task_id": "val-artifact-probe",
            "project_id": "p",
            "project_path": str(_cass_project_file(tmp_path)),
            "conditions": ["municipal_cass"],
            "data_dir": str(test_settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert outcome["state"] == "done"
    assert "val_file" in outcome  # record 增键（manager 灌入 status.result 面）
    val_file = Path(str(outcome["val_file"]))
    assert val_file.name == "calc-val-val-artifact-probe.json"  # 同 task_id 命名绑定
    assert val_file.is_file()
    assert val_file != Path(str(outcome["result_file"]))
    assert val_file != Path(str(outcome["diag_file"]))  # 三并列件互异
    payload = val_file.read_bytes()
    report = deserialize_validation(payload)  # 正门往返
    assert isinstance(report, ValidationReport)  # 源 A 报告面（声明级一次）
    assert serialize_validation(report) == payload  # 往返 serialize 字节恒等（内容锚）
