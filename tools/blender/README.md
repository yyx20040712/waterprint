# 模板资产工序（tools/blender——批3 主体；段二 family 参数化；批4 第一窗六族铺开）

辐流二沉池单族 bpy→glb→PNG 全链（spec.md §10 已签核）+段二 AAO/CASS
双族并行+批4 第一窗六族（2026-09-13）。资产落位
`webapp/public/assets/units/`（静态 fetch 非代码分包——§9 预算注记）。

## 工序（pipeline.sh 一键=下述五步——`bash pipeline.sh [family ...]`）

| 步 | 脚本 | 产物（build/ 下，不入库） | 说明 |
|----|------|--------------------------|------|
| 1 建模 | `build_clarifier_radial.py` / `build_aao.py` / `build_cass.py` / 批4 六件（见族清单） | `<family>.blend` | 命名四组+水密快检+AABB 对拍（违例中止）；族名→脚本映射在 pipeline.sh `build_script()` |
| 2 导出 | `export_glb.py`（FAMILY 环境变量） | `<family>.raw.glb` | +Y up 恒/勿 apply transforms/剔水面层/extras；缺省 FAMILY=clarifier_radial |
| 3 压缩 | `gltf-transform meshopt`（webapp devDep） | `<family>.meshopt.glb` | P3 签核=EXT_meshopt_compression+KHR_mesh_quantization；**勿用 `optimize`**（节点合并毁 inst 原型 TRS——实测记档） |
| 4 出图 | `render_thumb.py`（FAMILY+ENVELOPES 取景表） | `<family>.png` | **Cycles+OptiX 1024²** 透明底/50mm 轻透视（v1.1 用户裁定四项画质升级——EV −0.85+AgX+HDRI 0.50；ENVELOPES=glb 实测外接盒[门一 W1：z 向含栏杆顶]——STYLE-BASE §二） |
| 5 落位 | pipeline.sh 末段 | `webapp/public/assets/units/` | glb 直拷+PNG 调色板量化（平涂渲染 256 色无损感——过 ≤80KB 预算） |

- 族清单：`clarifier_radial`（辐流 Φ40×4——v1.0 冻结资产，非必要不
  重跑）/`aao_corridor`（AAO 廊道 95×38×5.3——段二）/`cass_batch`
  （CASS 序批 48.5×19.5×5.5——段二）/批4 第一窗六族（2026-09-13——
  取数锚档案=.workflow/b4-window1/anchor-sizes.md）：
  `coarse_screen`（粗格栅渠 1.8×0.6×1.0）/`fine_screen`（细格栅渠
  1.9×0.8×1.0）/`grit_vortex`（旋流沉砂 5.6×3.0×3.3——厚壁圆杯
  ring_geo+真圆环栏杆[截面径向平面]）/`vfilter_cell`（V 滤单格
  10×4.5×3.9）/`parshall_flume`（巴歇尔槽 3.095×1.05×0.479——上游
  抬高制）/`eq_basin_cell`（调节池单池 53×22×5.5——CASS 制式复用）。
  初沉池 chuchenchi=registry 复用条目同辐流 glb 零新建模。

- 环境：Blender 5.0.0=`D:\blender5.0\blender.exe`（无头 `-b -P`；
  脚本内绝对路径免 PATH 依赖）；PNG 量化=系统 Python Pillow；
  gltf-transform=`npx gltf-transform`（webapp devDependency）。
- 量化重定心：meshopt+quantize 会把网格重定心到自身原点、节点 TRS
  补偿——世界位不变；扫描层锚点/inst 基座一律用**世界 AABB** 派生，
  勿读节点 translation 裸值（实测 post 节点 y=4.67≠基座 4.12）。
- 新族接入：按 build_clarifier_radial.py 同构新增 build_<family>.py +
  registry.json 加条目（**built 日期必填**）+ check_templates.mjs 自动覆盖。
- **视觉资产批五步门**（宪法 §0.1——2026-09-12 用户 Ruling「执行漂移
  系统性修复」，与代码批「调研先行+多模型双审」同构）：
  ①建模前参考调研（多模态读真实照片/图纸→部件清单入 STYLE-BASE.md
  细节档位表）→②风格基准提案过三段流评审→③实现（pipeline 五步）
  →④出图后三段流复审（判据=reviews/criteria-template.md；报告落
  reviews/<family>-<日期>.md）→⑤用户视觉验收必发必答。
  机器门=check_templates.mjs 断言 designReview≥built+报告在场
  （缺=CI WARN 记债；过期/谎报=FAIL）。**审查类技能弃用须用户裁定**。

## 审档归档清单（reviews-archive.json）

清洗批 T5（2026-09-16）将 `tools/blender/reviews/` 三段流审档移出仓库（产出面
纪律——实体在仓外档案区 `waterprint-archive/reviews-blender/`）。五步门机器面
的指针半边=`reviews-archive.json`（入库数据件）：check_templates.mjs 在仓内
报告缺位时查此清单，命中=在案（绿），未命中=FAIL。新族三段流报告若随批归档
（不再入仓），须同批在清单 `archived` 数组登记门禁名 `<family>-<date>.md`。

## 生成物与再生成

build/ 目录全部为再生成产物（.gitignore 已排除）；入库面=脚本十五件
（九 build[辐流+段二双+批4 六]+export/render/pipeline）+lib 四件
（naming/normalize/materials/rectbuild）+资产十八枚（九族 glb/PNG）。
改模板几何/材质 → 重跑 `pipeline.sh <family>` → check_templates.mjs
水密复验 → 提交资产。批4 制式沉淀（微缝终制/真圆环/恒等锚实测源——
交接 §二）随 build 脚本 docstring 在案。
