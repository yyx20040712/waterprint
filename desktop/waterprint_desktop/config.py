"""角色配置持久化：desktop.json 读写 + 配对 token 生成与保管。

输入:  配置文件路径（构造注入；缺省解析=default_config_path）+角色/token
输出:  DesktopConfig（冻结数据类）+ConfigStore（load/save/ensure_server_token）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_config.py）
#
# 【公开接口】
#   DesktopRole（Literal 别名）：四角色串——"unconfigured"（首启未配置）/
#      "standalone"（单机：本地引擎回环绑定）/"server"（服务端：0.0.0.0
#      +token 强制）/"client"（客户端：不起引擎，本地静态壳供 UI）
#   DesktopConfig（frozen dataclass）：role+api_token 两槽
#   default_config_path() -> Path：缺省配置路径（env
#      WATERPRINT_DESKTOP_CONFIG 覆盖；缺省 ~/.config/waterprint/
#      desktop.json——Windows 用户可经 env 指向 %APPDATA%，打包面挂账
#      见 desktop/packaging/README.md）
#   ConfigStore：load()（缺文件=unconfigured 缺省；坏 JSON/未知角色/
#      token 形态非法=ValueError fail fast 不静默）/save()（原子写
#      tmp+os.replace，UTF-8 显式 encoding，键排序缩进确定形态——同输入
#      双写字节级一致）/ensure_server_token()（无则生成持久化后返回；
#      既有则原样返回——服务端重启配对 token 稳定）
#   generate_api_token() -> str：secrets.token_hex(TOKEN_BYTES)——32 位
#      hex ≥ server settings API_TOKEN_MIN_LENGTH=16 红线（熵真源=secrets，
#      长度红线由 server Settings 构造校验二次把关）
#
# 【行为规格】
#   R1 配置是角色唯一持久真源：setNetworkRole/getConfig 消费面全部经
#      本件；env/内存态不承担角色记忆。
#   R2 token 只在进入 server 角色时生成（Minecraft 式配对：服务端重启
#      或重新生成前有效——重新生成入口本批不提供，挂账）；standalone/
#      client 角色不消费 token（回环/无引擎面）。
#   R3 schema_version 只认现值（未知版本=ValueError——前向兼容显式拒绝
#      非静默猜测）；写文件恒带 schema_version 供未来迁移链判版。
#
# 【测试要求】缺省态/往返持久化/原子性（失败不残留半写）/非法拒绝/
#   token 生成下界与稳定性。
#
# 【参照】ADR-028；联机第五批 token 红线（server settings R-6/R-7）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

DesktopRole = Literal["unconfigured", "standalone", "server", "client"]
VALID_ROLES: Final[tuple[str, ...]] = ("unconfigured", "standalone", "server", "client")
# token 熵源字节数：token_hex(16)=32 位 hex 字符（≥16 位红线一倍余量；
# server Settings API_TOKEN_MIN_LENGTH=16 为校验下界非建议值——文档推荐
# 32，本值即推荐形态）
TOKEN_BYTES: Final[int] = 2 ** (2 * 2)  # 16（幂积保白名单字面量集）
# 配置 schema 版本（迁移链判版槽——未知版本 load 即拒）
SCHEMA_VERSION: Final[int] = 1


def default_config_path() -> Path:
    """缺省配置路径：env WATERPRINT_DESKTOP_CONFIG 覆盖，否则
    ~/.config/waterprint/desktop.json（XDG 习惯位；跨发行版不依赖
    xdg-user-dirs——打包安装器可经 env 重定向）。"""
    override = os.environ.get("WATERPRINT_DESKTOP_CONFIG")
    if override:
        return Path(override)
    return Path.home() / ".config" / "waterprint" / "desktop.json"


def default_data_root() -> Path:
    """桌面壳数据根（项目/导出基点）：env WATERPRINT_DESKTOP_DATA_DIR
    覆盖，否则 ~/.local/share/waterprint（XDG 数据习惯位）。引擎
    Settings 的 projects_dir/exports_dir 由本根派生（桌面应用 CWD 不可
    靠——CWD 相对缺省不适用，server 裸机缺省面不沿用）。"""
    override = os.environ.get("WATERPRINT_DESKTOP_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / ".local" / "share" / "waterprint"


def generate_api_token() -> str:
    """配对 token 生成（secrets 密码学随机 token_hex——secrets 模块文档
    口径：适合认证凭据；hex 输出无歧义字符，复制分发友好）。"""
    return secrets.token_hex(TOKEN_BYTES)


@dataclass(frozen=True)
class DesktopConfig:
    """桌面壳持久配置（role=装配决策唯一输入；api_token=服务端配对凭据）。"""

    role: DesktopRole = "unconfigured"
    api_token: str = ""


class ConfigStore:
    """desktop.json 读写门（唯一持久通道；UTF-8+原子写+确定性形态）。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> DesktopConfig:
        """读配置：缺文件=unconfigured 缺省（首启态）；存在即严格校验
        （坏 JSON/未知角色/未知 schema_version/token 非空且短于红线均
        ValueError——fail fast 不静默回退）。"""
        if not self._path.is_file():
            return DesktopConfig()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"桌面壳配置不可读：{self._path}（{exc}）") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"桌面壳配置形态非法（须对象）：{self._path}")
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"桌面壳配置版本不支持：{raw.get('schema_version')!r}"
                f"（现值 {SCHEMA_VERSION}）——{self._path}"
            )
        role = raw.get("role")
        if role not in VALID_ROLES:
            raise ValueError(f"桌面壳配置角色非法：{role!r}——{self._path}")
        api_token = raw.get("api_token", "")
        if not isinstance(api_token, str):
            raise ValueError(f"桌面壳配置 api_token 形态非法：{api_token!r}——{self._path}")
        if api_token != "" and len(api_token) < TOKEN_BYTES:
            raise ValueError(
                f"桌面壳配置 api_token 长度 {len(api_token)} < {TOKEN_BYTES}"
                f"（服务端配对红线）——{self._path}"
            )
        return DesktopConfig(role=role, api_token=api_token)

    def save(self, config: DesktopConfig) -> None:
        """写配置（原子：tmp 同目录写全量后 os.replace——半写不残留；
        键排序+缩进 2+尾行换行：同输入双写字节级一致）。"""
        payload = {
            "schema_version": SCHEMA_VERSION,
            "role": config.role,
            "api_token": config.api_token,
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_name(self._path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, self._path)

    def ensure_server_token(self) -> str:
        """服务端配对 token 保管口：无则生成并持久化，有则原样返回
        （重启稳定——b5 配对卡「服务端重启或重新生成前有效」语义）。"""
        config = self.load()
        if config.api_token != "":
            return config.api_token
        token = generate_api_token()
        self.save(DesktopConfig(role=config.role, api_token=token))
        return token
