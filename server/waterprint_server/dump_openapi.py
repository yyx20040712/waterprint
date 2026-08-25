"""OpenAPI 契约导出入口：app → api-contracts/openapi.json（确定性序列化）。

输入:  无（模块级 app 经 create_app(get_settings()) 装配）
输出:  api-contracts/openapi.json（sort_keys+indent 确定性 JSON——只由
       本模块生成入库，禁手改；双跑 diff 稳定=生成物确定性探针）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（SERVER D5，Ruling ②：M2 收口=后端 API 完整+OpenAPI 导出就绪）
#
# 【公开接口】
#   python -m waterprint_server.dump_openapi [--out <path>]
#       默认输出 <仓库根>/api-contracts/openapi.json
#   dump(schema) -> str：确定性序列化（sort_keys+indent=2+ensure_ascii
#       False——与 core 确定性序列化纪律同款）
#
# 【行为规格】
#   R1 生成物只经本模块入库（README 规则：禁手改——orval 生成物的
#      单一事实源）；CI contract-drift job 不启用（挂账 M3 前与 orval
#      一起收口——undefined-features-register 登记）。
#   R2 确定性：同 app 双跑字节相同（dump 双跑 diff 探针实录）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "api-contracts" / "openapi.json"


def dump(schema: dict[str, Any]) -> str:
    """确定性序列化（键排序+两空格缩进+UTF-8 保真+尾换行）。"""
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """导出入口（stdout 摘要；退出码 0=成功 2=写失败）。"""
    arguments = list(sys.argv[1:] if argv is None else argv)
    out = Path(arguments[arguments.index("--out") + 1]) if "--out" in arguments else DEFAULT_OUT
    from waterprint_server.main import app  # noqa: PLC0415  # 延迟装配（本模块导入零副作用）

    text = dump(app.openapi())
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"[FAIL] OpenAPI 导出写失败：{exc}")
        return 2
    operations = sum(len(methods) for methods in app.openapi()["paths"].values())
    print(f"[OK] OpenAPI 导出：{out}（{operations} 端点操作）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
