# siteplan —— 厂区布置编辑器

design.site 厂区布置编辑（原生 SVG 自绘零新依赖：待摆区拖放/拖拽移动/旋转
把手/道路·管线走廊折线绘制/测距标注/PUT 保存，M3 布置编辑器 MVP 批）。

> 当前状态：**M3 实装完成（2026-09-03，L2a+L2b 两笔切片）**——L2a 纯函数
> 层+store（窄化门/足迹投影 dims 键镜像 PoolBox 消费面/PUT 结构化替换/
> 吸附/测距+zustand node 直测首例——FE6 口径收口，vitest +31 用例）；
> L2b 组件集成层（SiteplanPane/SiteCanvas/PendingPanel+useSiteData 薄封装
> +app/siteplanPane 薄壳+AppRoute 六值扩七值 siteplan=canvas 后第二位；
> 门禁 10 绿全量通过）。挂账：坐标网视口自适应、走廊 kind 开放输入——
> 归 L4 批统筹；roads/corridors 删除编辑=B4 笔②销账（侧栏 Popconfirm
> 确认门+画布 Delete 键两路同门——仓内无 undo 删除须确认）；红线逐点
> 编辑=B4 笔③销账（顶点把手拖拽/双击增删点+删至 3 拒删提示+红线删除汇
> 清空通路收口）。

## 文件清单（M3 实装；规格见各文件头契约块）

| 文件 | 职责 |
|------|------|
| `lib/projectSite.ts` | 纯函数层：site 窄化（D6 轻门）/scene 足迹投影（children+instance 聚合包围盒）/projectSiteSafe 投影围栏（B4 笔③——{model,error} 错误捕获归 lib，组件 useMemo 零 try/catch）/withSite PUT 载荷/网点·旋转吸附/removeLineAt 折线 immutable splice 删除（B4 笔②——越界原引用直通）（SPC2 笔④几何原语迁 siteGeometry 顶格减压） |
| `lib/projectSite.test.ts` | 纯函数层 vitest（node 环境：窄化逐类拒带定位/缺省默认/footprint 键镜像数值例/withSite 深层引用相等/snap·rotation 档位表/removeLineAt 删项·越界直通[B4 笔②]/projectSiteSafe 围栏三分支[B4 笔③——合法透传/SEP 原实例/非 SEP 归一包装]；measure 用例 B4 笔②迁 siteGeometry.test.ts 源件镜像归位——行预算门禁拆文件） |
| `lib/siteGeometry.ts` | 纯几何原语层（SPC2 笔④自 projectSite 拆出）：OBB 四角/点-边枚举精确净距（core spacing 同式镜像）/点-线段距/线段相交/点在多边形（射线法+贴边 1e-9 归内——越界可视化判定面）/measureToNearest OBB 测距 |
| `lib/siteGeometry.test.ts` | 纯几何原语 vitest（node 环境：黄金角 0/30/45/90° 解析值容差 1e-9[跨语言 IEEE754 镜像口径]/归零族[相交·全含]/零长退化/凹多边形·顶点序无关·贴边归内/测距排序+多目标矩形对数值例+90° 真形净距[B4 笔②自 projectSite.test.ts 迁入去重]） |
| `lib/siteDraftDiff.ts` | 深比较纯函数（sameSite 键序无关——draft dirty 派生真源；SC1 D9④ 自 SiteplanPane 私有迁 lib） |
| `lib/siteDraftDiff.test.ts` | 深比较 vitest（三例：[]vs[] 同/[]vs 非[]异/键序无关深比较同） |
| `lib/canvasDisplay.ts` | 画布显示层常量与纯显示函数（B3 R7 自 SiteCanvas 模块级外搬：PX_PER_M/UNCALC_SIZE/坐标网窗/把手/双击窗/测距数/滚轮灵敏度/灰阶三色/BOUNDARY_* 常量族+DragSession/DoubleTapAnchor/MeasurePair 交互类型+pointsAttr/isSelectedLine 纯函数；B4 笔②增键盘删除判定段 svgOwnsKeyTarget/lineDeleteTarget——结构化类型零 DOM 可测；B4 笔③增红线选中加粗/顶点把手半径常量+TapAnchor/isDoubleTapAt 通用双击判定） |
| `lib/canvasDisplay.test.ts` | 键盘删除判定 vitest（B4 笔② node 直测先红后绿：svg 本体/直接子元素消费面/输入框不消费/Delete·Backspace 双键/road·corridor 目标产出/structure·无选中·他键 null；B4 笔③增 boundary 选中删除目标产出例） |
| `lib/vertexEditing.ts` | 红线逐点编辑纯函数面（B4 笔③ R1+R5——仓内首顶点级编辑面）：顶点命中/线段投影（含闭合 wrap 段）/最近段路由/增删移点 immutable copy-on-write+snapVertexPoint 吸附归本层（Pane 收净值）；BOUNDARY_MIN_VERTICES 删至 3 拒删返 null（core ≥3 门镜像） |
| `lib/vertexEditing.test.ts` | 顶点编辑纯函数 vitest（node 环境先红后绿：命中内外·最近优先·半径防御/投影 clamp·零长·wrap 段/最近段路由/插入索引位·wrap 尾插·非法直通/删至 3 拒删 null+不变性/移点 immutable/双轴吸附/sameSite 拒删不翻 dirty+增点翻 dirty） |
| `components/LineSidebar.tsx` | 选中折线删除侧栏纯展示子件（B4 笔② R2——ENG6 先例第三例：danger 按钮+受控 Popconfirm 确认门，侧栏按钮与画布 Delete 键汇父层 removeRequest 同一挂起态；取消/外点=零动作；B4 笔③泛化 RemovableSelection 面——boundary 分支=清空通路文案族） |
| `components/BoundaryLayer.tsx` | 红线层子件（B4 笔③ R1——自 SiteCanvas polygon 段子件化）：选中态加粗描边+顶点把手（r=1.0 世界单位·随 zoom）pointerdown 拖拽会话+双击顶点删点/双击线段增点（TapAnchor 通用双击判定，顶点优先歧义序）；描边可命中 fill=none（非 select 工具=装饰态） |
| `lib/windRoseGeometry.ts` | 风玫瑰纯计算面（B4 笔① R3）：WIND_DIRS 八方位罗盘序+windRoseSpokes 辐条/标注点相对向量——数据计算镜像 core site_plan.py:288-323（未知键跳过/负钳 0/None·空·全零=空数组/sorted 序）；Y 翻转内置（dy 负=屏幕向上），落位语义归 WindRose |
| `lib/windRoseGeometry.test.ts` | 风玫瑰纯计算 vitest（node 环境先红后绿：八方位序/None·空·全零=空/未知键跳过+sorted/比例缩径/负钳 0/标注点满径未缩放/N 朝上 dy<0/半径防御） |
| `lib/windRoseForm.ts` | 风玫瑰值表单纯逻辑面（B5 D5）：mergeWindRose 合并写回——未知键（WIND_DIRS 外）原样保留+八方位非空非负有限值覆盖；全空+有未知键→仅未知键、全空+无未知键→null（全量丢弃唯组件「清空」确认门）；WIND_DIRS 单源 import 自 windRoseGeometry |
| `lib/windRoseForm.test.ts` | 风玫瑰表单纯逻辑 vitest（B5 D5 node 先红后绿四例：全空无未知键→null[含原对象已知方位不隐式携带]/全空有未知键→仅未知键保留/负值·NaN·Infinity 过滤/部分值+未知键合并不丢） |
| `components/WindRose.tsx` | 风玫瑰画布角标（B4 笔① R3 仅渲染）：嵌套 svg x="100%" 锚右缘屏幕空间 overlay——零测量零视口态；pointerEvents=none 装饰面；None=返回 null；B5 D6 数据源改吃 draft.options.wind_rose（值编辑即时联动——面板 B5 销账） |
| `components/WindRose.test.tsx` | 角标组件冒烟（零 jsdom 红线内 node 直调元素树断言本 feature 首例：None/空/全零=null、有值=辐条+sorted 标注、N 朝上+标注未缩放满径） |
| `components/WindRosePanel.tsx` | 风玫瑰值编辑面板（B5 D5——右侧栏常驻[无选中时显示区]）：四行两列八方位 InputNumber[min=0 禁负]+相对频率口径提示语+清空 Popconfirm 确认门→onClear 上行 null；受控零本地态，onChange 上行 mergeWindRose 合并写回值；antd 薄壳不测（纯逻辑归 windRoseForm） |
| `store/siteplanStore.ts` | 视图 slice（zustand 纯 view 态：pan/zoom 夹紧/snap·grid 开关/选中[structure id/road·corridor 索引/B4 笔③ boundary 单例无 id]/工具+折线点序列机——业务数据零入 store） |
| `store/siteplanStore.test.ts` | store node 直测首例（初始态/各 action 纯转移/zoom 夹紧/tool 切换清折线/pending 序列机；B4 笔③增 boundary 选中面置清例） |
| `components/SiteplanPane.tsx` | 切片内组装（工具栏+待摆区+画布+选中侧栏[结构/折线/红线]+保存流——canvasPane 壳同构；B4 笔②增折线删除 removeRequest 确认门挂起态与 onRemoveLine/onRemoveRequest 回调；B4 笔③增顶点三回调 copy-on-write+拒删 useMessage 提示+红线删除 boundary 分支汇 clearBoundary 清空通路+setSelection(null) 收口；B4 笔③行预算拆法——收笔面板抽 LineFinishForm[ENG6 第四拆]+投影围栏 try/catch 归 lib projectSiteSafe；B5 D5 增 setWindRose 回调+WindRosePanel 无选中常驻挂载[+5 行内]） |
| `components/LineFinishForm.tsx` | 折线收笔参数面板子件（B4 笔③行预算拆法——ENG6 先例第四例：宽度/kind 会话态自持，条件渲染重挂载=缺省重置；落笔/丢弃上行 draft 落位归 SiteplanPane） |
| `components/SiteplanToolbar.tsx` | 工具栏纯展示子件（工具组/吸附/坐标网/复位/清空红线 Popconfirm 确认门/折线参数/保存——ENG6 自 SiteplanPane 拆出，态与回调全经 props） |
| `components/StructureSidebar.tsx` | 选中结构侧栏纯展示子件（B3 R7 自 SiteplanPane 侧栏块抽离——ENG6 工具栏先例第二例：标高编辑/间距校核分组/红线越界分组/移出按钮/操作提示，行数据 SiteplanPane 预聚合并经 props 单向穿隧） |
| `components/SiteCanvas.tsx` | SVG 画布薄壳（渲染+pointer 交互——几何全经 lib，组件零推导；B4 笔①挂 WindRose 屏幕角标/B4 笔② Delete 键 onRemoveRequest 上行/B4 笔③ boundary polygon 段子件化挂 BoundaryLayer+顶点三回调穿隧；B5 D6 WindRose 角标单行改源吃 draft.options.wind_rose[值编辑即时联动——draft prop 已在零新 props]） |
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
- **L4 面沿承现状**：边界红线（L4a 绘制/清空）与间距校核黄/红标示
  （L4b+SPC2）已实装；风玫瑰角标=B4 笔① 实装**仅渲染**（屏幕空间右上角
  overlay——数据计算镜像 core site_plan.py:288-323+Y 翻转内置），**风玫瑰
  值编辑面板挂账续记**（golden 全 wind_rose:null+零 UI 写值现状下渲染先行
  独立验收——简报 R3/DS 新发现②记档）；SVG=原生 JSX（DxfSvg 先例零运行期库），交互=pointer 事件
  自实现；本 feature 零 import 其他 feature（§13.5 分层门禁）。
