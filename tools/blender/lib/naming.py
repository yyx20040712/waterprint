"""模板命名规约（assemble/spec.md §10——R1 终裁+S4 增补）。

输入:  family/group/part (+可选掩码与 __nc 旗标)
输出:  build_name（组装）/parse_name（解析）/apply_extras（custom props
        双保险——glTF extras 经 export_extras=True 落地）

规格说明（spec §10；组词表 shell|trim|equip|inst，扫描层 equip→
  equipment/inst→instance 归一；无 cap 组）：
  - 语法：``<family>__<group>__<part>[__ax<掩码>][__nc]``；
  - 掩码轴字母=**Blender 轴字母**规范序 x<y<z（x=长、y=宽、z=深/上）；
    扫描层换轴到 glTF 系 y↔z 互换（Blender y=宽↔glTF z=宽；Blender
    z=上↔glTF y=上）；缺省掩码=水平双向（Blender x+y / glTF x+z）；
  - 竖直轴（Blender z / glTF y）恒禁入 trim 延伸集（S1——数学核显式拒）；
  - ``__nc`` =不水密件（水面/单面片/装饰——封盖材质集排除标记）。
"""

from __future__ import annotations

GROUPS = ("shell", "trim", "equip", "inst")
GROUP_ALIASES = {"equip": "equipment", "inst": "instance"}

# Blender 轴字母 → glTF 轴槽位（spec §1/§3：Blender y=宽→glTF z=宽、
# Blender z=上→glTF y=上——y↔z 互换）。键序即掩码字符合法域。
BLENDER_AXIS_ORDER = "xyz"


class NamingError(ValueError):
    """命名违例（语法/组词表/掩码轴域外——模板源数据病显式拒）。"""


def build_name(
    family: str,
    group: str,
    part: str,
    mask: str | None = None,
    nc: bool = False,
) -> str:
    if group not in GROUPS:
        raise NamingError(f"组词表外：{group!r}（合法 {GROUPS}）")
    if not family or "__" in family or not part or "__" in part:
        raise NamingError(f"family/part 空或含分隔符：{family!r}/{part!r}")
    name = f"{family}__{group}__{part}"
    if mask is not None:
        validate_mask(mask)
        name += f"__ax{mask}"
    if nc:
        name += "__nc"
    return name


def validate_mask(mask: str) -> None:
    """掩码合法性：非空、轴字母升序、无重复、竖直轴（Blender z）恒禁。"""
    if not mask or sorted(mask) != list(mask) or len(set(mask)) != len(mask):
        raise NamingError(f"掩码非法：{mask!r}（须非空且按 x<y<z 升序无重复）")
    for ch in mask:
        if ch not in BLENDER_AXIS_ORDER:
            raise NamingError(f"掩码轴字母域外：{ch!r}（合法 {BLENDER_AXIS_ORDER}）")
    if "z" in mask:
        # Blender z=竖直（S1：trim 竖直轴恒定值——规范定件不随池深缩放）
        raise NamingError(f"掩码含竖直轴 z：{mask!r}——S1 立法违例")


def parse_name(name: str) -> dict[str, object]:
    """解析四段名 → {family/group/part/mask/nc}；违例抛 NamingError。"""
    segments = name.split("__")
    if len(segments) < 3:
        raise NamingError(f"段数不足：{name!r}（须 ≥3 段 <family>__<group>__<part>）")
    family = segments[0]
    group = segments[1]
    if group not in GROUPS:
        raise NamingError(f"组词表外：{group!r} in {name!r}")
    part = segments[2]
    if part == "":
        raise NamingError(f"part 空：{name!r}")
    mask: str | None = None
    nc = False
    for tail in segments[3:]:
        if tail.startswith("ax") and len(tail) > 2:
            if mask is not None:
                raise NamingError(f"重复掩码段：{name!r}")
            mask = tail[2:]
            validate_mask(mask)
        elif tail == "nc":
            nc = True
        else:
            raise NamingError(f"尾段非法：{tail!r} in {name!r}（合法 __ax…/__nc）")
    return {"family": family, "group": group, "part": part, "mask": mask, "nc": nc}


def blender_mask_to_gltf(mask: str) -> tuple[bool, bool, bool]:
    """Blender 轴字母掩码 → glTF 轴槽位 [x,y,z]（y↔z 互换——扫描层同式）。

    Blender x(长)→glTF x；Blender y(宽)→glTF z；Blender z(上)→glTF y。
    """
    return ("x" in mask, "z" in mask, "y" in mask)


def apply_extras(obj: object, mask: str | None, nc: bool) -> None:
    """custom props 双保险（§10：``__ax``/``__nc`` 同步写入 extras 位）。"""
    if mask is not None:
        obj["__ax"] = mask  # type: ignore[index]
    if nc:
        obj["__nc"] = True  # type: ignore[index]
