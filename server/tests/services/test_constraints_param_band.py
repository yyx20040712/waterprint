"""constraints 服务 param_band 伴生件：1A4 批单元参数正性域面契约（拆分件）。

输入:  waterprint_server.services.constraints（list_constraints）+真源 kb（仓库 data 面）
输出:  param_band 113 条面契约断言（键面/表达式/unit_kinds 非空升序选条/
       WARN+flag/族级出处+追认标记随行——109 存量〔P10 追认笔回写〕+4 补录
       新键生而已追认）
背景:  1A4 批（2026-10-04）自 test_constraints.py 拆分——主件 517 行破 §2
       500 行预算墙（W3 前向规范：测试新增预估触墙首笔即落独立伴生件
       ——test_app_validation_mass_balance 拆分先例同款）。
"""

from __future__ import annotations

import importlib
from pathlib import Path

_mod = importlib.import_module("waterprint_server.services.constraints")
list_constraints = getattr(_mod, "list_constraints")

# 真源 kb 面（仓库 data 目录——conftest REPO_DATA 同源推导）
_REPO = Path(__file__).resolve().parents[3] / "data"
# 1A4 批 2.0.0：param_band 109 条（param.<field>.positive——28 单元
# _PARAMS_POSITIVE 机扫单源投影逐字段一条；实扫单源=.workflow/
# 1a4-20261004/scan_params_positive.py：189 参数次/109 唯一键与主控预扫
# 三方一致）；P10 批 2.1.0：109→113（+4 补录新键 h/s/alpha/b_throat
# 生而已追认+n/b 两键 unit_kinds 扩容 municipal_cugeshan/xigeshan——
# 31 单元 200 参数次，实扫单源=.workflow/p10-20261005/
# scan_params_positive_p10.py）
_PARAM_BAND_COUNT = 113
# P10 批补录四键（生而已追认——source/value_basis 随批追认标记；109 存量
# 起草标记归 P10 追认笔统一回写后收紧为全族已追认）
_P10_SUPPLEMENT_KEYS = {
    "param.h.positive", "param.s.positive", "param.alpha.positive",
    "param.b_throat.positive",
}


def test_param_band_entries_carry_positive_domain_contract() -> None:
    """1A4：param_band 面契约——单元参数正性域带族（28 单元
    _PARAMS_POSITIVE 机扫单源投影，逐字段一条同字段跨单元聚合）；
    键面 `param.<field>.positive`+表达式单子句单侧正性 `<field> > 0`
    （DSL 右值常量合规；NaN>0=False→越带→警告——声明期 NaN 检出
    =FZ-4 计算期守卫的前置报告面）；unit_kinds 非空=节点 ID 选条判据
    （geometry_guard 非空先例形态——与 input_band/mass_balance 恒空
    kind 直判族接线红线分立）且升序；WARN/flag 仪表灯（block 断路器
    归 P1 后续批挂账）；已追认（Ruling 2026-10-05 P10 批——109 存量随批
    回写+4 补录键生而已追认）；消费面=core app_validation param_band
    分支（1A4 批接线），本投影=观测面。
    """
    catalog = list_constraints(_REPO)
    family = [e for e in catalog.entries if e.kind == "param_band"]
    assert len(family) == _PARAM_BAND_COUNT
    by_key = {e.key: e for e in family}
    # 键面+表达式契约（逐字段一条；`0`=正性域数学下界常量——kb 表达式
    # 原文承载，源码零抄录）
    assert all(
        e.key.startswith("param.") and e.key.endswith(".positive")
        and e.key == f"param.{e.label.split('（')[1].split('——')[0]}.positive"
        for e in family
    )
    assert all(
        e.expression == f"{e.key[len('param.'):-len('.positive')]} > 0"
        for e in family
    )
    # 抽验三键（高频 n=13 单元/中频 h2=7 单元/末位 z_water_inlet）
    assert by_key["param.n.positive"].expression == "n > 0"
    assert by_key["param.h2.positive"].expression == "h2 > 0"
    assert by_key["param.z_water_inlet.positive"].expression == "z_water_inlet > 0"
    assert by_key["param.n.positive"].unit_kinds == tuple(
        sorted(by_key["param.n.positive"].unit_kinds)
    )  # 升序（确定性）
    assert "municipal_aao" in by_key["param.n.positive"].unit_kinds
    assert by_key["param.z_water_inlet.positive"].unit_kinds == ("mine_water_input",)
    # P10 追认笔回写后收紧：全族 113 条已追认（109 存量随批回写+4 补录
    # 键生而已追认——P10 批补录注记随行）
    assert set(by_key) >= _P10_SUPPLEMENT_KEYS
    for entry in family:  # 非空选条面+WARN+flag+追认标记随行
        assert entry.unit_kinds  # 非空=节点 ID 选条（缺项跳检=稀疏语义）
        assert entry.unit_kinds == tuple(sorted(entry.unit_kinds))
        assert entry.severity == "WARN" and entry.enforcement == "flag"
        assert "已追认（Ruling 2026-10-05" in entry.source  # 追认标记在册（P10 批）
        if entry.key in _P10_SUPPLEMENT_KEYS:
            assert "P10 批补录" in entry.value_basis  # 补录键溯源注记
        assert "追认单直录起草" in entry.value_basis
        assert "_PARAMS_POSITIVE 机扫单源投影" in entry.value_basis
    assert "GB 50014-2021" in by_key["param.n.positive"].source  # 族级出处
