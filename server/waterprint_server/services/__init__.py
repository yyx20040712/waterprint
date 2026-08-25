"""服务层包根：用例编排（每用例一文件，只调 core L4，禁 import fastapi）。

输入:  routers 传入的服务请求（纯数据）+ ServiceContext（装配束）
输出:  领域结果（core 产出 + 任务状态）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【四个服务文件】projects（项目 IO 用例）/ calculation（计算与方案
#   应用）/ enumeration（枚举用例）/ exports（导出用例）。
# 【铁律】服务文件禁止 import fastapi/starlette（分层 §13.4）；
#   core 调用只经 waterprint.app（L4 正门）；事务性编排
#   （方案应用原子写）在本层实现。
# 【ServiceContext】（SERVER 2026-08-26 实装注记）服务函数为模块级
#   公开面（镜像测试 getattr 契约），首参统一 ServiceContext——
#   create_app 每次构建新束挂 app.state（工厂可重复构建无全局状态，
#   main.py R1）；tasks 数据区=exports_dir/tasks（结果/行文件/取消
#   标记，§16 A6 任务产物目录语义）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from waterprint_server.jobs.manager import Manager
from waterprint_server.settings import Settings


@dataclass(frozen=True)
class ServiceContext:
    """服务装配束（每 app 一份；禁模块级可变全局——main R1 工厂可重复）。"""

    settings: Settings
    manager: Manager

    @property
    def projects_dir(self) -> Path:
        """项目文件基点（R1 路径安全：一切项目路径经 safe_child 拼接）。"""
        return self.settings.projects_dir

    @property
    def exports_dir(self) -> Path:
        """导出产物基点。"""
        return self.settings.exports_dir

    @property
    def artifacts_dir(self) -> Path:
        """任务产物区（结果 serialize/枚举行 feather/取消标记，§16 A6）。"""
        return self.settings.exports_dir / "tasks"

    @property
    def cancel_dir(self) -> Path:
        """取消标记区（协作令牌文件面）。"""
        return self.artifacts_dir / "cancel"

    @property
    def templates_dir(self) -> Path:
        """Excel 模板包基点（data/templates，UF-16 模板录入批）。"""
        return self.settings.data_dir / "templates"
