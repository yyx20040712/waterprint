"""settings 镜像测试：环境配置（路径基点字段、fail-fast 校验）。

输入:  waterprint_server.settings 公开符号
输出:  配置契约断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from pydantic import ValidationError

_mod = importlib.import_module("waterprint_server.settings")
Settings = getattr(_mod, "Settings")
get_settings = getattr(_mod, "get_settings")
safe_child = getattr(_mod, "safe_child")
ensure_directories = getattr(_mod, "ensure_directories")

pytestmark = [
    pytest.mark.skipif(
        None in (Settings, get_settings),
        reason="实现未就绪：waterprint_server.settings（服务层 M2）",
    ),
]


def test_settings_exposes_path_and_limit_fields() -> None:
    """路径基点 + 上限字段齐备（§18 安全面与 §17.2 缓存上限的配置载体）。"""
    names = set(getattr(Settings, "model_fields", {}))
    assert {
        "projects_dir", "exports_dir", "data_dir", "calc_workers",
        "max_upload_mb", "max_excel_rows",
    } <= names
    assert get_settings() is get_settings()  # lru_cache 单例（测试可 cache_clear 覆盖）


def test_settings_defaults_exact_values_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    """R2-C 测试债（E1 冻结全集锚点）：七字段默认值精确断言。

    断言写真值非比较表（魔法数字禁令真源区例外=测试字面锚）；env 逐项
    delenv 隔离（WATERPRINT_HOST 等宿主环境污染面归零——WP1 先例
    Settings(_env_file=None) 同款防御形态）。
    """
    for name in (
        "HOST", "PORT", "LOCK_EXPIRY_S", "DWG_CONVERTER_TIMEOUT_S",
        "TASK_RETENTION_S", "TASK_SWEEP_INTERVAL_S", "TASK_REGISTRY_CAP",
    ):
        monkeypatch.delenv(f"WATERPRINT_{name}", raising=False)
    defaults = Settings(_env_file=None)
    assert defaults.host == "127.0.0.1"  # 裸机默认只听回环（WP1 安全红线）
    assert defaults.port == 8000
    assert defaults.lock_expiry_s == 10000  # ≈2.8 小时（编辑会话锁最长占用心智）
    assert defaults.dwg_converter_timeout_s == 100  # ODA 外挂转换子进程超时
    assert defaults.task_retention_s == 100000  # ≈27.8 小时（终态任务保留窗）
    assert defaults.task_sweep_interval_s == 100  # ≈1.7 分钟（周期清扫轮询）
    assert defaults.task_registry_cap == 1000  # 内存 _tasks 软上限


def test_zero_workers_rejected_wiring() -> None:
    """R2 接线断言：calc_workers < 1 启动即失败（fail fast 不静默默认）。"""
    with pytest.raises(ValidationError):
        Settings(calc_workers=0)
    assert Settings(calc_workers=1).calc_workers == 1  # 合法下限过（1=白名单值）


def test_path_component_whitelist_rejects_traversal() -> None:
    """R1 消费方行为：safe_child 拒 ../、绝对路径、分隔符注入（§18 路径安全）。"""
    base = Path("base")
    assert safe_child(base, "proj_1").parent == base
    for evil in ("..", "../evil", "/abs", "a/b", "", "C:" + chr(92) + "x", "a b"):
        with pytest.raises(ValueError, match="路径分量非法"):
            safe_child(base, evil)


# ══ E2E-1 数据包自愈域（test_settings_data_dir 草稿三用例——[HUMAN-LOCK]
#     2026-09-26 用户「全部追认」授权落地；R4 C-3 八用例（test_r4_draft.py
#     C-3 节单源）同笔并落——E2E-1 呈批件 2026-09-25 追加节工序）══

import shutil  # noqa: E402 （域内追加——C-3 四包全拷用）

import yaml  # noqa: E402 （域内追加——C-3 路径锁定断言用）

default_data_dir = getattr(_mod, "default_data_dir", None)
validate_data_packages = getattr(_mod, "validate_data_packages", None)

REPO_ROOT = Path(__file__).resolve().parents[2]  # conftest 同名常量镜像自持
_PACKAGES = ("coefficients", "constraint_kb", "templates", "unit_prices")


def test_data_dir_default_resolves_repo_root_cwd_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E-1 P0-A：data_dir 缺省=包定位上溯仓库根（CWD 相对旧缺陷回归锚）。

    旧缺陷：Path("data") 按 CWD 解析，README「cd server」口径落到
    server/data（不存在）⇒ 约束库 500/计算必败（e2e-audit 2026-09-24）。
    """
    monkeypatch.delenv("WATERPRINT_DATA_DIR", raising=False)
    monkeypatch.chdir(REPO_ROOT / "server")  # README 口径①的 CWD——旧缺陷复现位
    settings = Settings(_env_file=None)  # type: ignore[misc]
    assert settings.data_dir == Path(__file__).resolve().parents[2] / "data"
    assert (settings.data_dir / "coefficients" / "manifest.yaml").is_file()


def test_validate_data_packages_failfast_message(tmp_path: Path) -> None:
    """E2E-1 P0-A：缺包启动校验 raise RuntimeError 且文案可执行（含 env 指引）。"""
    empty = tmp_path / "data"
    empty.mkdir()
    settings = Settings(  # type: ignore[misc]
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=empty,
        calc_workers=1,
        log_file=str(tmp_path / "t.log"),
    )
    with pytest.raises(RuntimeError, match="WATERPRINT_DATA_DIR"):
        validate_data_packages(settings)  # type: ignore[misc]


def test_data_dir_env_overrides_default_factory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """E2E-1 P0-A：env WATERPRINT_DATA_DIR 优先于包定位缺省（部署覆盖面）。"""
    monkeypatch.setenv("WATERPRINT_DATA_DIR", str(tmp_path))
    settings = Settings(_env_file=None)  # type: ignore[misc]
    assert settings.data_dir == tmp_path


def _c3_make_settings(data_dir: Path, tmp_path: Path):
    """四包齐备 data_dir 的 Settings（C-3 判据载体——tmp 三基点隔离）。"""
    return Settings(  # type: ignore[misc]
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=data_dir,
        calc_workers=1,
        log_file=str(tmp_path / "t.log"),
    )


def _c3_copy_full_packages(target: Path) -> Path:
    """四包全拷（与仓库真包逐字节一致）。"""
    for name in _PACKAGES:
        shutil.copytree(REPO_ROOT / "data" / name, target / name)
    return target


def test_c3_real_packages_pass(tmp_path: Path) -> None:
    """C-3 判据对仓库真包 PASS（防过度拒绝回归锚——四包 manifest 均非空映射）。"""
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_missing_file_keeps_env_hint(tmp_path: Path) -> None:
    """C-3 兼容锚：缺文件态文案保留 WATERPRINT_DATA_DIR 指引（E2E-1 既有断言面）。"""
    (tmp_path / "data").mkdir()
    with pytest.raises(RuntimeError, match="WATERPRINT_DATA_DIR"):
        validate_data_packages(_c3_make_settings(tmp_path / "data", tmp_path))  # type: ignore[misc]


def test_c3_empty_manifest_rejected(tmp_path: Path) -> None:
    """C-3：manifest 空文件（safe_load→None）=启动拒（旧判据 is_file 可过的盲区）。"""
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    (data_dir / "coefficients" / "manifest.yaml").write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="空损|不可解析"):
        validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_empty_mapping_rejected(tmp_path: Path) -> None:
    """C-3：合法 yaml 但空映射（{}）=启动拒（至少一条非空映射判据锚）。"""
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    (data_dir / "templates" / "manifest.yaml").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="空损|不可解析"):
        validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_scalar_manifest_rejected(tmp_path: Path) -> None:
    """C-3 回炉（d1 W1）：合法 yaml 标量/列表（非 dict）=启动拒——锁 isinstance 分支。

    路径锁定前置： '::::[broken' 实为 plain scalar（str）——不触发 YAMLError，
    原 broken 用例实际测的即本分支（d1 三层分析实证）；本用例显式锁路径。
    """
    for index, raw in enumerate(("::::[broken", "42", "[1,2]")):
        loaded = yaml.safe_load(raw)  # 路径锁定：三输入均正常返回非 dict
        assert not isinstance(loaded, dict)
        data_dir = _c3_copy_full_packages(tmp_path / f"data-scalar-{index}")
        (data_dir / "coefficients" / "manifest.yaml").write_text(raw, encoding="utf-8")
        with pytest.raises(RuntimeError, match="空损|不可解析"):
            validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_broken_yaml_rejected(tmp_path: Path) -> None:
    """C-3 回炉（d1 W1）：确定语法错（未闭合 flow sequence）=启动拒——锁 YAMLError 分支。

    路径锁定前置：'a: [1,' 经 yaml.safe_load 确抛 ParserError（YAMLError 子类）
    ——与标量分支（isinstance 判据）构成两条独立防线的确定性覆盖。
    """
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("a: [1,")  # 路径锁定：该输入确定走解析异常分支
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    (data_dir / "unit_prices" / "manifest.yaml").write_text("a: [1,", encoding="utf-8")
    with pytest.raises(RuntimeError, match="空损|不可解析"):
        validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_non_utf8_rejected(tmp_path: Path) -> None:
    """C-3 回炉（d1 W1）：非 UTF-8 字节=启动拒——锁 UnicodeDecodeError 分支。"""
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    (data_dir / "templates" / "manifest.yaml").write_bytes(b"\xff\xfe\x00broken")
    with pytest.raises(RuntimeError, match="空损|不可解析"):
        validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]


def test_c3_two_states_both_listed(tmp_path: Path) -> None:
    """C-3：缺文件与空损并存时两态清单同报（文案区分的合并面）。"""
    data_dir = _c3_copy_full_packages(tmp_path / "data")
    (data_dir / "constraint_kb" / "manifest.yaml").write_text("", encoding="utf-8")
    shutil.rmtree(data_dir / "templates")
    with pytest.raises(RuntimeError) as exc_info:
        validate_data_packages(_c3_make_settings(data_dir, tmp_path))  # type: ignore[misc]
    message = str(exc_info.value)
    assert "constraint_kb" in message and "templates" in message
