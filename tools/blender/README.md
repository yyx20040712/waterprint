# 模板资产工序（tools/blender——批3 主体）

辐流二沉池单族 bpy→glb→PNG 全链（spec.md §10 已签核）。资产落位
`webapp/public/assets/units/`（静态 fetch 非代码分包——§9 预算注记）。

## 工序（pipeline.sh 一键=下述五步）

| 步 | 脚本 | 产物（build/ 下，不入库） | 说明 |
|----|------|--------------------------|------|
| 1 建模 | `build_clarifier_radial.py` | `clarifier_radial.blend` | Φ40×4 四组命名+水密快检+AABB 对拍（违例中止） |
| 2 导出 | `export_glb.py` | `clarifier_radial.raw.glb` | +Y up 恒/勿 apply transforms/剔水面层/extras |
| 3 压缩 | `gltf-transform meshopt`（webapp devDep） | `clarifier_radial.meshopt.glb` | P3 签核=EXT_meshopt_compression+KHR_mesh_quantization；**勿用 `optimize`**（节点合并毁 inst 原型 TRS——实测记档） |
| 4 出图 | `render_thumb.py` | `clarifier_radial.png` | Eevee 512² 透明底/50mm 轻透视（P4）/实测 GPU 可用 |
| 5 落位 | pipeline.sh 末段 | `webapp/public/assets/units/` | glb 直拷+PNG 调色板量化（平涂渲染 256 色无损感——145KB→7KB 过 ≤80KB 预算） |

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
  细节档位表）→②风格基准提案过 glm-look 三段流→③实现（pipeline 五步）
  →④出图后三段流复审（判据=reviews/criteria-template.md；报告落
  reviews/<family>-<日期>.md）→⑤用户视觉验收必发必答。
  机器门=check_templates.mjs 断言 designReview≥built+报告在场
  （缺=CI WARN 记债；过期/谎报=FAIL）。**审查类技能弃用须用户裁定**。

## 生成物与再生成

build/ 目录全部为再生成产物（.gitignore 已排除）；入库面=脚本六件+
lib 三件+资产两枚（glb/PNG）。改模板几何/材质 → 重跑 pipeline.sh →
check_templates.mjs 水密复验 → 提交资产。
