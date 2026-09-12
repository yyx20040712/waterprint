# 模板归一化与变换矩阵规格（assemble spec——批3 首件）

> 状态：**冻结候选——待批3 启动会评审签核（未过签核，批3 主体件不动工）**。
> 真源链：brief（.workflow/packages/3d-visual-brief.md）→ Kimi 规划
> （reports/3d-visual-plan-kimi.md）→ 双源审查（reports/3d-visual-final-ds-review{,-v2}.md）
> → 总裁采纳清单 S1~S12（reports/3d-visual-plan-summary.md §四）→ **本件**。
> 本件与 S1~S12 冲突时以 summary §四 为准并记档呈裁。
> 机器锚：本件 §4 数值算例与 `computeTransforms.test.ts`/`deviation.test.ts`
> 冻结值**逐数一致**（规格变更=测试同步翻案，§12 纪律）。

## 0. 范围与冻结声明

- **范围**：FE 显示层三维模板（glTF 族资产）装配的归一化空间/分组变换
  矩阵/比例域降级/剖切与 stencil 条款/registry schema/资产规约——
  brief 铁律 1（core 零改：模板不是业务数据，不进 core 不参与哈希）与
  铁律 3（渲染层零业务几何推导——池体尺寸只从场景图取）全程有效；
- **本批（首件）已冻结件**：`types.ts`（词汇+缺省掩码）/
  `computeTransforms.ts`（数学核：sceneDimsToTarget/shellScale/
  groupTransform/transformDeterminant）/`deviation.ts`+两测试件；
- **批3 主体件（未动工，签核后开工）**：groupScan/instanceLayout/
  loader/registry 实装/UnitTemplateInstance/FallbackBox/fallbackLog/
  check_templates.mjs/Blender 工序（build_*脚本四库文件）。

## 1. 坐标系与轴映射表（S2-③）

| 面 | 基（右手系） | 东 | 北 | 上 | 备注 |
|---|---|---|---|---|---|
| core 场景图（存储） | z-up | +X | +Y | +Z | 米；SCENE_VERSION=waterprint-scene-6/z-up/m |
| Blender 建模（模板源） | z-up | +X（长向） | +Y（宽向） | +Z（深向） | 原点=池底中心；池底平面 z=0 |
| glTF（+Y up 恒导出） | y-up | +X | −Z | +Y | Blender 导出器 −90°绕 X |
| three 世界（projectScene 换轴后） | y-up | +X | −Z | +Y | L5R 唯一换轴点 |

- **换轴式同构**：Blender→glTF `(x,y,z)↦(x,z,−y)`；core→three
  `projectScene` 同式 `(x,z,−y)`——故模板本地系与场景系经各自换轴后
  在 three 世界**同构直配**，模板资产不经投影层换轴（总裁一表裁定；
  机器锚=computeTransforms.test.ts「轴映射跨面对拍」用例，projectScene
  实跑对拍锁定）；
- **dims 键↔模板本地轴（glTF 系）**：`length`↔x（长）、`depth`↔y
  （深/上）、`width`↔z（宽/南负向）——cylinder 族 `diameter`→L=W；
- **旋转**：core 契约 `(0,0,rz)`→three `(0,rz,0)`（绕世界竖轴，保手性
  俯视逆时针同向）；模板实例同式。单元级合成（§3）。

## 2. 统一归一化空间（S1——唯一定法）

- **全组米制建模**：模板内一切组（shell/trim/equipment/instance）的
  几何顶点与锚点均在**模板米制空间**表达（Blender 源文件即米制）；
- **shell 归一基准**：shell 组外接盒恰为 `[−L0/2, L0/2]×[−W0/2, W0/2]
  ×[0, H0]`（L0/W0/H0=registry `templateSize` 声明的**模板实际米数**，
  CI 对拍 shell 组 AABB 容差校验 §8）——归一化空间由此派生：
  `n=(x/L0, y/H0, z/W0)`（glTF 轴序）将 shell 映为 `[−0.5,0.5]²×[0,1]`；
  位置语义一致=**所有组的锚点都在同一米制空间表达、随同一壳缩放走**；
- **唯一定法=「位置缩放+截面轴逆缩放抵消」**（§3 统一公式）。原修订
  「两法择一」中的方法一（trim 截面/高度按占 shell 高度比例表达）**已
  删除**（S1 终裁：该法数学上截面随 H 等比变化——H₀=5m 模板 1.2m 栏杆
  在 H=6m 池被拉至 1.44m，违背 brief「规范定值不随池深缩放」立法本意）；
- **glb 不含运行时水面**：厂区图水面恒走场景图 `water_surface` 节点
  既有路径（WaterSurface 组件——参数水深联动 R3）；Blender 源 blend
  可含水面层仅供 PNG 缩略图出图消费（导出 glb 时剔除该层）。

## 3. 矢量约定与统一矩阵公式（S2-①）

- **列矢量约定**：顶点 `v' = M·v`（v 列矢量）；组合 `M = M_n···M_1`
  右者先作用；**缩放先作用**——`M = T(t)·diag(σ)`（缩放在最右）。
  行矢量口径禁用（Kimi §2.2 原 `T(anchor)·diag` 记法即顺序歧义病根，
  本件起以本节为准）；
- **统一公式（全组类一式）**：

  ```
  M_group = T(t)·diag(σ)，t = anchor ⊙ (s − σ)   （⊙=逐分量积）
  s  = 壳缩放（glTF 轴序）= [L/L0, H/H0, W/W0]   （shellScale 冻结件）
  ```

  语义：锚点随壳缩放走（anchor⊙s），σ 轴上的同额缩放经 −anchor⊙σ
  抵消——延伸轴上两项恒等消去（纯缩放），定值轴上锚点平移而截面恒定；
- **逐组 σ 与锚点派生**：

  | 组 | σ | anchor 派生（扫描层供值） |
  |---|---|---|
  | shell | σ=s | 任意（恒等抵消——translation 恒 [0,0,0]） |
  | trim | 延伸轴 σ_i=s_i、定值轴 σ_i=1 | **节点 AABB min**（安装面锚——常量轴锚定；竖直 y 恒定值） |
  | equipment | σ=(u,u,u)，u=actual/templateFeature（§5） | registry 语义锚：`pool_center_bottom`=模板原点（中心筒类）/`aabb_min`（端部设备类，缺省） |
  | instance | 不缩放（σ=𝟙） | 不经 groupTransform（P7 未裁 §11；位姿归 instanceLayout 批3 主体） |

- **trim 延伸掩码**：命名后缀 `__ax<轴字母集>`（Blender 轴字母规范序
  x<y<z——`axx`=仅 x 长、`axz`=x+z 水平双向…；扫描层换轴到 glTF 系
  y↔z 互换）；**缺省=水平双向 [x,z]**（池顶沿/环形走道主形态，
  `DEFAULT_TRIM_STRETCH` 冻结常量）；**竖直轴（glTF y）恒禁入延伸集**
  （S1 立法——数学核显式拒）；
- **单元级合成**：`World = T(unitPos)·R_y(rz)·M_group`（unitPos/rz=
  projectScene 摆置；同族同尺寸多池合批时实例矩阵=摆置矩阵×组矩阵，
  归并策略归批3 主体 Kimi §2.3）；
- **数值细节**：−0 归一 +0（负锚点×零差积；沿 projectScene 先例）；
  浮点断言容差 12 位（测试冻结惯例）。

## 4. 数值极端算例（S2-②——与测试冻结值逐数一致）

**算例基準**：AAO 廊道族典型 templateSize=60×12×5（L0/W0/H0，米）；
辐流二沉池圆柱族=Φ40×4（L0=W0=40, H0=4）。

**A. 栏杆 H 极端（S1/S2 核心工况）**——北缘栏杆段（延伸向 x=长；
模板 AABB x∈[−30,30]、y∈[5.0,6.2]（立柱高 1.2m 规范定值）、
z∈[−6,−5.94]；anchor=AABB min=(−30, 5.0, −6)；掩码=仅 x）：

| 目标 (L,W,H) | s（glTF 轴序） | σ | t=anchor⊙(s−σ) | 立柱底 y′（模板 5.0） | 立柱顶 y′（6.2） | 截面高 |
|---|---|---|---|---|---|---|
| 48,12,**3** | [0.8, 0.6, 1] | [0.8, 1, 1] | (0, **−2**, 0) | 3.0（=壁顶 H） | 4.2 | **1.2 恒** |
| 60,12,**6** | [1, 1.2, 1] | [1, 1, 1] | (0, **+1**, 0) | 6.0 | 7.2 | **1.2 恒** |

（对照：若按已删方法一/壳三轴缩放——H=6 时立柱高被拉至 1.44m 违例；
x 延伸向 48 目标半幅 30→24=全长 48 ✓。）

**B. 宽向锚定**——同栏杆目标 W=6（sW=0.5）：σ=[1,1,1]、t_z=−6×
(0.5−1)=+3.0；栏杆北缘 z −6→−3=新北缘（−W/2）✓ 定值轴锚点随壳缘走。

**C. 中心筒保圆（S3 数据链）**——圆柱族目标 Φ30×4：s=[0.75,1,0.75]；
中心筒模板特征 Φ3.0m、actualFactor=0.12×30=3.6m→**u=3.6/3.0=1.2**；
σ=(1.2,1.2,1.2) 三轴等模（保圆）；anchor=pool_center_bottom=(0,0,0)
→t=(0,0,0)（池心池底不动）；筒体 x∈[−1.5,1.5]→[−1.8,1.8] 居中、
底 y=0 贴底。

**D. 端部设备锚随壳**——东壁安装设备 anchor=(20,0,0)（模板壁）、
u=1.2：t_x=20×(0.75−1.2)=−9；锚点 20→1.2×20−9=**15=目标壁**（L/2）✓。

**E. 行列式（S6）**：全组类产出 det(σ)=σxσyσz>0 恒断言（数学核
防线——非正 σ 分量/负缩放显式拒）。

## 5. equipment 比例数据链（S3——封闭链）

```
templateFeature（registry：模板中该特征实际米数，如中心筒 Φ3.0）
actual（registry：actualFactor 派生系数 × 场景 dim，如 0.12×diameter）
u = actual / templateFeature        （等比缩放——保圆/保形）
```

- scene 图无特征件尺寸（只有池径/深）——**actualFactor 派生系数入
  registry 显式声明**（0.12×D 类），数据链封闭：场景 dim→actual→u→σ；
- templateFeature≤0 或 actual≤0=registry 声明病显式拒（数学核防线）。

## 6. 比例域与降级判定（deviation 冻结件）

- **两层分工**：`deviation()`=数据级降级决策（非正尺寸/出域→fallback
  结果对象，零异常——装配器走 FallbackBox+fallbackLog 登记，不静默
  不出错 brief 铁律 5）；数学核 throw=漏裁兜底防线（目标非正应先经
  deviation 裁定降级）；
- **判定口径**：逐条目闭域 `min ≤ numerator/denominator ≤ max`
  （**边界恰等 ok**）；首条出域即返（明细携 key/ratio/domain 供登记）；
  空声明表=无约束 ok；典型比（ln|actual/typical| 度量）归 registry
  建条目时以 templateSize 标定入绝对域，运行时零典型比计算；
- **非正尺寸**（H≤0 类）→nonpositive_dim（Kimi「绝对域 sanity 同路径」
  ——L>10×典型幅极端由比例域覆盖）；
- **P2 初始域草案**（呈裁签核后入 registry）：AAO 廊道 L/W∈[6,15]
  （典型 60/12）、辐流 L/H∈[4,14]（典型 40/4=10）、CASS L/W∈[3,8]
  ——典型 ±50% 标定起点，试点后按 R2（圆柱族环形 trim 非均匀残余
  失真）收紧；圆柱族域内 R 变幅收紧至 ≤2.5×（R2 对策记档）；
- **极端比例验证矩阵**（批3 验收工况，Kimi §6.4）：AAO L:W=10:1 域内
  模板+栏杆高恒定目检 / L:W=20:1 出域回退盒体+登记 / 辐流 L/H=3 与
  15 边界与出域 / CASS 双池 n-1 检修缺格徽标。

## 7. 剖切与 stencil 条款（S4/S5/S6——R1 终裁=C2VD 机制推广）

- **无 cap 组**（R1 终裁撤销）：剖口封盖走既有 C2VD stencil 机制
  （材质 clippingPlanes+双 writer+运行时剖切面大 quad）对封闭网格零
  CSG 零求交；命名规约无 cap 组位（§10）；
- **封盖材质集（S4）**：仅 **shell 组内未标 `__nc` 的水密封闭流形体**
  参与双 writer（IncrementWrap 背面/DecrementWrap 正面）；水面/单面片/
  装饰体排除（`__nc` 标记）；trim/equipment/instance 恒不入封盖材质集
  ——被剖时材质 `side: DoubleSide`+**穿帮入视觉验收口径**（kimi P1-3
  合并侧裁）；前提硬约束：**shell 封盖子件必须水密封闭**（§8 CI 校验）；
- **多实例隔离（S5 定案）**：**逐实例 cap 面片**——每池实例一枚，规格
  =该实例单元 AABB 投影至剖切面+过幅 1.1×（sectionCapQuad 先制扩
  实例化；过幅若侵入邻池区[间距<10% 壳幅]钳至间距内——共面帽盖零
  重复绘制）；奇偶计数语义在多封闭体叠加下保持（NotEqual 0 判据——
  重叠区 stencil=2 仍正确标记剖面）；**不采用**逐实例清 stencil（调度
  复杂化）/按池分 pass（drawcall 翻倍）。批3 试点验收**必含多实例
  同帧半剖工况**（相邻双池无互填+剖口封盖无破洞）；
- **负缩放禁令（S6 硬条款）**：实例矩阵 determinant>0（数学核逐产出
  断言；镜像池/对称布置禁用负缩放矩阵——绕序翻转破坏 stencil 计数）。

## 8. 水密性 CI 校验规格（S7——check_templates.mjs 实现依据）

校验对象：registry `status:ready` 族的 glb，shell 组未标 `__nc` 子件，
**逐 primitive**：

1. **位置焊接**：glTF 硬边/法线/UV 拆分产生同位重复顶点——先按位置
   焊接（容差 ε，见容差条款）再入拓扑计数，禁直接按索引边配对；
2. **边入射计数**：焊接后无向边恰关联 2 三角形面（边界边=1→开口；
   >2→非流形）——任一非零即 error；
3. **绕序一致性**：逐连通分量有符号体积 `V=Σ(v0·(v1×v2))/6` 同号
   （全正或全负；混合号=绕序翻转——法向不一致，stencil 计数前提破坏）；
4. **组级汇总**：shell 封盖子件逐件通过才算族通过；trim/equipment/
   instance 不校验（天然非水密，§7 口径）。

**容差 vs meshopt 量化（S12/ds-P2-2）**：校验在 MeshoptDecoder 解码
后网格上做；量化（POS 14bit 默认档）顶点偏移≈外接盒幅×2⁻¹⁴——焊接
容差起点 ε=壳外接盒最大幅×2⁻¹³（量化步长 2 倍），批3 首族实测重标定
后冻结入 CI 常量；归一化 AABB 对拍容差（shell 外接盒=templateSize）
同口径重标定。**该实现 ~2–3 人日入批3 预算**（总裁已裁）。

## 9. registry schema v1 草案（S12——冻结前验证）

```ts
type FamilyEntry = {
  family: string;                      // 如 "clarifier_radial"
  glb: string; thumb: string;          // 资产路径（manifest 版本戳拼接）
  dimSource: DimSource;                // 场景 dims→L/W/H 映射（族缺省）
  templateSize: TemplateSize;          // 壳 AABB 米数（§8 CI 对拍）
  ratioDomain: RatioDomainEntry[];     // §6 闭域声明（P2 签核值）
  equipment: Record<string, {          // part 名→特征规格（§5）
    templateFeature: number;
    actualFactor: number;              // ×场景 dim 派生 actual
    anchor?: "pool_center_bottom" | "aabb_min";  // 缺省 aabb_min
  }>;
  instanceSpacing: Record<string, number | null>; // P5 呈裁常量表
  badges: { poolCount: boolean; maintenanceNA: boolean };
  status: "ready" | "pending";         // pending=缺资产合法降级
  kindAliases?: Record<string, {       // S12：多对一（污泥族 6 kind→1 glb）
    dimSource?: DimSource;             // 分条目覆盖——kind 级 dimSource
    ratioDomain?: RatioDomainEntry[];  // 分条目覆盖——kind 级比例域
  }>;
};
```

- **S12 验证条款**：schema v1 冻结前以污泥族样例条目验证 kindAliases
  分条目表达能力（6 kind 共 1 glb、各 kind 独立 dimSource/ratioDomain）
  ——批4 铺开前置；
- 体积预算/懒加载/chunk 纪律沿 Kimi §1.5（真源不复述：glb ≤150KB/
  PNG ≤80KB/全族 ≤2MB；public/assets 静态 fetch 非代码分包）。

## 10. 命名与资产规约（R1 终裁+S4 增补）

```
<family>__<group>__<part>[__ax<掩码>][__nc]
组 group ∈ { shell, trim, equip, inst }        （扫描层 equip→equipment/
                                               inst→instance 归一）
例：aao__shell__wall   aao__trim__walkway__axxz   clarifier__equip__center_well
    clarifier__inst__rail_post   aao__shell__decor_strip__nc（装饰件不入封盖集）
```

- 分组以 Empty 父级承载（glTF 保留节点层级）；`__ax` 掩码与 `__nc`
  同时写入 custom props（glTF extras 双保险）；
- **无 cap 组**（§7）；**shell 水密封闭硬约束**（CI §8）；
- Blender 侧：原点=池底中心（§1）；**导出勿 apply all transforms**
  （组节点 TRS 装配器要用，仅 apply 到组叶节点几何）；+Y up 恒；
  glb 剔除水面层（§2）；无位图贴图（PBR 常量——体积预算前提）；
  单族 ≤8k tri（CI 卡）。

## 11. 横切条款与挂账（S8~S11 呈裁/记档）

- **S8/P7（instance_count 推导分支）**：spec 立场=**数量唯一真源=场景图
  `instance_count`**（core scene.py R3 口径）；「缺省由布置域÷间距常量
  推导」分支**未裁前禁用**（渲染层几何推导嫌疑，铁律 3 边界）——批3
  启动会裁：禁推导分支（推荐）or 定义其为显示层样式派生；
- **S9（缩略图降级链）**：PNG 失败→C2-thumb 实时后备的降级队列**并发
  上限 ≤2**（19 单元同 404 时不并发 19 离屏 R3F——350ms 预算/主视图
  GPU 争用防线）；超限直落 UnitGlyph 占位；probe 增降级计数（PNG 404
  率/切后备频次可观测——window.__probe.thumbnailFallbacks）；
- **S10（批5 预算分档）**：半剖双 writer≈shell 两遍+cap 填充率——批5
  预算分**无剖/半剖两档**，probe 阈值批5 启动前重标定（本批记档不实装）；
- **S11（检修缺位→占位）**：纯函数契约冻结——
  `missingSlotPlaceholders(nPools, nActive, spacing) → {index, position}[]`
  （缺位索引与占位坐标——渲染层警示占位[半透明轮廓/虚线框]+徽标消费）；
  **13 kind 覆盖核对清单批3 验收前出**。摸底实录（2026-09-12）：场景图
  现状=单元单包络发射（pools.py pool_primitives 单体一节点），R4 文档
  承诺的 n_active 分池排布+缺位标注**未在场景图实现**；缺位数据源候选
  =params/结果面（FE 零 core 改可达——推荐）vs 场景图扩展（违铁律 1
  排除）——与 P7 同窗呈裁；
- **P2~P6 呈裁预研**（ds-P2-3 启动会前到可签核）：P2 初始域=§6 草案表；
  P3 压缩=**meshopt**（推荐：解码器小/纯 JS/无 wasm 分发负担；Draco
  备选）；P4 缩略图相机=轻透视 50mm 等效（贴近厂区图首视角）；P5 间距
  常量草案=栏杆立柱 1.5m/曝气头 0.8m 网格（显示层常量——数值签核）；
  P6 污泥族合并=**推荐采纳**（§9 kindAliases 已按合并形设计）。

## 12. 冻结面·变更纪律

- **本批冻结件**（S1~S12 的机器锚载体）：`assemble/types.ts`/
  `computeTransforms.ts`/`deviation.ts`+`computeTransforms.test.ts`/
  `deviation.test.ts`（vitest 27 例）——数值算例 §4 与测试冻结值逐数
  一致是**双向锁**：改规格必同步翻案测试、改测试必记档规格变更动机；
- **规格沉默处默认答案**：engineering-conventions GR 族+viewer3d README
  规格要点（语义色查表/InstancedMesh/预算口径）；新歧义先入
  undefined-features-register 禁就地自创语义；
- 本件 ≤500 行（file budgets 门禁）；修订沿台账记档+批3 启动会追认制。
