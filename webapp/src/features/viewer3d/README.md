# viewer3d —— 三维视图

厂区/单体三维渲染（React Three Fiber 类型化渲染器，懒加载路由）。

> 当前状态：**FE1 段一实装完成（2026-08-28）**——数据通道
> （`api/useSceneQuery` → GET /api/scene/{project_id}，orval 生成类型）
> + 投影层纯函数（`lib/projectScene`：SCENE_VERSION 门/五 kind 完备/
> instance 摆置/语义 token/root 一致性，vitest 11 用例）+ 组件薄壳
> （Canvas/PoolBox/WaterSurface/Internals/Annotations）+ view 态 store
> 就位；**挂账**：路由接线与 app 层组合（后续批）、UV 流纹动画与
> CJK 字体子集（R9）、相机控制器（OrbitControls 归升版统筹 FE2）。

## 文件清单（FE1 实装；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectScene.ts` | 投影层纯函数（SceneGraph JSON→渲染描述：版本门/分组/摆置——组件唯一数据源） |
| `lib/projectScene.test.ts` | 投影层 vitest（node 环境，D4 五面：版本/kind 完备/摆置确定性/语义 token/root 一致性） |
| `components/Scene.tsx` | R3F Canvas（灯光/相机预设/剖切平面挂载+三组渲染器+图层开关） |
| `components/PoolBox.tsx` | 池体/渠道/地面渲染器（box/cylinder/plane/extrusion 四 kind；semanticColor 语义色查表） |
| `components/WaterSurface.tsx` | 水面（半透明+透明度脉动；蓝水线语义色） |
| `components/Internals.tsx` | 重复构件 InstancedMesh（投影层 placements 写矩阵，每语义组一次 draw call） |
| `components/Annotations.tsx` | 三维标注（troika SDF 文本，标注位=节点位+池深直读） |
| `components/troika-three-text.d.ts` | troika 类型声明（包无 types 字段——仅消费面字段） |
| `store/viewer3dStore.ts` | 相机/剖切/显示开关 slice（zustand，纯 view 态 §12.3） |
| `api/useSceneQuery.ts` | 场景图查询（orval hooks 消费封装：projectId+可选 conditionKey） |

## 规格要点

- **前端零业务几何推导**（§10.5/§16 A7）：一切尺寸来自场景图
  scene JSON（core geometry 投影产出）；渲染器只做类型化摆放
  （唯一换算=cylinder 直径→半径的 three 接口适配）；
- **SCENE_VERSION 门**：投影层拒非 `waterprint-scene-1/y-up/m`
  （Y-up+m 单位——core scene.py R4 唯一版本读取口）；
- 独立路由 + 懒加载 chunk（与 React Flow 画布互不干扰 §12.6）；
- 剖切 clipping plane（store → THREE.Plane → 材质 clippingPlanes）；
  性能预算 1080p ≥60fps（InstancedMesh 前提）；
- 3D 中文标注字体子集在构建期生成（R9——v1 默认字体挂账）。
