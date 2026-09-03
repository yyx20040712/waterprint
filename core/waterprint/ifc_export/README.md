# IFC 导出（L5c 原型已启动 2026-09-03）

> 状态：**原型实装**（L5c 批）。依赖 IfcOpenShell（LGPL）许可评估通过
> （§11 R16 / §16 风险表）。

## 启动条件（全部已满足）

1. LGPL 合规评估结论为"可行"（独立依赖分发 + 源码要约方案）
   ——**已满足**（评估报告 2026-09-02：结论=有条件启动，条件 C1~C6；
   报告位于仓库外工作流目录 `../../.workflow/reports/m5-ifc-lgpl-evaluation.md`，
   相对路径以本文件为基；C1~C2 已随 L5c 实装落地——C1=uv 标准 pip 依赖
   `ifcopenshell>=0.8.5`（uv.lock 锁定，禁冻结/嵌入）；C2=import 白名单
   ifcopenshell 本体+waterprint.geometry/contracts（file-contracts.md
   登记+importlinter 四契约机器拦截）；C3 随附物于开源发布时点执行）；
2. M5 厂区三维总装与图纸收口完成——**L5a core 场景图 site 级已落**
   （本批），导出原型以 SceneGraph 为唯一输入先行（总装收口推进中）；
3. 评估不通过则本目录删除，交付形态降级为 glTF + DXF（§11 R16 对策）
   ——未触发。

## C6 版本口径核正（2026-09-03，L5c DoD）

评估报告 C6 原句「uv 锁 3.13」与仓库实况有偏差，核正为：
`.python-version`=**3.14**（仓库根入库文件）；CI 矩阵 3.12+3.13
（ci.yml），本地 core venv 实跑 3.13；ifcopenshell 0.8.5 覆盖
cp310~cp314 全线轮子——三口径均可装可跑，无阻塞。

## 现行形态（已登记 file-contracts.md + structure-graph.md §1a/§1b）

- `ifc_export/builder.py`：`build_ifc(scene_graph)` + `write_ifc(model, path)`
  ——SceneGraph → IFC4 最小集（IfcProject/Site/Building 骨架 +
  OwnerHistory/Units(SI)/GeometricContext + IfcExtrudedAreaSolid
  [box/cylinder] + IfcLocalPlacement 链 + IfcRelAggregates）；
  构筑物=**IfcBuildingElementProxy** 中性形态（原型级，禁 IfcWall 等
  建筑语义）；水面/内部构件/渠道/红线不含；确定性=uuid5 GlobalId +
  时间戳固定值定槽（双跑 bytes 恒等，镜像测试锁定）；
- 定位是 BIM 互操作投影，非语义中枢（§10.2 路线 C）——纯投影消费
  geometry 场景图，不持有独立状态；
- 挂账：export_artifact kind 注册与 server 下载端点（二期——该面
  无 design.site 通道）；IFC2X3/IFC4X3 档与更多实体族（按需）。
