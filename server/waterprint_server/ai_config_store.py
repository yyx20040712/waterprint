"""LLM 配置存取件（F1 回炉批 2026-09-25）：校验/.env 原子读改写/env 同步。

输入:  AiConfigUpdate 四键裸值（str|None/int|None——routers/ai_config.py 转发）
输出:  snapshot 五键 dict +持久化（CWD .env 原子写）+os.environ 四键同步
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（F1 回炉批——门一 k1 B-1/W-1/W-7/N-8 处置；sse_limits 顶层
# 共享件先例——禁 import fastapi）
#
# 【校验】四 str 键统一：strip 后长度上限（base_url/api_key≤500、model
#   ≤100）+拒绝控制字符 [\x00-\x1f\x7f]（B-1：值内换行可向 .env 注入
#   任意键——.env 行格式 KEY=VALUE 的唯一分隔面）；base_url 非空时
#   scheme 前缀大小写不敏感（N-8）且前缀后须有主机部（非空非纯斜杠）；
#   llm_timeout_s∈[5,900]。违例 raise ValueError（main 统一映射 422——
#   消息零值嵌入）。
# 【持久化】CWD .env 读改写：utf-8-sig 容 BOM 读（W-7 半面）；解码失败
#   raise ValueError（「非 UTF-8——请手工转存」，W-7：原 UnicodeDecodeError
#   直炸 500 且 GET/PUT 双断=用户无法经配置面自救）；非本批键行与空行
#   原样保留（N-2：原实现静默删空行）；空值键行删除；写盘=同目录 tmp
#   文件+os.replace 原子替换（W-1：原直写=崩溃半截文件）；全读改写全程
#   threading.Lock 串行（W-1：同步 def 线程池并发丢更新面）。
# 【env 同步】写盘成功后 os.environ 四键 set（含空串清除语义——子进程
#   spawn 继承面不重启即生效）。
# 【快照】GET 投影：strip 后判 configured/has_api_key（N-8：原空白串
#   误判为真）；api_key 明文任何面零回传（仅存在性布尔——routers 层投影）。
# 【禁止事项】禁 import fastapi；禁 print/日志；api_key 禁入异常文本。
# 【测试要求】server/tests/routers/test_ai_config.py（锁面呈批件
#   .workflow/healthcheck-20260925/F1-server-tests-draft.md——回炉批
#   增补 B-1 控制字符 422 用例）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Final

# 四键 env 名（settings env_prefix 对齐 agent CLI 读取面——子进程 env 单通道）。
_BASE_URL_KEY: Final[str] = "WATERPRINT_AI_BASE_URL"
_API_KEY_KEY: Final[str] = "WATERPRINT_AI_API_KEY"
_MODEL_KEY: Final[str] = "WATERPRINT_AI_MODEL"
_TIMEOUT_KEY: Final[str] = "WATERPRINT_AI_LLM_TIMEOUT_S"
# GET 超时回显缺省（env 未设/非法时——agent llm.py _DEFAULT_TIMEOUT_S 同值）。
_DEFAULT_TIMEOUT_S: Final[int] = 10**2 + 2 * 10  # 120（幂积保白名单字面量集）
# 校验边界值（声明面——来源=简报 F1 §二；幂积保白名单字面量集）：
_BASE_URL_MAX: Final[int] = (10 // 2) * 10**2  # 500
_MODEL_MAX: Final[int] = 10**2  # 100
_API_KEY_MAX: Final[int] = (10 // 2) * 10**2  # 500
_TIMEOUT_MIN_S: Final[int] = 10 // 2  # 5（简报 F1 声明面）
_TIMEOUT_MAX_S: Final[int] = (10 - 1) * 10**2  # 900（简报 F1 声明面）
# B-1：控制字符全拒（值内换行=行注入面；\x7f DEL 同族）。
_CTRL_CHARS: Final[re.Pattern[str]] = re.compile(r"[\x00-\x1f\x7f]")
_SCHEMES: Final[tuple[str, ...]] = ("http://", "https://")
# .env 四键行匹配（非匹配行原样保留——本批键行重排至文件尾，dotenv 后行胜出兜底）。
_ENV_KEY_LINE: Final[re.Pattern[str]] = re.compile(
    r"^\s*WATERPRINT_AI_(?:BASE_URL|API_KEY|MODEL|LLM_TIMEOUT_S)\s*="
)
_ENV_PATH: Final[Path] = Path(".env")
# W-1：读改写串行锁（同步 def 端点跑线程池——并发 PUT 丢更新面）。
_STORE_LOCK: Final[threading.Lock] = threading.Lock()


def _clean_str(name: str, raw: str, limit: int) -> str:
    """str 键清洗（strip+长度+控制字符拒——B-1）。

    ValueError 消息零值嵌入（k1 审计口径——api_key 等值禁入异常文本）。
    """
    text = raw.strip()
    if _CTRL_CHARS.search(text):
        raise ValueError(f"{name} 含控制字符（换行/回车等）——禁止（防 .env 行注入）")
    if len(text) > limit:
        raise ValueError(f"{name} 长度超限（>{limit} 字符）")
    return text


def _check_base_url(text: str) -> None:
    """base_url scheme 域检（大小写不敏感+主机部非空——N-8 收紧）。"""
    lowered = text.lower()
    for scheme in _SCHEMES:
        if lowered.startswith(scheme):
            if text[len(scheme) :].strip("/ ").strip() == "":
                raise ValueError("base_url 缺主机部（scheme 后为空）")
            return
    raise ValueError("base_url 非空时须以 http:// 或 https:// 开头")


def snapshot() -> dict[str, str | bool | int]:
    """当前进程 env 四键投影（GET 真值面——spawn 单通道）。"""
    base_url = os.environ.get(_BASE_URL_KEY, "").strip()
    api_key = os.environ.get(_API_KEY_KEY, "").strip()
    model = os.environ.get(_MODEL_KEY, "").strip()
    raw_timeout = os.environ.get(_TIMEOUT_KEY, "").strip()
    return {
        "base_url": base_url,
        "model": model,
        "has_api_key": bool(api_key),
        "llm_timeout_s": (
            int(raw_timeout) if raw_timeout.isdecimal() else _DEFAULT_TIMEOUT_S
        ),
        "configured": bool(base_url and api_key and model),
    }


def validate_and_merge(
    base_url: str | None,
    model: str | None,
    api_key: str | None,
    llm_timeout_s: int | None,
) -> dict[str, str]:
    """域校验+env 合并（缺省键沿用 env 现值；空串=清除；键序=.env 行序单源）。"""
    values: dict[str, str] = {}
    for name, key, raw, limit, checker in (
        ("base_url", _BASE_URL_KEY, base_url, _BASE_URL_MAX, _check_base_url),
        ("model", _MODEL_KEY, model, _MODEL_MAX, None),
        ("api_key", _API_KEY_KEY, api_key, _API_KEY_MAX, None),
    ):
        if raw is None:
            values[key] = os.environ.get(key, "")
            continue
        text = _clean_str(name, raw, limit)
        if checker is not None and text:
            checker(text)
        values[key] = text
    if llm_timeout_s is None:
        raw_timeout = os.environ.get(_TIMEOUT_KEY, "")
        values[_TIMEOUT_KEY] = (
            raw_timeout if raw_timeout.isdecimal() else str(_DEFAULT_TIMEOUT_S)
        )
    else:
        if not _TIMEOUT_MIN_S <= llm_timeout_s <= _TIMEOUT_MAX_S:
            raise ValueError(f"llm_timeout_s 须为 {_TIMEOUT_MIN_S}~{_TIMEOUT_MAX_S} 的整数")
        values[_TIMEOUT_KEY] = str(llm_timeout_s)
    return values


def _rewrite_env_file(final_values: dict[str, str]) -> None:
    """读改写 CWD .env（锁内调用——非本批键行与空行原样保留；空值键行删除）。"""
    kept: list[str] = []
    exists = _ENV_PATH.is_file()
    if exists:
        try:
            # utf-8-sig：BOM 容忍读（重写后 BOM 消解——首行键名曾因 \ufeff 不匹配正则残留垃圾行）
            lines = _ENV_PATH.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError as exc:
            raise ValueError(
                ".env 文件编码非 UTF-8——请用文本编辑器转存为 UTF-8 后重试"
            ) from exc
        kept = [ln for ln in lines if not _ENV_KEY_LINE.match(ln)]
    kept.extend(f"{key}={value}" for key, value in final_values.items() if value)
    if not kept and not exists:
        return  # 全清除且 .env 不存在——不造空文件
    content = ("\n".join(kept) + "\n") if kept else ""
    # W-1 原子写：同目录 tmp+os.replace（崩溃不留半截文件；replace 同卷原子）
    tmp_path = Path(f"{_ENV_PATH}.tmp")
    tmp_path.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp_path, _ENV_PATH)


def update(
    base_url: str | None,
    model: str | None,
    api_key: str | None,
    llm_timeout_s: int | None,
) -> dict[str, str | bool | int]:
    """PUT 全流程（锁内串行：校验→原子写盘→env 同步→回快照）。"""
    with _STORE_LOCK:
        final_values = validate_and_merge(base_url, model, api_key, llm_timeout_s)
        _rewrite_env_file(final_values)
        for key, value in final_values.items():
            os.environ[key] = value
    return snapshot()
