"""引擎装配件：角色化 Settings + server 应用工厂消费 + UI 同源挂载。

输入:  AssemblyPlan（roles.py）+api_token+端口/数据基点+webapp dist 目录
输出:  build_engine_settings（Settings 构造）/build_engine_app
       （create_app+UI 挂载）+resolve_engine_port（端口决策）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_engine.py）
#
# 【公开接口】
#   resolve_engine_port() -> int：WATERPRINT_PORT env 覆盖，缺省
#      DEFAULT_ENGINE_PORT（8621）——沿用 server settings 端口通道
#   resolve_data_dir() -> Path：数据包根决策（WATERPRINT_DATA_DIR env
#      覆盖，缺省=仓库根 data/ 包定位上溯——安装态经 env 指向布局）
#   build_engine_settings(plan, api_token, port, data_root, data_dir=None)
#      -> Settings：角色派生绑定（host=plan.engine_bind_host）+token
#      （server 角色=传入 token〔≥16 由 Settings 构造校验二次把关〕；
#      standalone=空即鉴关）+projects/exports 基点=桌面数据根派生
#      （CWD 相对缺省不适用桌面形态）；其余面（CORS/池大小）沿 env 通道
#   build_engine_app(settings, webapp_dist, executor=None) -> FastAPI：
#      waterprint_server.main.create_app 消费+UI 静态面挂载
#
# 【行为规格】
#   R1 token 通道单源：服务端模式 token 经 WATERPRINT_API_TOKEN 的
#      Settings 字段通道注入（kwarg=该通道的程序面，不造第二通道）；
#      0.0.0.0+空 token 由 server Settings 构造即拒（R-6 机器防线——
#      本件不重复实现红线只复用）。
#   R2 UI 同源挂载（ADR-028 选型 A）：dist 在场（index.html 存在）时
#      StaticFiles(html=True) 挂 "/"——/api 路由先注册先生效，UI 与
#      API 同源零 CORS 依赖零反代件；dist 缺席=跳过挂载（API-only
#      诚实降级，打包缺 UI 的调试形态）。
#   R3 executor 注入口：create_app(settings, executor=None) 透传——
#      测试注入 ThreadPoolExecutor 跳过进程池 spawn（server 工厂既有
#      注入口，非新面）。
#
# 【测试要求】两角色 Settings 面（绑定/token 门槛）/UI 挂载与缺席/
#   引擎端口 env 覆盖。
#
# 【参照】ADR-028；server main.create_app；server settings R-6/R-7
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from waterprint_server.main import create_app
from waterprint_server.settings import Settings

from waterprint_desktop.roles import (
    DEFAULT_ENGINE_PORT,
    AssemblyPlan,
)


def resolve_engine_port() -> int:
    """引擎端口决策：WATERPRINT_PORT env 覆盖，缺省 8621（桌面壳约定）。

    server 裸机面同键 env 通道原样沿用——用户显式配置优先于壳缺省。"""
    override = os.environ.get("WATERPRINT_PORT")
    if override:
        return int(override)
    return DEFAULT_ENGINE_PORT


def resolve_data_dir() -> Path:
    """数据包根决策：WATERPRINT_DATA_DIR env 覆盖，缺省=仓库根 data/
    （桌面壳包定位上溯——agent data_asset_root 同款装配语义；安装态下
    server settings 的包定位缺省会指向 venv 内=不可用，桌面壳须显式
    供数据根——打包形态经 env 指向安装器布局，见 desktop/packaging）。"""
    override = os.environ.get("WATERPRINT_DATA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data"


def build_engine_settings(
    plan: AssemblyPlan,
    api_token: str,
    port: int,
    data_root: Path,
    data_dir: Path | None = None,
) -> Settings:
    """角色化引擎 Settings（绑定/token=角色派生；数据基点=桌面数据根）。

    server 角色 host=0.0.0.0：空 token 在 Settings 构造即 ValidationError
    （server R-6 红线复用非重实现）；standalone 角色 host=127.0.0.1+空
    token（回环面鉴权关=既有缺省语义）。data_dir 缺省=resolve_data_dir()
    （五数据包根——与 server 启动校验/装载面同源）。"""
    if plan.engine_bind_host is None:
        raise ValueError(f"角色 {plan.role!r} 不起引擎（无 Settings 可建）")
    token = api_token if plan.require_token else ""
    return Settings(
        host=plan.engine_bind_host,
        port=port,
        api_token=token,
        projects_dir=data_root / "projects",
        exports_dir=data_root / "exports",
        data_dir=data_dir if data_dir is not None else resolve_data_dir(),
    )


def build_engine_app(
    settings: Settings, webapp_dist: Path | None, executor: object | None = None
) -> FastAPI:
    """引擎应用装配：server 应用工厂+UI 静态面同源挂载（R2 选型 A）。

    dist 缺席/无 index.html=跳过挂载（API-only 降级——窗口面在 main 层
    对缺失作提示，本件只做装配事实）。"""
    app = create_app(settings, executor=executor)
    if webapp_dist is not None and (webapp_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=webapp_dist, html=True), name="desktop-ui")
    return app
