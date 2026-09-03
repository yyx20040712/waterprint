# viewer3d —— 三维视图

厂区/单体三维渲染（React Three Fiber 类型化渲染器，懒加载路由）。

> 当前状态：**FE1 段一实装完成（2026-08-28）**——数据通道
> （`api/useSceneQuery` → GET /api/scene/{project_id}，orval 生成类型）
> + 投影层纯函数（`lib/projectScene`：SCENE_VERSION 门/六 kind 完备/
> instance 摆置/语义 token/root 一致性）+ 组件薄壳
> （Canvas/PoolBox/WaterSurface/Internals/Annotations）+ view 态 store
> 就位；路由接线与 app 层组合**已完成（FE3 批 6b 段一 2026-08-29：
> `app/viewer3dPane.tsx` 懒加载挂载+URL `?project=` 参数单一真相+空态
> 项目下拉）**；**UX2 批取景自适应（2026-08-30）**：投影层返回扩
> `bounds`（全 placements 的 AABB；空场景=null——vitest 数值锚），
> Scene 机位=preset 方向向量归一化×（对角线长×1.5）+bounds 中心；
> **L5b 总装模式+漫游（2026-09-03）**：SCENE_VERSION 门步进
> `waterprint-scene-2/y-up/m`（与 core L5a 同窗）；变换门收窄——
> rotation 弧度直透传消费（度→弧度换算归 core 装配层）、scale 仍拒
> 非默认；polyline 红线归独立 `boundaries` 组（压平键 x{i}/y{i} 解码+
> 顶点计入 bounds）；SiteBoundary 闭合折线（#d4380d 沿 siteplan
> COLOR_BOUNDARY 同色先例）；OrbitControls 漫游（three 包内
> examples/jsm 零新 npm 依赖）+三 preset 并存（preset=设
> position/target 一次，用户随后自由拖拽/缩放/平移）；**挂账**：UV
> 流纹动画与 CJK 字体子集（R9）、internals 方阵网格随单元 rotation
> 的旋转矩阵化（core 加法摆放同口径）。

## 文件清单（FE1 实装；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectScene.ts` | 投影层纯函数（SceneGraph JSON→渲染描述：版本门/分组/摆置/bounds 聚合——组件唯一数据源） |
| `lib/projectScene.test.ts` | 投影层 vitest（node 环境，D4 五面：版本/kind 完备/摆置确定性/语义 token/root 一致性；UX2 bounds 数值锚+空场景；L5b rotation 放行/scale 仍拒+红线分组） |
| `components/Scene.tsx` | R3F Canvas（灯光/相机预设/剖切平面挂载+四组渲染器+图层开关+OrbitControls 漫游座） |
| `components/PoolBox.tsx` | 池体/渠道/地面渲染器（box/cylinder/plane/extrusion 四 kind；semanticColor 语义色查表；rotation 直消费） |
| `components/WaterSurface.tsx` | 水面（半透明+透明度脉动；蓝水线语义色；rotation 直消费） |
| `components/Internals.tsx` | 重复构件 InstancedMesh（投影层 placements 写矩阵+逐实例 rotation compose，每语义组一次 draw call） |
| `components/Annotations.tsx` | 三维标注（troika SDF 文本，标注位=节点位+池深直读） |
| `components/SiteBoundary.tsx` | 场地红线（L5b：闭合折线 LineLoop——#d4380d 同色先例字面平行） |
| `components/troika-three-text.d.ts` | troika 类型声明（包无 types 字段——仅消费面字段） |
| `store/viewer3dStore.ts` | 相机/剖切/显示开关 slice（zustand，纯 view 态 §12.3） |
| `api/useSceneQuery.ts` | 场景图查询（orval hooks 消费封装：projectId+可选 conditionKey） |

## 规格要点

- **前端零业务几何推导**（§10.5/§16 A7）：一切尺寸来自场景图
  scene JSON（core geometry 投影产出）；渲染器只做类型化摆放
  （唯一换算=cylinder 直径→半径的 three 接口适配）；
- **SCENE_VERSION 门**：投影层拒非 `waterprint-scene-2/y-up/m`
  （Y-up+m 单位——core scene.py R4 唯一版本读取口；L5a 步进 -2 双端
  同窗：site 摆放+rotation 放行）；
- **变换门收窄（L5b）**：rotation 弧度直透传（R3F rotation 属性直
  消费——换算归 core 装配层）；scale 仍拒非默认（R3F scale 消费面
  未开——门收窄不撤）；
- **总装红线（L5b）**：kind=polyline（semantic="site_boundary"）归
  boundaries 组独立渲染（闭合折线 #d4380d；红线顶点计入 bounds——
  总装取景覆盖红线外框）；未摆放单元 core 已不进场景图（前端零特判
  ——structures 空=回退排布 core 兜）；
- **漫游（L5b 预裁 6）**：OrbitControls（three 包内 examples/jsm——
  零新 npm 依赖）+三 preset 并存（preset 点击=设相机 position/target
  一次，用户随后自由拖拽/缩放/平移；controls 内部态不入 store）；
- **UX2 取景自适应（2026-08-30）**：投影层返回 `bounds`（全 placements
  ∪红线顶点 AABB——机位数据锚；空场景 null 显式缺省）；Scene 机位=
  preset 方向归一化×（对角线×1.5）+bounds 中心（小场景不再偏远/大
  场景不出画）；
- 独立路由 + 懒加载 chunk（与 React Flow 画布互不干扰 §12.6）；
- 剖切 clipping plane（store → THREE.Plane → 材质 clippingPlanes）；
  性能预算 1080p ≥60fps（InstancedMesh 前提）；
- 3D 中文标注字体子集在构建期生成（R9——v1 默认字体挂账）。
