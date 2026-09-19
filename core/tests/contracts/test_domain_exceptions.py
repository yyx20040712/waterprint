"""domain_exceptions 薄壳镜像：导入冒烟+成员集在场（B3-c 批 2c）。

组合消费面行为由 tests/graph/（executor R5 隔离）与 tests/solution/
（行级域拒）既有镜像承担——本件满足镜像规则最小义务并钉公共核心
成员集恒等（防静默漂移的单源锚）。
"""

from __future__ import annotations

from waterprint.contracts.domain_exceptions import DOMAIN_EXCEPTIONS_CORE
from waterprint.contracts.flow import InvalidFlowError
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.quality import InvalidQualityError
from waterprint.contracts.sludge import InvalidSludgeError


def test_core_members() -> None:
    """公共核心成员集=contracts 层四族（定案 §1——两消费面组合的公共底座）。"""
    assert set(DOMAIN_EXCEPTIONS_CORE) == {
        InvalidFlowError,
        InvalidQualityError,
        InvalidSludgeError,
        InvalidUnitConfig,
    }
