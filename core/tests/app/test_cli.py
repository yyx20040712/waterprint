"""cli 镜像测试：命令行入口（退出码语义/new-unit 幂等保护/编码防线）。

输入:  waterprint.cli.main 公开符号
输出:  CLI 契约断言
注记:  M4a ③ 补 export audit 端到端（golden 项目实跑结果→HTML 落盘）
       与失败面（读入/越界路径/未注册 kind）两用例。
"""

from __future__ import annotations

import html
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

_mod = importlib.import_module("waterprint.cli")
main = getattr(_mod, "main", None)

pytestmark = pytest.mark.skipif(
    main is None,
    reason="实现未就绪：waterprint.cli（M1）",
)


def test_exit_code_semantics_wiring(tmp_path: Path) -> None:
    """R1 接线断言（NET2 填真实现）：0 成功 / 2 用法错误 / 3 校验失败。

    无参调用→2（argparse required 子命令缺失）；坏项目文件→3（network
    子命令读入不存在文件=读入校验失败口径——v2 首发子命令语义同 R1）。
    """
    assert main([]) == 2
    assert main(["network", str(tmp_path / "nonexistent.xlsx")]) == 3


def test_new_unit_refuses_existing_target_wiring(tmp_path: Path) -> None:
    """R2 接线断言（NET2 填真实现）：目标单元包已存在 = 拒绝（防误覆盖）。

    --root 指向 tmp 复制的模板根：首次生成成功（0）；同参再生成同一
    'test_demo' 目标 → 第二次拒绝（非 0——幂等保护）。
    """
    import shutil

    template = Path(__file__).resolve().parents[2] / "waterprint" / "units_lib" / "_template"
    root = tmp_path / "units_lib"
    shutil.copytree(template, root / "_template", ignore=shutil.ignore_patterns("__pycache__"))
    first = main(["new-unit", "municipal", "test_demo", "--root", str(root)])
    assert first == 0
    assert (root / "municipal" / "test_demo").is_dir()
    second = main(["new-unit", "municipal", "test_demo", "--root", str(root)])
    assert second != 0


def _golden_result(golden_data_dir: Path, tmp_path: Path) -> tuple[Path, Path, Any]:
    """M4a ③ 夹具：golden 项目实跑一次 → result.json 落盘（serialize 产物）。

    env 口径与 tests/golden/test_municipal_e2e.py 同源（expected.generated
    版本串+DEFAULT_ASSUMPTIONS+真库 coefficients）；返回（项目路径，结果
    路径，plant）——CLI 消费面=文件对，断言面=plant 真值。
    """
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.result_schema import serialize
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case = golden_data_dir / "municipal_34760"
    project_path = case / "input_project.json"
    expected = json.loads((case / "expected_summary.json").read_text(encoding="utf-8"))
    data = Path(__file__).resolve().parents[3] / "data" / "coefficients"
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(data),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    plant = run_full_calc(
        load_project(project_path),
        build_condition_set(expected["checked_units"]),
        env,
    ).plant
    result_path = tmp_path / "result.json"
    result_path.write_bytes(serialize(plant))
    return project_path, result_path, plant


def test_export_audit_end_to_end_wiring(golden_data_dir: Path, tmp_path: Path) -> None:
    """M4a ③ e2e：wp export audit → HTML 落盘（转义/@media print/三元组）。

    golden 项目实跑结果 → --out 嵌套目录（mkdir 面）→ 断言：退出码 0 /
    迹首条公式 ID 与条文号以转义形态在场 / repro 三元组自证 / @media
    print 打印版在（⑤ 面）/ 零脚本（R3 自包含）；默认 --out=结果同目录
    <stem>.audit.html 再证一次（确定性命名）。
    """
    project_path, result_path, plant = _golden_result(golden_data_dir, tmp_path)
    out = tmp_path / "nested" / "dir" / "audit.html"
    assert main(["export", "audit", str(project_path), str(result_path), "--out", str(out)]) == 0
    assert out.is_file()
    document = out.read_text(encoding="utf-8")
    assert "公式溯源审计报告" in document
    assert "@media print" in document
    assert "<script" not in document
    node = plant.trace[0]
    assert html.escape(node.formula_id) in document  # 转义渲染端到端
    assert html.escape(node.norm_ref) in document
    assert plant.repro.design_hash in document  # 三元组自证（R4 时间面）
    assert main(["export", "audit", str(project_path), str(result_path)]) == 0
    assert (tmp_path / "result.audit.html").is_file()  # 默认命名=结果同目录


def test_export_audit_failure_paths_wiring(
    golden_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """M4a ③ 失败面：坏项目/坏结果/损坏结果→3；--out 含 '..'→3（越界消息）；
    未注册 kind（calcbook）→2（argparse 用法错误——愿景行其余成员保持注释）。
    """
    project = golden_data_dir / "municipal_34760" / "input_project.json"
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_bytes(b"not-json")
    assert main(["export", "audit", str(tmp_path / "nope.json"), str(project)]) == 3
    assert main(["export", "audit", str(project), str(tmp_path / "nope.json")]) == 3
    assert (
        main(["export", "audit", str(project), str(corrupt), "--out", str(tmp_path / "a.html")])
        == 3
    )
    escape = tmp_path / ".." / "escape.html"
    assert (
        main(["export", "audit", str(project), str(tmp_path / "nope.json"), "--out", str(escape)])
        == 3
    )
    assert "越界分量" in capsys.readouterr().err  # 路径检查先于结果读入（裁定面）
    assert main(["export", "calcbook", str(project), str(project)]) == 2
