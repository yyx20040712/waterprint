"""roles.py 镜像测试：三角色装配决策矩阵（联机第七批 ADR-028）。"""

from __future__ import annotations

import pytest

from waterprint_desktop.roles import (
    ENGINE_LAN_BIND,
    ENGINE_LOOPBACK_BIND,
    SHELL_PORT,
    plan_for,
)


def test_matrix_all_four_roles() -> None:
    cases = {
        "unconfigured": (None, True, False, False),
        "standalone": (ENGINE_LOOPBACK_BIND, False, True, False),
        "server": (ENGINE_LAN_BIND, False, True, True),
        "client": (None, True, False, False),
    }
    for role, expected in cases.items():
        plan = plan_for(role)
        assert plan.role == role
        assert (
            plan.engine_bind_host,
            plan.serve_static_shell,
            plan.mount_ui_on_engine,
            plan.require_token,
        ) == expected


def test_shell_port_is_cors_contract_value() -> None:
    # 8620=server CORS 缺省白名单约定端口（b5/b6 契约对齐——改端口须同批
    # 改 server settings.allowed_origins 缺省串）
    assert SHELL_PORT == 8620


@pytest.mark.parametrize("bad", ["", "lan", "host", "standalone ", "CLIENT"])
def test_unknown_role_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="未知桌面壳角色"):
        plan_for(bad)
