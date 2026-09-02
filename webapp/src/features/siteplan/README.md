# siteplan —— 厂区布置编辑器

design.site 厂区布置编辑（原生 SVG 自绘零新依赖：待摆区拖放/拖拽移动/旋转
把手/道路·管线走廊折线绘制/测距标注/PUT 保存，M3 布置编辑器 MVP 批）。

> 当前状态：**M3 实装完成（2026-09-03，L2a+L2b 两笔切片）**——L2a 纯函数
> 层+store（窄化门/足迹投影 dims 键镜像 PoolBox 消费面/PUT 结构化替换/
> 吸附/测距+zustand node 直测首例——FE6 口径收口，vitest +31 用例）；
> L2b 组件集成层（SiteplanPane/SiteCanvas/PendingPanel+useSiteData 薄封装
> +app/siteplanPane 薄壳+AppRoute 六值扩七值 siteplan=canvas 后第二位；
> 门禁 10 绿全量通过）。挂账：坐标网视口自适应、走廊 kind 开放输入、
> roads/corridors 删除编辑——归 L4 批统筹。

## 文件清单（M3 实装；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectSite.ts` | 纯函数层：site 窄化（D6 轻门）/scene 足迹投影（children+instance 聚合包围盒）/withSite PUT 载荷/网点·旋转吸附/测距（组件唯一几何源） |
| `lib/projectSite.test.ts` | 纯函数层 vitest（node 环境：窄化逐类拒带定位/缺省默认/footprint 键镜像数值例/withSite 深层引用相等/snap·rotation·measure 档位表） |
| `store/siteplanStore.ts` | 视图 slice（zustand 纯 view 态：pan/zoom 夹紧/snap·grid 开关/选中/工具+折线点序列机——业务数据零入 store） |
| `store/siteplanStore.test.ts` | store node 直测首例（初始态/各 action 纯转移/zoom 夹紧/tool 切换清折线/pending 序列机） |
| `components/SiteplanPane.tsx` | 切片内组装（工具栏+待摆区+画布+选中侧栏+保存流——canvasPane 壳同构） |
| `components/SiteCanvas.tsx` | SVG 画布薄壳（渲染+pointer 交互——几何全经 lib，组件零推导） |
| `components/PendingPanel.tsx` | 待摆区（design.nodes 有而 site 无的单元——拖入画布即摆放） |
| `api/useSiteData.ts` | 数据通道薄封装（useReadProject+scene 查询直用——零新端点） |

## 规格要点

- **轮廓数据源=既有 GET /api/scene/{project_id}**（openapi 恒红线：零新
  端点）：足迹（footprint w/h）投影自 scene 节点 primitive——dims 键解释
  镜像 viewer3d 渲染器消费面（`PoolBox.tsx` boxGeometry：box/plane/
  extrusion 用同一对 length×width 键、cylinder 用 diameter 键；镜像=同源
  所见即所得非业务复制）；scene 不可得（无已完成计算/查询失败）→固定
  示意矩形+「未计算」角标——仅显示层，**placement 只存 {x,y,rotation,
  ground_elevation}，示意尺寸永不落盘**（R3 红线）；
- **保存=既有 PUT 结构化替换**：`withSite(raw, site)` 仅替换 design.site
  其余原样回传（withConstraintChoices 同构禁散拼）；onSuccess invalidate
  `/api/projects/{id}` 读键；409 锁/WaterprintApiError 按 AssumptionsPanel
  先例呈现（不 force 不重试）；
- **D6 轻形状门**（projectFlow 同构）：structures/roads/corridors/options
  逐类逐键形状拒（键/索引定位）；未知键透传不拒——server strict 面是唯一
  语义门（TS 零业务复制红线）；缺 site 键=全默认态；
- **测距=编辑辅助非校核裁判**：选中构筑物至多 3 个最近构筑物的中心距+
  净距（轴对齐矩形投影边到边距离）——不引阈值不判合规（防火间距校核=
  L4 批 server 裁判）；
- **吸附口径**：坐标网间距=design.site.options.coord_grid（默认 10.0m）；
  吸附开关=store view 态（默认开）；旋转把手=90° 吸附（默认）、Shift=
  自由角（1° 舍入）；
- **L4 面不在本批**：间距校核黄/红标示/风玫瑰角标/边界红线——零实现
  零占位；SVG=原生 JSX（DxfSvg 先例零运行期库），交互=pointer 事件
  自实现；本 feature 零 import 其他 feature（§13.5 分层门禁）。
