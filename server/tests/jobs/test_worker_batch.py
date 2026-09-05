"""export_batch worker SVRB 镜像测试：project_path 通道/部分失败协议/进度段。

输入:  waterprint_server.jobs.worker（run_task export_batch 面）
输出:  批量任务执行契约断言（载荷通道/逐项 kwargs/终态判定/SSE stage）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（SVRB 服务端批量任务面 2026-09-05·server 通道笔）
#
# 【覆盖面】
#   - D2 project_path 通道：worker load_project→逐项 _build_drawing_kwargs
#     ——kwargs 面与单产物路径完全等价（dxf=site_design、ifc=
#     assumptions+site_design、余 kind 空）；
#   - D4 部分失败协议：单项异常→failures 收集继续；部分失败=done+
#     failures；全失败=raise（任务 failed——诚实性：零产物不报完成）；
#   - D4 进度 stage 带 unit 段（export:{kind}:{unit}；无-unit 项省略）；
#   - D3 ifc 放行面：_EXPORT_KINDS 增 ifc+_safe_out_name .ifc 后缀闸；
#   - 取消 outcome 携已产 files/failures（manager 灌入 result 的载荷源）。
# 【替身口径】core.export_artifact monkeypatch 替身（test_worker.py 先例
#   ——真 calc 结果文件经 deserialize 正门；GR-38 rename 由真码执行）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.jobs.worker")
run_task = getattr(_mod, "run_task")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = [
    pytest.mark.skipif(
        run_task is None,
        reason="实现未就绪：waterprint_server.jobs.worker（服务层）",
    ),
    pytest.mark.anyio,
]


@pytest.fixture(autouse=True)
def _progress_queue_guard():
    """进度队列全局还原（test_worker_dwg.py 先例——Manager 注入面防泄漏）。"""
    prior = _mod._PROGRESS_QUEUE  # noqa: SLF001  # 快照（注入口全局）
    yield
    _mod._PROGRESS_QUEUE = prior  # noqa: SLF001  # 还原（基线动态零漂移）


async def _project_and_result(service_ctx, cass_payload):  # type: ignore[no-untyped-def]
    """真项目路径+真 calc 结果（worker 正门实载荷——两通道同源前置）。"""
    outcome = projects_mod.create_project(service_ctx, {"project": cass_payload})
    project_path = str(service_ctx.projects_dir / f"{outcome.project_id}.wp.json")
    artifacts = service_ctx.exports_dir / "tasks"
    artifacts.mkdir(parents=True, exist_ok=True)
    calc = run_task(
        {
            "kind": "calc",
            "task_id": "svrb-calc",
            "project_id": outcome.project_id,
            "project_path": project_path,
            "conditions": [],
            "data_dir": str(service_ctx.settings.data_dir),
            "artifacts_dir": str(artifacts),
        },
        None,
        None,
    )
    assert calc["state"] == "done"
    return project_path, str(calc["result_file"])


def _batch_payload(  # 前置束参数束（test_worker_dwg 同款先例）
    project_path: str, result_file: str, exports_dir: Path,
    items: list[dict[str, object]],
) -> dict[str, object]:
    """批量载荷构造（project_path 通道+design_digest 留痕面全携；
    result_file 统一注入真值——worker deserialize 正门实载荷）。"""
    return {
        "kind": "export_batch",
        "task_id": "svrb-batch",
        "project_id": "p-svrb",
        "project_path": project_path,
        "design_digest": "d" * 16,
        "exports_dir": str(exports_dir),
        "items": [{**item, "result_file": result_file} for item in items],
    }


def _item(kind: str, out_name: str, **extra: object) -> dict[str, object]:
    """批量项构造（template 恒占位——替身不消费真渲染）。"""
    return {
        "kind": kind,
        "template": "unused",
        "out_name": out_name,
        **extra,
    }


async def test_export_batch_project_path_channel_passes_drawing_kwargs_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D2 接线断言：worker load_project（project_path）→逐项 kwargs 与
    单产物路径完全等价（dxf=site_design/ifc=assumptions+site_design/余空）。"""
    from waterprint import app as core

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    captured: list[tuple[str, dict[str, object]]] = []

    def _capture(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口（core.export_artifact 公开面）
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        captured.append((kind, extra))
        Path(out).write_bytes(b"svrb")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _capture)
        result = run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [
                    _item("dxf", "a.dxf", unit_id="municipal_cass", condition_key="design"),
                    _item("ifc", "b.ifc", unit_id="", condition_key="design"),
                    _item("calcbook", "c.xlsx"),
                ],
            ),
            None,
            None,
        )
    assert result["state"] == "done"
    assert [kind for kind, _ in captured] == ["dxf", "ifc", "calcbook"]
    assert set(captured[0][1]) == {"site_design"}  # dxf 恰 site_design
    assert set(captured[1][1]) == {"assumptions", "site_design"}  # ifc 双参
    assert captured[2][1] == {}  # 余 kind 空 dict（单产物对偶口径）
    expected = core.load_project(Path(project_path))  # load 自 project_path 实证
    assert captured[0][1]["site_design"] == expected.design.site
    assert captured[1][1]["site_design"] == expected.design.site
    assert dict(captured[1][1]["assumptions"]) == {  # DEFAULT_ASSUMPTIONS 合成视图
        entry.key: entry.default for entry in core.DEFAULT_ASSUMPTIONS
    }


async def test_export_batch_partial_failure_done_with_failures_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D4 接线断言：单项异常→failures 收集继续；部分失败=done+failures
    （result schema：index/unit_id/condition_key/error 截 200 字符）。"""
    from waterprint import app as core

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def _flaky(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        if condition_key == "bad":
            raise ValueError("injected item failure (SVRB partial)")
        Path(out).write_bytes(b"ok")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _flaky)
        result = run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [
                    _item("dxf", "a.dxf", unit_id="u1", condition_key="design"),
                    _item("dxf", "b.dxf", unit_id="u2", condition_key="bad"),
                    _item("dxf", "c.dxf", unit_id="u3", condition_key="avg"),
                ],
            ),
            None,
            None,
        )
    assert result["state"] == "done"  # 部分失败=done（非 failed）
    assert len(result["files"]) == 2  # 成功项照常落盘
    failures = list(result["failures"])
    assert len(failures) == 1
    assert set(failures[0]) == {"index", "unit_id", "condition_key", "error"}
    assert failures[0]["index"] == 1
    assert failures[0]["unit_id"] == "u2"
    assert failures[0]["condition_key"] == "bad"
    assert "ValueError" in str(failures[0]["error"])
    assert len(str(failures[0]["error"])) <= 200  # 截 200 字符


async def test_export_batch_all_failures_raises_aggregate_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D4 接线断言：全失败→raise（任务 failed——error=聚合首条+计数；
    零产物不报 done 的诚实性口径）。"""
    from waterprint import app as core

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def _always_fail(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        raise ValueError(f"boom-{condition_key}")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _always_fail)
        with pytest.raises(RuntimeError, match=r"全部 2 项失败.*首错.*boom-design"):
            run_task(
                _batch_payload(
                    project_path, result_file, out_dir,
                    [
                        _item("dxf", "a.dxf", condition_key="design"),
                        _item("dxf", "b.dxf", condition_key="avg"),
                    ],
                ),
                None,
                None,
            )
    assert list(out_dir.iterdir()) == []  # 零产物（tmp 已由真码清理或未落位）


async def test_export_batch_progress_stage_carries_unit_segment_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D4 接线断言：SSE stage 带 unit 段——export:{kind}:{unit_id}；
    无-unit 项 unit 段省略=export:{kind}（Event 面零 schema 变化）。"""
    from waterprint import app as core

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    messages: list[dict[str, object]] = []

    class _Sink:
        def put(self, message: dict[str, object]) -> None:
            messages.append(message)

    def _noop(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        Path(out).write_bytes(b"ok")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _noop)
        result = run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [
                    _item("dxf", "a.dxf", unit_id="u1", condition_key="design"),
                    _item("dxf", "b.dxf", unit_id="u2", condition_key="avg"),
                    _item("ifc", "c.ifc", unit_id="", condition_key="design"),
                ],
            ),
            None,
            _Sink(),
        )
    assert result["state"] == "done"
    assert [m["stage"] for m in messages] == [  # unit 段逐项+无-unit 省略
        "export:dxf:u1",
        "export:dxf:u2",
        "export:ifc",
    ]


async def test_export_batch_ifc_out_name_suffix_gate_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D3 接线断言：_safe_out_name ifc 特判——ifc 项产物名须 .ifc 后缀
    （dxf 单特判同款式；IPC 直注面防线）。"""
    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    with pytest.raises(_mod.InvalidTaskPayloadError, match="后缀"):
        run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [_item("ifc", "model.dxf", condition_key="design")],
            ),
            None,
            None,
        )
    assert list(out_dir.iterdir()) == []  # 拒于任何落盘之前


async def test_export_batch_cancelled_outcome_carries_files_and_failures_wiring(
    service_ctx, cass_payload, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """SVRB D4 接线断言：取消 outcome 携已产 files+failures（manager 灌入
    result 的载荷源——§2.3 缺陷收口：文件已落盘不可撤，清单诚实可查）。"""
    from waterprint import app as core

    project_path, result_file = await _project_and_result(service_ctx, cass_payload)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cancel_flag = tmp_path / "cancel.flag"

    def _one_fail_one_ok_then_cancel(  # type: ignore[no-untyped-def]  # noqa: PLR0913  # 替身签名镜像被测接口
        kind, plant, template, out, *, unit_id=None, condition_key=None, **extra
    ):
        if condition_key == "bad":
            raise ValueError("svrb item fail")
        Path(out).write_bytes(b"ok")
        cancel_flag.write_text("cancel", encoding="utf-8")  # 末项成功后置令牌

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(core, "export_artifact", _one_fail_one_ok_then_cancel)
        result = run_task(
            _batch_payload(
                project_path, result_file, out_dir,
                [
                    _item("dxf", "a.dxf", condition_key="bad"),
                    _item("dxf", "b.dxf", condition_key="design"),
                    _item("dxf", "c.dxf", condition_key="avg"),
                ],
            ),
            str(cancel_flag),
            None,
        )
    assert result["state"] == "cancelled"
    assert len(result["files"]) == 1  # 已产 b.dxf 携带
    assert len(result["failures"]) == 1  # a.dxf 失败记录随行
    assert (out_dir / "b.dxf").is_file()
    meta_sidecars = [p.name for p in out_dir.glob("*.meta.json")]
    assert json.dumps(result)[:1]  # outcome JSON 可序列化（registry 落盘面）
    assert meta_sidecars == []  # 取消后零新边车（K-02 口径——payload 无登记块）
