# IFC 导出（M5+ 后置，条件未满足前保持空目录）

> 状态：**未启动**。依赖 IfcOpenShell（LGPL）许可评估通过（§11 R16 / §16 风险表）。

## 启动条件

1. LGPL 合规评估结论为"可行"（独立依赖分发 + 源码要约方案）；
2. M5 厂区三维总装与图纸收口完成；
3. 评估不通过则本目录删除，交付形态降级为 glTF + DXF（§11 R16 对策）。

## 未来形态（届时建包并登记 file-contracts.md）

- `ifc_export/builder.py`：SceneGraph → IfcBuildingElement 级模型
  （纯投影消费 geometry 场景图，不持有独立状态，§10.2 同规）；
- 定位是 BIM 互操作投影，非语义中枢（§10.2 路线 C）。
