# viewer3d —— 三维视图

厂区/单体三维渲染（React Three Fiber 类型化渲染器，懒加载路由）。

## 文件清单（M0.5 结构接线已创建规格骨架；实装期填充实现，规格见各文件头）

| 文件 | 职责 |
|------|------|
| `components/Scene.tsx` | R3F Canvas（灯光/地面/相机控制器） |
| `components/PoolBox.tsx` | 池体/渠道渲染器（按场景图 Node 生成图元） |
| `components/WaterSurface.tsx` | 水面（半透明 + shader 水流动画：UV 偏移/透明度脉动） |
| `components/Internals.tsx` | 重复构件 InstancedMesh（曝气头/填料，每类一次 draw call） |
| `components/Annotations.tsx` | 三维标注（troika SDF + Noto Sans SC 子集字体） |
| `store/viewer3dStore.ts` | 相机/剖切/显示开关 slice |
| `api/` | 场景图获取（geometry/scene JSON） |

## 规格要点

- **前端零业务几何推导**（§10.5/§16 A7）：一切尺寸来自场景图
  scene JSON（core geometry 投影产出）；渲染器只做类型化摆放；
- 独立路由 + 懒加载 chunk（与 React Flow 画布互不干扰 §12.6）；
- 剖切 clipping plane；性能预算 1080p ≥60fps（InstancedMesh 前提）；
- 3D 中文标注字体子集在构建期生成（R9）。
