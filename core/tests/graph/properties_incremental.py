"""incremental 性质测试：随机编辑序列下 增量 == 全量重算（字节级）。

输入:  增量执行器与全量执行器（M1 实现后激活）
输出:  等价性断言（违反 = CI 失败——§17.2 语义铁律）

说明：本性质需要可运行的最小图（M1 三单元切片）。实现后由
golden_data/m3_incremental_seed.json 提供种子图与编辑序列
（数据由人类维护）；数据缺失时跳过。实现者不得在本文件内
放宽等价性（字节级比较是硬约束）。
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.graph.incremental")
recompute_scope = getattr(_mod, "recompute_scope", None)

hypothesis = pytest.importorskip("hypothesis")

_SEED = Path(__file__).resolve().parent.parent / "golden" / "golden_data" / "m3_incremental_seed.json"

pytestmark = [
    pytest.mark.skipif(
        recompute_scope is None or not _SEED.is_file(),
        reason="实现未就绪或种子数据未整理（M1/M3：waterprint.graph.incremental）",
    ),
]


def test_incremental_equals_full_recompute_on_seed_sequence() -> None:
    """种子编辑序列：每步增量结果与全量重算字节级一致。"""
    seed = json.loads(_SEED.read_text(encoding="utf-8"))
    assert {"base_design", "edits"} <= set(seed)
    # 实现后：逐步应用 edits，比较 recompute_scope 增量结果与
    # execute_graph 全量结果的确定性序列化字节（raise AssertionError 若不等）。
    raise AssertionError(
        "种子数据已就绪但等价性断言未接线：本断言必须由实现者与领域专家"
        "共同完成接线（红-绿），不得删除或放宽"
    )
