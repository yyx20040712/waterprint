"""单元库浏览验收探针（UF-52——批6m 验收追认收口，门二实证部）。

目的：对左侧单元库浏览面（webapp Sider UnitLibrary）做端到端验收——
36 条目四线+内置分组全列+Drawer 参数面/端口面预览正确（wave6-master-plan
批6m 节验收口径）。**数据判据独立 oracle 化**（门一 d1-W2 处置）：期望值
不写死探针内——启动时实读 GET /api/units 按 business_line×kind 独立
推导组计数/叶总数/抽样单元参数端口行数，再对 UI 渲染面断言（UI vs API
两面独立，非按自定常数自证）。

**不入 pytest 收集**（tools/ 不在 testpaths；依赖 uvicorn:8000+vite:5173
活链路——非 hermetic，手动验收工具+清单形态，先例=tools/oda_smoke.py
批6j；清单=同目录 units_browser_probe.md）。

用法（前置：server 与 vite dev 双起——见 units_browser_probe.md §一）::

    python tools/units_browser_probe.py            # 全断言族（exit 0=PASS）

断言族（P0 oracle+P1~P10，任一失败=FAIL 退出码 1）：
  P0  API oracle 推导（独立于 UI：组计数字典/叶总数/抽样单元行数）
  P1  组行计数与 oracle 恰等（四线+内置〔5 组〕——N8 术语口径）
  P2  叶行总数与 oracle 恰等（title=unit_id 的 span——排除 antd 自带
      title 的 node-content-wrapper）
  P3  foot 计数条口径：左=kind=unit 条数（32）右=组数含内置组（5）——
      C2-lib GL-01 用户裁决 2026-09-10（视觉稿形态保留）在册口径
  P4  叶行英文码不显示（用户裁定 2026-09-10 C2-lib——悬浮 title=全
      unit_id 唯一追溯通道；git 1fd8b8182+app README 在案）
  P5  抽样单元（API 首个多参包单元）Drawer：标题三件+参数/端口行列数
      与 oracle 恰等；参数五列/端口四列
  P6  参数列物理意义 label_zh 在场（C2-ALIGN A5r——非裸 field_id）
  P7  搜索过滤（unit_id 子串）恰命中 oracle 推导集
  P8  内置空参单元 Drawer 空参数文案「内置节点无参数面」（R 轮 G1-02）
  P9  console 零 error+零 pageerror（探针域内全页面告警归零口径——
      ChatPane Drawer 弃用 width prop 已随批6m 迁移收口）
  P10 Drawer 宽度等价性证明（d1-W4 处置）：styles.wrapper 迁移后
      .ant-drawer-content-wrapper 实测宽=期望值（单元库 480〔本批
      面〕+聊天 420〔批6m 邻域收口面〕）——width prop→styles.wrapper
      同节点恒等实证
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000/api/units"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".workflow" / "b6m-probe-out"
OUT.mkdir(parents=True, exist_ok=True)

LINE_ORDER = ["municipal", "conveyance", "mine_water", "sludge"]

results: list[tuple[str, bool, str]] = []


def check(pid: str, ok: bool, detail: str) -> None:
    results.append((pid, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'} {pid}: {detail}")


def leaf_spans(page):
    """叶行 span 集（title=unit_id——排除 antd wrapper 自带 title）。"""
    return page.locator(
        "aside .ant-tree span[title]:not(.ant-tree-node-content-wrapper)"
    ).all()


def fetch_oracle() -> dict:
    """P0 数据 oracle：GET /api/units 实读独立推导（零 UI 参与）。"""
    with urllib.request.urlopen(API, timeout=10) as resp:
        catalog = json.load(resp)
    units = catalog["units"]
    unit_kind = [u for u in units if u["kind"] != "builtin"]
    by_line: "OrderedDict[str, int]" = OrderedDict()
    for line in LINE_ORDER:
        by_line[line] = sum(
            1 for u in unit_kind if u["business_line"] == line
        )
    builtin = [u for u in units if u["kind"] == "builtin"]
    sample = next(
        (u for u in unit_kind if len(u.get("params") or []) >= 5), None
    )
    empty_builtin = next(
        (u for u in builtin if not (u.get("params") or [])), None
    )
    return {
        "total": len(units),
        "unit_count": len(unit_kind),
        "group_counts": dict(by_line),
        "builtin_count": len(builtin),
        "sample": sample,
        "empty_builtin": empty_builtin,
    }


def main() -> int:
    oracle = fetch_oracle()
    print(
        f"[oracle] total={oracle['total']} units={oracle['unit_count']} "
        f"builtin={oracle['builtin_count']} lines={oracle['group_counts']}"
    )
    console_errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.on(
            "console",
            lambda m: console_errors.append(m.text) if m.type == "error" else None,
        )
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("aside .ant-tree", timeout=30_000)
        page.wait_for_timeout(1200)

        # P0 oracle 自身健全性（非空+抽样在场）
        check(
            "P0",
            oracle["total"] > 0
            and oracle["sample"] is not None
            and oracle["empty_builtin"] is not None,
            f"oracle 推导健全 total={oracle['total']}",
        )

        # P1 组行计数（oracle 推导对照）
        zh = {
            "municipal": "市政污水",
            "conveyance": "输送提升",
            "mine_water": "矿井水",
            "sludge": "污泥处理",
        }
        texts = [
            t.strip()
            for t in page.locator("aside .ant-tree-treenode").all_inner_texts()
            if t.strip()
        ]
        for line, count in oracle["group_counts"].items():
            hit = [t for t in texts if zh[line] in t]
            ok = any(f"({count})" in t for t in hit)
            check(f"P1-{zh[line]}", ok, f"组行={hit[:2]} 期望含 ({count})")
        check(
            "P1-内置节点",
            any(
                f"({oracle['builtin_count']})" in t
                for t in texts
                if "内置节点" in t
            ),
            f"内置组期望含 ({oracle['builtin_count']})",
        )

        # P2 叶行总数
        leaves = leaf_spans(page)
        check(
            "P2",
            len(leaves) == oracle["total"],
            f"叶行={len(leaves)} oracle={oracle['total']}",
        )

        # P3 foot 计数条（口径注记：左=kind=unit 计数，右=组数含内置组）
        foot = page.locator("aside").first.inner_text()
        check(
            "P3",
            f"{oracle['unit_count']} 单元" in foot
            and f"{len(oracle['group_counts']) + 1} 组" in foot,
            f"foot 期望 {oracle['unit_count']} 单元/"
            f"{len(oracle['group_counts']) + 1} 组（含内置组）",
        )

        # P4 叶行英文码不显示（抽样=oracle 首个 unit）
        sample = oracle["sample"]
        row = page.locator(
            f"aside .ant-tree span[title='{sample['unit_id']}']"
        ).first
        row_text = row.inner_text()
        check(
            "P4",
            sample["unit_id"] not in row_text,
            f"叶行={row_text!r} 不含码 {sample['unit_id']}",
        )

        # P5 抽样单元 Drawer 预览（行列数与 oracle 恰等）
        row.click()
        page.wait_for_selector(".ant-drawer-open", timeout=10_000)
        page.wait_for_timeout(600)
        drawer = page.locator(".ant-drawer").first
        dtext = drawer.inner_text()
        title_ok = (
            sample["name_zh"] in dtext
            and sample["unit_id"] in dtext
            and "单元" in dtext
        )
        tables = drawer.locator(".ant-table").all()
        exp_params = len(sample.get("params") or [])
        exp_ports = len(sample.get("ports") or [])
        param_rows = tables[0].locator("tbody tr").count() if tables else -1
        port_rows = tables[1].locator("tbody tr").count() if len(tables) > 1 else -1
        param_cols = tables[0].locator("thead th").count() if tables else -1
        port_cols = (
            tables[1].locator("thead th").count() if len(tables) > 1 else -1
        )
        check(
            "P5",
            title_ok
            and param_rows == exp_params
            and port_rows == exp_ports,
            f"标题={title_ok} 参数行={param_rows}/{exp_params} "
            f"端口行={port_rows}/{exp_ports}",
        )
        check(
            "P5-cols",
            param_cols == 5 and port_cols == 4,
            f"参数列={param_cols}(期5) 端口列={port_cols}(期4)",
        )
        # P10-单元库抽屉宽度等价（styles.wrapper 迁移后实测——选择器锚
        # 开态抽屉：querySelector 首匹配可能是 DOM 在前的已关抽屉宽 0）
        uw = page.evaluate(
            "document.querySelector('.ant-drawer-open .ant-drawer-content-wrapper')"
            "?.getBoundingClientRect().width ?? 0"
        )
        page.screenshot(path=str(OUT / "b6m-drawer-sample.png"))

        # P6 参数列物理意义在场
        first_cell = (
            tables[0].locator("tbody tr").first.inner_text()
            if param_rows > 0
            else ""
        )
        headers = (
            [h.strip() for h in tables[0].locator("thead th").all_inner_texts()]
            if param_cols > 0
            else []
        )
        check(
            "P6",
            headers[:2] == ["参数", "量纲"]
            and any("\u4e00" <= ch <= "\u9fff" for ch in first_cell),
            f"表头={headers} 首行={first_cell[:24]!r}",
        )

        # P7 搜索过滤（oracle 推导命中集）
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        needle = sample["unit_id"].split("_")[-1]
        expect_ids = sorted(
            u["unit_id"]
            for u in [oracle["sample"]]  # 命中集=unit_id 含针的全体
        )
        all_units = json.loads(
            urllib.request.urlopen(API, timeout=10).read()
        )["units"]
        expect_ids = sorted(
            u["unit_id"] for u in all_units if needle in u["unit_id"]
        )
        page.locator("aside input").first.fill(needle)
        page.wait_for_timeout(600)
        visible = sorted(
            s.get_attribute("title") for s in leaf_spans(page)
        )
        check(
            "P7",
            visible == expect_ids,
            f"针={needle} 命中={visible} oracle={expect_ids}",
        )
        # P7b 中文名搜索可命中（k1-W2 处置——显示面=name_zh 与搜索面
        # 一致性钉死：用户可见名必须可检索，防「码可搜名不可搜」断裂）
        zh_needle = sample["name_zh"][-2:]
        expect_zh = sorted(
            u["unit_id"]
            for u in all_units
            if zh_needle in u["name_zh"] or zh_needle in u["unit_id"]
        )
        page.locator("aside input").first.fill(zh_needle)
        page.wait_for_timeout(600)
        visible_zh = sorted(
            s.get_attribute("title") for s in leaf_spans(page)
        )
        check(
            "P7b",
            sample["unit_id"] in visible_zh
            and visible_zh == expect_zh,
            f"中文针={zh_needle!r} 命中={visible_zh} oracle={expect_zh}",
        )
        page.screenshot(path=str(OUT / "b6m-search.png"))

        # P8 内置空参单元 Drawer 空参数文案
        page.locator("aside input").first.fill("")
        page.wait_for_timeout(400)
        eb = oracle["empty_builtin"]
        page.locator(
            f"aside .ant-tree span[title='{eb['unit_id']}']"
        ).first.click()
        page.wait_for_selector(".ant-drawer-open", timeout=10_000)
        page.wait_for_timeout(500)
        jtext = page.locator(".ant-drawer").first.inner_text()
        check(
            "P8",
            "内置节点无参数面" in jtext,
            f"{eb['unit_id']} 空参数文案在场",
        )

        # P9 console 零错误
        check("P9", len(console_errors) == 0, f"errors={console_errors[:3]}")

        # P10 聊天 Drawer 宽度等价（ChatPane 迁移面——420 恒等证明）
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        chat_btn = page.locator("[data-testid='wp-chat-open'], .wp-chat-open")
        if chat_btn.count() == 0:
            # 顶栏按钮兜底定位（含「AI」或「对话」字样的按钮）
            chat_btn = page.locator("button", has_text="对话")
        chat_btn.first.click()
        page.wait_for_selector(".ant-drawer-open", timeout=10_000)
        page.wait_for_timeout(500)
        cw = page.evaluate(
            "document.querySelector('.ant-drawer-open .ant-drawer-content-wrapper')"
            "?.getBoundingClientRect().width ?? 0"
        )
        check(
            "P10-lib",
            abs(uw - 480) <= 1,
            f"单元库 Drawer 实测宽={uw}（期 480——styles.wrapper 同节点）",
        )
        check(
            "P10-chat",
            abs(cw - 420) <= 1,
            f"聊天 Drawer 实测宽={cw}（期 420——width prop 迁移恒等）",
        )
        page.screenshot(path=str(OUT / "b6m-drawer-chat.png"))

        browser.close()

    ok_all = all(ok for _, ok, _ in results)
    report = {
        "verdict": "PASS" if ok_all else "FAIL",
        "oracle": {
            "total": oracle["total"],
            "unit_count": oracle["unit_count"],
            "group_counts": oracle["group_counts"],
            "builtin_count": oracle["builtin_count"],
        },
        "checks": [{"id": p, "ok": o, "detail": d} for p, o, d in results],
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "b6m-probe-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"\nverdict={report['verdict']} "
        f"({sum(o for _, o, _ in results)}/{len(results)})"
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
