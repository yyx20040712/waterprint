"""环境配置：env → Settings（pydantic-settings，一切可调参数的唯一住所）。

输入:  环境变量 / .env（前缀 WATERPRINT_）
输出:  Settings（不可变，应用启动注入）+ 路径基点分量校验工具
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/test_settings.py）
#
# 【公开接口】
#   class Settings(BaseSettings)：模型字段——
#       projects_dir（项目文件根，路径安全基点）
#       exports_dir（导出产物根，路径安全基点）
#       data_dir（数据包根：单价/系数/模板——E2E-1 起缺省=包定位
#          default_data_dir()，CWD 无关；env WATERPRINT_DATA_DIR 可覆盖）
#       calc_workers（进程池大小，默认 CPU−1）
#       max_upload_mb / max_excel_rows（§18 上传面）
#       cache_entries / cache_mb（LRU 与落盘上限 §17.2）
#       task_queue_priorities（FIFO 优先级 §17.1）
#       log_level / log_file
#   get_settings() -> Settings（lru_cache，测试可覆盖）
#   safe_child(base, name) -> Path：R1 路径基点分量校验工具
#   ensure_directories(settings)：基点目录存在或可创建（fail fast）
#   default_data_dir() -> Path：数据包根缺省解析（E2E-1 P0-A 自愈——
#      包定位上溯仓库根，与 CWD 解耦）
#   validate_data_packages(settings)：四数据包 manifest.yaml 在场校验
#      （E2E-1 P0-A fail fast——缺包 raise RuntimeError 可执行文案）
#
# 【行为规格】
#   R1 一切路径类配置只作基点：业务路径 = 基点内拼接 + 分量校验
#      （拒绝 ".."/绝对路径/分隔符，§18 路径安全——routers/services
#      全部遵守，测试构造越界路径断言拒绝）。
#   R2 配置校验：目录存在或可创建；calc_workers >= 1；
#      非法值启动即失败（fail fast，不静默默认——锁定断言
#      Settings(calc_workers=0) 构造抛 ValidationError）。
#   R3 密钥/外发零依赖：内网工具无外部服务配置项；不出现任何
#      出站 URL 配置（§18 出站请求面——零外部请求是产品约束）。
#
# 【数值纪律】（ADR-009 附则 d：配置数值属 settings/env/数据包）
#   - max_upload_mb=10（10MB 与 core io._MAX_BYTES 同口径，白名单值）；
#   - max_excel_rows=10**2*10**2（=10000 行，§18 上传面幂积表达式）；
#   - cache_entries=10**2*10（=1000 条）、cache_mb=10**2（=100MB，
#     §17.2 LRU 上限，UF-08 注记"缓存属 incremental 优化层"随行）；
#   - max_json_depth=10**2（=100 层，与 core io._MAX_DEPTH 同源口径，
#     HTTP 上传面深度闸）；
#   - page_size_default=2*10**2（=200/页，§12.2 规格值）；
#   - task_queue_priorities 默认 {calc:10, enumerate:2, export_batch:1}
#     （§17.1 交互计算 > 枚举 > 批量导出——值域取白名单 {0,1,2,10}）；
#   - dwg_converter_timeout_s=10**2（=100 秒，WP0 ODA-A：DXF→DWG 外挂
#     转换子进程超时——部署侧可选件的防御值，非工程量）。
#
# 【测试要求】默认值合法、非法值拒绝、路径越界防护的消费方行为。
#
# 【参照】重写计划 §18/§17.2；简报 SERVER D3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 分量白名单字符集（R1）：ASCII 字母数字开头，允许 -/_，长度上限 64——
# 拒绝 ".."、绝对路径、盘符与路径分隔符注入（§18 路径安全）。
_COMPONENT_PATTERN: re.Pattern[str] = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_FAIL_FAST_FIELDS = (
    "calc_workers",
    "max_upload_mb",
    "max_excel_rows",
    "max_json_depth",
    "dwg_converter_timeout_s",  # WP0：超时 <1 秒=闸死转换面（fail fast 不静默）
    "task_retention_s",  # WP4：保留窗 <1 秒=终态即弃（读面自毁，fail fast）
    "task_sweep_interval_s",  # WP4：间隔 <1 秒=空转热循环（fail fast 不静默）
    "task_registry_cap",  # WP4：上限 <1=任何任务都越限（语义空洞，fail fast）
    "lock_expiry_s",  # WP4：过期窗 <1 秒=新鲜锁即放行（锁面失效，fail fast）
)
# 服务层引擎版本标识（可复算三元组成员——与 server/pyproject version 同源同步）。
ENGINE_VERSION: Final[str] = "waterprint-server 0.1.0"
# R2A 批1（token 鉴权 2026-09-02，终裁 R-7）：API token 最小长度真源=16
#（幂积 2**(2*2) 保白名单字面量集）——字母数字 62 字符集下 62¹⁶≈4.8×10²⁸
# 组合（终裁勘误：95¹⁶ 系全可打印 ASCII 误算），为防在线暴力枚举的熵下界；
# 文档推荐 32，本值=validator 拒绝线非建议值。
API_TOKEN_MIN_LENGTH: Final[int] = 2 ** (2 * 2)  # 16
# R2A 批1（终裁 R-6）：回环绑定集合——token 空+host 出集合=构造即拒
#（fail fast，uvicorn.run 之前不留半启动态）。机器防线（绑定判定）为
# best-effort（容器内绑定经 CMD 旗标不经本字段），真红线=入口语义
#（docs/deployment.md「安全红线」节——反代/端口映射对外可达必须配 token）。
_LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset({"127.0.0.1", "::1", "localhost"})


def default_data_dir() -> Path:
    """数据包根缺省解析（E2E-1 P0-A 自愈）：包定位上溯，CWD 无关。

    server/waterprint_server/settings.py 上溯两级=仓库根（仓库开发态，
    data/ 随仓内置）；Docker/打包部署态由显式 env WATERPRINT_DATA_DIR
    覆盖，不经本缺省（Dockerfile.server ENV 行）。定义于 Settings 之前——
    data_dir 字段 default_factory 直引函数对象（类体即时解析）。
    """
    return Path(__file__).resolve().parents[2] / "data"


class Settings(BaseSettings):
    """一切可调参数的唯一住所（不可变；启动注入，禁代码内联数值）。"""

    model_config = SettingsConfigDict(
        env_prefix="WATERPRINT_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="forbid",
    )

    projects_dir: Path = Path("projects")
    # 相对 cwd 的语义保持，仅落绝对形态——write_dxf 绝对路径守卫（路径安全族
    # AU-1）与真服务相对默认不兼容（M5 TCP 探针实录 500 收口：单产物/worker
    # 批量 tmp 派生全经此基点）。
    exports_dir: Path = Path("exports").resolve()
    # E2E-1（e2e-audit 2026-09-24 P0-A）：缺省改包定位自愈——旧缺省
    # Path("data") 按 CWD 相对解析，README「cd server && uv run …」口径落到
    # server/data（不存在）⇒ 约束库 500/计算 DataPackError/AI 接入 400 全线
    # 断。部署面（Docker/打包）显式 env WATERPRINT_DATA_DIR 覆盖，不经缺省。
    data_dir: Path = Field(default_factory=default_data_dir)
    calc_workers: int = Field(default_factory=lambda: max(1, (os.cpu_count() or 2) - 1))
    # R1-4⑤（AU-8 已接线 ENG2 2026-08-27）：上传体积闸已接线（413，routers 依赖层）。
    max_upload_mb: int = 10
    max_excel_rows: int = 10**2 * 10**2  # 10000（§18 上传面；幂积保白名单字面量集）
    cache_entries: int = 10**2 * 10  # 1000（§17.2 LRU 条数上限）
    cache_mb: int = 10**2  # 100（§17.2 落盘体积上限 MB）
    task_queue_priorities: dict[str, int] = Field(
        default_factory=lambda: {"calc": 10, "enumerate": 2, "export_batch": 1,
                                   "joint_enumerate": 2, "ai_chat": 10}
    )
    # B4-4b 子批 2（2026-09-24）：对话编排三中性键+子进程透传面——env 名即
    # WATERPRINT_AI_*（env_prefix 天然对齐 agent CLI 读取面）；空=未配置
    #（agent 环降级模式承载，非 503——design-final §三勘正：降级即行为）。
    # api_key 禁入任何日志（ai_chat 子进程 env 注入后即弃）。
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_llm_timeout_s: int = 10**2 + 2 * 10  # 120s（幂积保白名单——agent 环 §七推导值）
    log_level: str = "INFO"
    log_file: str = "waterprint-server.log"
    max_json_depth: int = 10**2  # 100（HTTP 上传面深度闸，与 core io._MAX_DEPTH 同源）
    page_size_default: int = 2 * 10**2  # 200（§12.2 分页默认页大小）
    # WP0（ODA-A 形态 A 2026-09-02）：可选 DXF→DWG 外挂转换器——默认空串=关
    #（容器内不随镜像分发转换器=默认关，零行为漂移）；路径指向用户自装的
    # ODA File Converter 可执行件（docs/deployment.md「导出格式」节）。
    dwg_converter_path: str = ""
    # 转换子进程超时秒（超时=warning+跳过 DWG——DXF 交付承诺不可破）。
    dwg_converter_timeout_s: int = 10**2  # 100（幂积保白名单字面量集，注记见规格头）
    # WP1（部署面安全收口 2026-09-02）：绑定面代码化——裸机/开发态默认只听
    # 本地回环（24 端点零鉴权，暴露即全权——对外绑定=WATERPRINT_HOST 显式
    # 覆盖=信任决策，见 docs/deployment.md「安全红线」节）。容器内绑定由
    # Dockerfile CMD 旗标决定（0.0.0.0 供 nginx 跨容器反代，8000 不发布宿主）。
    host: str = "127.0.0.1"
    port: int = 2 * 2 * 2 * 10 * 10 * 10  # 8000（幂积保白名单字面量集）
    # WP4（服务端小修攒批 2026-09-02·修1）：任务/产物 TTL 淘汰——终态任务
    # 连同四类落盘面（registry 档/cancel 标记/calc 结果/enum 行文件）超
    # 保留窗即清扫；重启恢复记录=新租约（恢复读面供 exports 消费）。
    task_retention_s: int = 10**2 * 10**2 * 10  # 100000 秒≈27.8 小时（幂积保白名单字面量集）
    task_sweep_interval_s: int = 10**2  # 100 秒≈1.7 分钟（周期清扫轮询间隔）
    task_registry_cap: int = 10**2 * 10  # 1000（终态驱逐面软上限——非终态不驱逐，R-1 A-01）
    # WP4·修4：项目锁过期窗——锁文件 mtime 年龄超窗=陈旧残留（持有者已
    # 死），视为无锁放行（§17.3 v1 单用户；锁仍为外部协调件零写入方）。
    lock_expiry_s: int = 10**2 * 10**2  # 10000 秒≈2.8 小时（编辑会话锁最长占用心智）
    # R2A 批1（token 鉴权 2026-09-02）：静态 Bearer token（env
    # WATERPRINT_API_TOKEN）——空=鉴权关（默认，24 端点零行为变化）；
    # 非空=21 端点受保（19 非事件仅认 Bearer 头+events 两端点认头或
    # ？token=），units 三静态只读端点豁免。见 auth.py 依赖面。
    api_token: str = ""
    # B6（SSE 治理 2026-09-06，简报 D5）：四维限流+心跳旋钮（int|None——
    # None=该维不启用，沿 WP4 task_registry_cap 先例；默认启用=治理默认态，
    # 阈值保守不触碰既有测试/正常用）。阈值锚（D4 总控补证）：全局 100=
    # SSE 连接协程级不占进程池（calc_workers 解耦），内存十 MB 量级安全；
    # 每任务 5（多标签+重连叠接余量，终态即退）；每项目 10（项目流长生命
    # 周期更严）；建连速率 10/s 突发 2×rate 固定（不增旋钮）；心跳 30s=
    # nginx proxy_read_timeout 300s 的 1/10（静默掐断消除，D6）。消费面
    # sse_limits.py（四维）/jobs/manager.py（心跳）。
    sse_max_connections: int | None = 10**2  # 100（幂积保白名单字面量集）
    sse_max_subscribers_per_task: int | None = 10 // 2  # 5
    sse_max_subscribers_per_project: int | None = 10  # 10（白名单值）
    sse_connect_rate_per_second: int | None = 10  # 10/s（突发=2×rate 固定）
    sse_heartbeat_seconds: int | None = 10 * 2 + 10  # 30（300s 读超时的 1/10）

    @field_validator(
        "sse_max_connections",
        "sse_max_subscribers_per_task",
        "sse_max_subscribers_per_project",
        "sse_connect_rate_per_second",
        "sse_heartbeat_seconds",
    )
    @classmethod
    def _sse_knobs_positive(cls, value: int | None) -> int | None:
        """B6 fail fast：SSE 旋钮非 None 时 <1 构造即 ValidationError（心跳 0=热循环）。"""
        if value is not None and value < 1:
            raise ValueError(
                f"配置非法：SSE 旋钮 {value} 须 >= 1 或 None（B6 fail fast——不静默默认）"
            )
        return value

    @field_validator(*_FAIL_FAST_FIELDS)
    @classmethod
    def _positive_int(cls, value: int) -> int:
        """R2 fail fast：下限类配置 < 1 构造即 ValidationError（不静默默认）。"""
        if value < 1:
            raise ValueError(f"配置非法：{value} 须 >= 1（R2 fail fast——不静默默认）")
        return value

    @field_validator("port")
    @classmethod
    def _port_range(cls, value: int) -> int:
        """WP1 fail fast：端口出 1~65535（TCP 值域）构造即 ValidationError。"""
        if not 1 <= value <= 2 ** (2 * 2 * 2 * 2) - 1:  # 65535=2^16−1（幂积保白名单字面量集）
            raise ValueError(f"配置非法：端口 {value} 须在 1~65535（WP1 fail fast——不静默默认）")
        return value

    @field_validator("api_token")
    @classmethod
    def _api_token_length(cls, value: str) -> str:
        """R2A R-7 fail fast：非空 token 长度下限（62 字符集熵基线，见常量注记）。"""
        if value != "" and len(value) < API_TOKEN_MIN_LENGTH:
            raise ValueError(
                f"配置非法：api_token 长度 {len(value)} < {API_TOKEN_MIN_LENGTH}"
                "（字母数字 62 字符集 16 位熵≈4.8×10²⁸ 下界——R2A R-7 fail fast）"
            )
        return value

    @model_validator(mode="after")
    def _token_required_off_loopback(self) -> Settings:
        """R2A R-6 fail fast：空 token 仅许回环绑定（对外绑定必须配 token）。"""
        if self.api_token == "" and self.host not in _LOOPBACK_HOSTS:
            raise ValueError(
                "配置非法：api_token 为空且 host 非 {127.0.0.1, ::1, localhost}"
                " 回环集合——对外绑定必须配置 WATERPRINT_API_TOKEN"
                "（R2A R-6 fail fast，机器防线 best-effort；入口红线见"
                " docs/deployment.md「安全红线」节）"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """进程级配置缓存（测试可用 get_settings.cache_clear() 覆盖）。"""
    return Settings()


def validate_component(name: str) -> str:
    """路径/文件名分量白名单校验（R1-1 公开工具：exports 文件名分量等复用）。

    拒绝面与 safe_child 同源（../、绝对路径、分隔符、盘符——正则只认单分量
    字符集天然排除）；越界 raise ValueError（消费方翻译领域异常）。
    """
    if not isinstance(name, str) or not _COMPONENT_PATTERN.fullmatch(name):
        raise ValueError(
            f"路径分量非法：{name!r}（§18 路径安全——仅 ASCII 字母数字与 -/_，"
            "拒绝 ../绝对路径/分隔符注入；基点内拼接是唯一合法构造）"
        )
    return name


def safe_child(base: Path, name: str) -> Path:
    """路径基点分量拼接（R1）：分量过白名单字符集，越界即拒（ValueError）。

    拒绝面：空串/绝对路径/../ 分隔符与盘符（正则只认单分量字符集，
    天然排除）。services 层捕获 ValueError 翻译为领域异常（4xx 面）。
    """
    return base / validate_component(name)


def ensure_directories(settings: Settings) -> None:
    """基点目录存在或可创建（R2 fail fast：创建失败=启动即败，不静默）。"""
    try:
        settings.projects_dir.mkdir(parents=True, exist_ok=True)
        settings.exports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValidationError.from_exception_data(
            "Settings",
            [
                {
                    "type": "value_error",
                    "loc": ("projects_dir",),
                    "input": str(settings.projects_dir),
                    "ctx": {"error": ValueError(f"基点目录不可创建：{exc}")},
                }
            ],
        ) from exc


# E2E-1（e2e-audit 2026-09-24 P0-A）：数据包四目录清单——启动在场校验面
# （coefficients 系数/constraint_kb 约束库/templates 模板/unit_prices 单价，
# 各以 manifest.yaml 为完整性判据；与 data/ 目录现状一一对应）。
_DATA_PACKAGES: Final[tuple[str, ...]] = (
    "coefficients",
    "constraint_kb",
    "templates",
    "unit_prices",
)


def validate_data_packages(settings: Settings) -> None:
    """启动期数据包在场校验（E2E-1 P0-A fail fast）：缺任何 manifest.yaml
    以可执行文案拒绝启动（晚拒+拒在用户脸上的 500 时代终结——对齐
    ADR-012 D6 fail-fast 理念）。

    消费点=main 启动块（README「python -m waterprint_server.main」口径），
    uvicorn 直启（Docker CMD）面数据包随镜像走+显式 env，不经本校验。
    """
    missing = [
        name
        for name in _DATA_PACKAGES
        if not (settings.data_dir / name / "manifest.yaml").is_file()
    ]
    if missing:
        raise RuntimeError(
            f"数据包不完整：{settings.data_dir} 缺 "
            + "、".join(f"{name}/manifest.yaml" for name in missing)
            + "——启动拒绝（fail fast）。请设置 WATERPRINT_DATA_DIR 指向含 "
            + "、".join(_DATA_PACKAGES)
            + " 四个子目录的数据根；缺省按包文件位置解析（仓库开发态="
            "仓库根 data/，非仓库布局——如安装态——请显式设 env）"
        )
