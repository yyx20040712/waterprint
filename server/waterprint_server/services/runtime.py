"""运行时信息服务：版本握手聚合（meta）+运行角色/配对面（runtime）。

输入:  Settings（settings.py——host/api_token/data_dir）+请求者对端地址
       （routers/meta.py 传入——socket 面，headers 不参判）
输出:  MetaInfo/RuntimeInfo（冻结 pydantic 模型）+runtime_role/lan_addresses
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机架构第五批 2026-11-19——用户裁决 Minecraft 式开关模型；
# 镜像测试 server/tests/routers/test_meta.py）
#
# 【公开接口】
#   MetaInfo（BaseModel）：app_version/data_version/api_version 三槽
#   RuntimeInfo（BaseModel）：role/bind_host/lan_addresses/
#      token_configured/token_reveal 五槽
#   build_meta(settings) -> MetaInfo          GET /api/meta 载荷组装
#   build_runtime(settings, requester_host) -> RuntimeInfo
#                                             GET /api/runtime 载荷组装
#   runtime_role(bind_host) -> RuntimeRole     绑定地址即角色判定
#   lan_addresses() -> list[str]               本机局域网 IPv4 枚举
#   API_SEMANTIC_VERSION（Final）              API 语义版本真源
#
# 【行为规格】
#   R1 data_version 单源复用：经 core.app.load_run_env 读 UF-10/b24
#      三包聚合串（assumptions+coefficients+unit_prices——空 design
#      项目仅取版本面，不触计算），服务层不建第二聚合源；进程内
#      lru_cache 幂等（units 目录静态面先例——数据包为版本化资产，
#      运行期不换包）。
#   R2 role 派生零新配置：绑定地址即角色（settings.is_loopback_host
#      ——回环=standalone、对外〔0.0.0.0/具体网卡〕=server）。切换
#      本体（127.0.0.1↔0.0.0.0+重启生效）属 desktop 壳（b7 批）。
#   R3 token 安全红线：token_reveal 仅请求者 socket 对端地址回环时
#      放行明文（配对卡展示面——本机用户读本机 token 的 Minecraft 式
#      配对模型）；非回环恒 None；X-Forwarded-For 类 headers 不参判
#      （反代伪装回环骗取 token 面封死）；token 值禁入任何日志——
#      本模块零日志调用，测试钉死配置 sink 无 token 落盘。
#   R4 lan_addresses：gethostname 解析的非回环 IPv4 去重排序（尽力
#      而为非契约——解析空集=空列表，配对卡诚实降级"未发现局域网
#      地址"；standalone 角色恒空列表=无监听地址语义）。
#
# 【数值纪律】lru_cache maxsize=2*2（幂积保白名单字面量集）。
#
# 【测试要求】见 server/tests/routers/test_meta.py（版本三槽/角色两态/
#   回环 reveal 门/非回环+伪装头拒/豁免面/日志零 token）。
#
# 【参照】任务书联机架构第五批；frontend-redesign/connection.html；
#   docs/architecture.md §4.1 安全红线
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import ipaddress
import socket
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel
from waterprint.app import load_run_env
from waterprint.contracts.project_schema import (
    CURRENT_FORMAT_VERSION,
    Metadata,
    ProjectFile,
)

from waterprint_server.settings import ENGINE_VERSION, Settings, is_loopback_host

RuntimeRole = Literal["standalone", "server"]

# API 语义版本（客户端版本握手判据）：与 app_version〔发行串〕解耦——
# 应用补丁/数据包抬版不动本值，仅 API 面不兼容变更时人工抬版（客户端
# 模式〔下一批〕握手比对槽）。
API_SEMANTIC_VERSION: Final[str] = "1.0"


class MetaInfo(BaseModel):
    """GET /api/meta 载荷：应用版本+数据包版本聚合+API 语义版本。"""

    app_version: str
    data_version: str
    api_version: str


class RuntimeInfo(BaseModel):
    """GET /api/runtime 载荷：运行角色/绑定面/配对面（token 仅回环可见）。"""

    role: RuntimeRole
    bind_host: str
    lan_addresses: list[str]
    token_configured: bool
    token_reveal: str | None


def _blank_project() -> ProjectFile:
    """聚合用空项目（design 全默认容器——assumption_overrides 空，仅读版本面）。"""
    return ProjectFile(
        format_version=CURRENT_FORMAT_VERSION,
        metadata=Metadata(
            format_version=CURRENT_FORMAT_VERSION,
            content_hash="",
            engine_version="",
            data_version="",
        ),
    )


@lru_cache(maxsize=2 * 2)  # 4（幂积保白名单字面量集）
def _aggregated_data_version(data_dir: Path) -> str:
    """UF-10 三包聚合单源消费（R1）：load_run_env 读 data_version。

    空项目装载只触发 coefficients/assumptions 版本面与 unit_prices
    manifest 槽读，不触计算；混合数据根相异=fail-fast 与计算路径同面。
    """
    return load_run_env(data_dir, _blank_project()).data_version


def build_meta(settings: Settings) -> MetaInfo:
    """版本握手信息组装（app=ENGINE_VERSION；data=三包聚合；api=语义版本）。"""
    return MetaInfo(
        app_version=ENGINE_VERSION,
        data_version=_aggregated_data_version(settings.data_dir),
        api_version=API_SEMANTIC_VERSION,
    )


def runtime_role(bind_host: str) -> RuntimeRole:
    """绑定地址即角色（R2：回环=standalone、对外=server——零新配置面）。"""
    return "standalone" if is_loopback_host(bind_host) else "server"


def lan_addresses() -> list[str]:
    """本机局域网 IPv4 枚举（R4：hostname 解析非回环 IPv4 去重升序）。"""
    found: set[str] = set()
    try:
        # getaddrinfo 五元组解包取 sockaddr（元组拆包替代下标——AF_INET
        # 恒四元组 (host, port)；host 联合型窄化排除 AF_UNIX 形态）
        for _, _, _, _, sockaddr in socket.getaddrinfo(
            socket.gethostname(), None, socket.AF_INET
        ):
            host = sockaddr[0]
            if isinstance(host, str):
                found.add(host)
    except (socket.gaierror, OSError):
        # 主机名不可解析（exotic 容器/最小环境）=空集诚实降级，不伪造地址
        return []
    return sorted(
        address
        for address in found
        if not ipaddress.ip_address(address).is_loopback
    )


def build_runtime(settings: Settings, requester_host: str) -> RuntimeInfo:
    """运行角色与配对面组装（R2/R3——role 派生+回环 reveal 门）。

    requester_host=对端 socket 地址（routers 层自 request.client 取，
    空串=取不到对端按非回环处理=fail-closed 不 reveal）。
    """
    role = runtime_role(settings.host)
    return RuntimeInfo(
        role=role,
        bind_host=settings.host,
        lan_addresses=lan_addresses() if role == "server" else [],
        token_configured=settings.api_token != "",
        token_reveal=(
            settings.api_token if is_loopback_host(requester_host) else None
        ),
    )
