"""ODA File Converter 本地手动冒烟工具（批6j——挂账池「ODA E2E」兑现面）。

目的：验证本仓导出的 DXF 可被 ODA File Converter（Open Design Alliance
免费转换器）读取并转换——DXF→DWG 正向+DWG→DXF 反向往返，往返件经
ezdxf 读回断言可读+实体非空。**不入 pytest 收集**（tools/ 不在
core/server testpaths；CI 无 ODA 环境——skip 拦截矛盾，故为手动工具
+验证清单形态，清单=同目录 oda_smoke.md）。

用法（仓根执行；server venv 同时含 core/server 依赖）::

    uv run --project server python tools/oda_smoke.py             # 默认：夹具两份 DXF（相对+绝对标高）全流程
    uv run --project server python tools/oda_smoke.py --dxf a.dxf # 指定既有件（可重复）
    uv run --project server python tools/oda_smoke.py --allow-missing  # 转换器缺席=软跳过（exit 0）
    uv run --project server python tools/oda_smoke.py --mock      # 无 ODA 机器验证编排逻辑（mock 转换器）

转换器定位序：--converter > 环境变量 ODA_FILE_CONVERTER > 常见安装位扫描
> PATH。缺席默认=诚实失败（exit 1——手动验证工具不假绿）。

转换真源=server waterprint_server.jobs.dwg.dwg_convert（WP0 ODA-A CLI
契约单源；批6j output_type 参数支撑往返向）——本脚本零 CLI 契约副本。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TIMEOUT_S = 100  # server settings.dwg_converter_timeout_s 同值（幂积保白名单字面量集口径注记见 settings.py）
_COMMON_INSTALL_BASES = (
    r"C:\Program Files\ODA",
    r"C:\Program Files (x86)\ODA",
)

_MOCK_PY = """import shutil, sys
from pathlib import Path
in_dir, out_dir, _version, out_type = sys.argv[1:5]
name = sys.argv[7] if len(sys.argv) > 7 else None
src = Path(in_dir) / name
if src.is_file():
    shutil.copyfile(src, Path(out_dir) / src.with_suffix("." + out_type.lower()).name)
sys.exit(0)
"""

_MOCK_BAT = '@echo off\r\npython "%~dp0oda_mock_converter.py" %*\r\n'


def _find_converter(explicit: str | None) -> Path | None:
    """定位 ODA File Converter：显式参 > 环境变量 > 常见安装位 > PATH。"""
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    env = os.environ.get("ODA_FILE_CONVERTER", "").strip()
    if env:
        p = Path(env)
        return p if p.is_file() else None
    for base_text in _COMMON_INSTALL_BASES:
        base = Path(base_text)
        if base.is_dir():
            for hit in sorted(base.glob("*/ODAFileConverter.exe")):
                if hit.is_file():
                    return hit
    which = shutil.which("ODAFileConverter")
    return Path(which) if which else None


def _write_mock_converter(directory: Path) -> Path:
    """mock 转换器（--mock）：ODA CLI 契约复刻的测试替身——argv 形态
    <in_dir> <out_dir> <version> <DWG|DXF> <recurse> <audit> [filter]，
    行为=按输出类型复制输入件（bat 包装保 CreateProcess 可执行性）。
    用途=无 ODA 机器验证**编排逻辑**；产物真实性由真机 ODA 冒烟承担
    （清单文档明示——mock 通过≠ODA 兼容性通过）。"""
    py = directory / "oda_mock_converter.py"
    py.write_text(_MOCK_PY, encoding="utf-8")
    bat = directory / "oda_mock_converter.bat"
    # 纯 ASCII 面（bat 禁嵌本机非 ASCII venv 路径——cmd 代码页脆性）：
    # python 由继承环境 PATH 解析（uv run/venv 面恒在）。
    bat.write_text(_MOCK_BAT, encoding="ascii")
    return bat


def _fixture_dxf(directory: Path) -> list[Path]:
    """夹具两份纵断 DXF（core 轻夹具 inlet→cass——test_export_profile
    同源构造）：默认相对基准+绝对标高模式（顺带实跑批6j 通道）。"""
    from waterprint.app import run_full_calc
    from waterprint.app_enumeration import export_artifact
    from waterprint.contracts.condition import build_condition_set as _bcs
    from waterprint.contracts.project_schema import (
        DesignState,
        Metadata,
        ProjectFile,
    )
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    data = _REPO / "data" / "coefficients"
    lib = load_coefficients(data)
    env = RunEnv(
        engine_version="p2",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={}, coefficients=lib,
        price_book={}, trace_sink=None, engine_params={},
    )
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {"kind": "municipal_input",
                          "q_avg_daily": 34760.7 / 86400, "kz": 1.4,
                          "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                          "TN": 43.0},
                "municipal_cass": {},
            },
            edges=[{"src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"}}],
        ),
        metadata=Metadata(format_version="1.0", content_hash="",
                          engine_version="p2", data_version="p2"),
    )
    plant = run_full_calc(project, _bcs([]), env).plant
    made: list[Path] = []
    for tag, opts in (
        ("relative", {}),
        ("absolute", {"water_level": "1053.2", "ground_elev": "1051.0"}),
    ):
        out = directory / f"smoke_profile_{tag}.dxf"
        export_artifact(
            "dxf", plant, Path("unused"), out,
            condition_key="design", sheet="profile", **opts,
        )
        made.append(out)
    return made


def _smoke_one(converter: Path, dxf: Path) -> tuple[bool, str]:
    """单件冒烟：DXF→DWG→（DWG→DXF 往返）→ezdxf 读回断言。"""
    import ezdxf

    from waterprint_server.jobs.dwg import dwg_convert

    dwg = dwg_convert(str(converter), dxf, _TIMEOUT_S)
    if dwg is None:
        return False, "DXF→DWG 转换失败（dwg_convert_skipped 日志见因）"
    back = dwg_convert(str(converter), dwg, _TIMEOUT_S, output_type="DXF")
    if back is None:
        return False, "DWG→DXF 往返转换失败"
    doc = ezdxf.readfile(back)
    count = len(doc.modelspace())
    if count <= 0:
        return False, f"往返 DXF 读回实体数为 {count}（空产物）"
    return True, (
        f"dwg={dwg.stat().st_size}B roundtrip={back.stat().st_size}B"
        f" entities={count}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ODA File Converter 本地手动冒烟（批6j）")
    parser.add_argument("--converter", help="ODAFileConverter.exe 显式路径")
    parser.add_argument("--dxf", action="append",
                        help="指定既有 DXF 件（可重复；缺省=core 夹具两份）")
    parser.add_argument("--allow-missing", action="store_true",
                        help="转换器缺席=软跳过（exit 0）——默认诚实失败 exit 1")
    parser.add_argument("--mock", action="store_true",
                        help="用 mock 转换器验证编排逻辑（无 ODA 机器）")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="oda-smoke-") as tmp:
        work = Path(tmp)
        if args.mock:
            converter = _write_mock_converter(work)
            print(f"[mock] 转换器测试替身：{converter}")
        else:
            converter = _find_converter(args.converter)
            if converter is None:
                print("SKIP/FAIL：未定位 ODAFileConverter（--converter 显式传"
                      "或安装 ODA File Converter——验证清单见 tools/oda_smoke.md）")
                return 0 if args.allow_missing else 1
            print(f"[converter] {converter}")
        try:
            targets = ([Path(p) for p in args.dxf] if args.dxf
                       else _fixture_dxf(work))
        except Exception as exc:  # noqa: BLE001  # 手动工具面：夹具失败如实呈现
            print(f"FAIL：夹具导出失败：{exc!r}")
            return 1
        failures = 0
        for dxf in targets:
            if not dxf.is_file():
                print(f"FAIL：{dxf} 不存在")
                failures += 1
                continue
            ok, detail = _smoke_one(converter, dxf)
            print(f"{'PASS' if ok else 'FAIL'}  {dxf.name}  {detail}")
            failures += 0 if ok else 1
        total = len(targets)
    print(f"[summary] {total - failures}/{total} passed"
          + ("（mock 模式——产物真实性须真机 ODA 复验）" if args.mock else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
