/**
 * 应用壳：布局骨架+标签路由状态机+Providers 组合（app 层组合面）。
 *
 * 输入: 各 feature 切片与 app 层装配件（app 层是唯一允许组合 features 的
 *        层）+URL ?tab=/（UX1 D2 初值三级解析）?task=（深链意图判据）
 * 输出: 应用布局（§19.2 骨架：顶栏/左侧单元库（M2 实装=UnitLibrary）/
 *       中央标签工作区）——
 *       Providers 包裹（ConfigProvider 深色+QueryClient）+Tabs activeKey
 *       状态机（onChange 经 replaceState 写 ?tab=——路由态 URL 持久化）
 *
 * 规格说明（FE3 批 6b 段一，D1/D8 实装；FE6 批 6b 段四 D1 扩六值标签；
 *   FE8 批 6b 段六 cost 标签实装替换占位屏；FE9 批 6b 段七 drawings
 *   标签实装替换占位屏——六标签全实装，占位屏组件退役删除；UX1 批
 *   6b 段八 D2 增 ?tab= 路由态进 URL；R2-A 批 2 增 token 运行期面；
 *   M3 批 2026-09-03 D2 扩七值：siteplan=厂区布置，插 canvas 后第二位；
 *   C1 批 2026-09-10 主题骨架批：滚动容器重构+顶栏品牌区+状态栏）：
 *   - 路由机制定 D1=AntD Tabs 状态机：activeKey 用 useState（默认 canvas；
 *     路由名与次序=router.tsx AppRoute 冻结面七值 canvas/siteplan/
 *     solutions/viewer3d/elevation/drawings/cost——solutions 插 canvas 后=
 *     设计→看方案用户流程，siteplan 插第二位=设计→布置就近（M3 D2）；
 *     elevation/drawings/cost 次序沿 FE3 五值面——R9 勘误
 *     回旧），Tabs activeKey/onChange 驱动——不引入 react-router
 *     （零新依赖纪律；FE3 D1 已定夺机制=状态机——勘误：原注引「router.tsx
 *     头『M2 定型』」该字样现不存在，router 头注实况见其文件）；
 *   - UX1 D2/S4 路由态进 URL：activeKey 初值三级解析——?tab= 合法值
 *     （parseTabParam ROUTES 成员校验）→用之；无 ?tab= 但有 ?task=→
 *     "solutions"（深链意图——?task= 面板在 solutions 标签，直开可见；
 *     I-4 保守预裁维持单参不受扰，仅初值落点不跳转）；缺省 canvas；
 *     onChange 经 withTabParam replaceState 写 ?tab=（他键原序保留）
 *     ——刷新/分享后落点保持；非法 ?tab= 值归 null 走兜底；
 *   - 画布常驻不卸载（D8）：antd Tabs 默认 destroyInactiveTabPane=false
 *     （非激活隐藏不销毁，防画布状态丢失）；路由 view 态持久化=UX1
 *     D2 ?tab= URL 面（原挂账行收口——view 态不参与 content-hash 维持）；
 *   - viewer3d 标签=Viewer3dPane（懒加载 Scene 独立 chunk §12.6；面板级
 *     ErrorBoundary 在其内）；canvas 标签=CanvasPane（FE4：默认标签首屏
 *     直渲染只读工艺画布——D4 不 lazy，URL ?project= 与 viewer3d 共用）；
 *     siteplan 标签=SiteplanPane（M3：design.site 厂区布置编辑器——原生
 *     SVG 自绘零新依赖，?project= 只读订阅+空态引导，不 lazy 无大件）；
 *     solutions 标签=SolutionsPane（FE6：单单元枚举提交→SSE 任务进度→
 *     分页方案表→行级应用——URL ?task= 联动，与 ?project= 双参共存）；
 *     elevation 标签=ElevationPane（FE7：latest done calc 纵断投影——
 *     懒加载 ProfileChart（echarts 独立 chunk）+工况切换+提升面板，
 *     "wp:task" 事件桥 invalidate 刷新）；trust 标签=TrustPane（P2 次批
 *   2026-09-12：结果可信度报告——ADR-012 D8 第八标签，全工况聚合
 *   无工况切换）；cost 标签=CostPane（FE8：
 *     latest done calc 四模块概算装配——分级汇总表+可折叠溯源+指标
 *     对照卡+工况切换，非 lazy 无大件，"wp:task" 事件桥第四处）；
 *     drawings 标签=DrawingsPane（FE9：dxf 单元图导出+产物目录+元数据
 *     预览卡——工况/单元源 cost/projects 同键缓存共享，"wp:task" 事件
 *     桥第五处）；占位屏组件随 FE9 退役删除（宪法 §2 死代码即删——
 *     六标签零消费面）；
 *   - 本文件只做布局与路由组合；业务交互一律在 features 内（§13.5）；
 *   - R2-A 批 2 D2 ?token= 首参引导：编排=模块加载期最早时点（先于任何
 *     React Query 请求；StrictMode 双挂载安全——幂等写+剥离）；分层预裁
 *     本编排只能在 app 层（shared/api 的 token.ts 不得 import 本层
 *     projectParam——分层禁令），main.tsx 零触碰；读 parseTokenParam
 *     →非 null 则 setApiToken+replaceState 剥离（他键原序保留）；
 *     R 轮 G1-02/07 复核（2026-09-02）：node 无 window 守卫跳过；trim
 *     非空才写（纯空白仅剥离不落库——写入面口径两分记于顶层块注）；
 *   - R2-A 批 2 D5 连接设置入口：Header 设置按钮（齿轮，静默常驻——
 *     token 空默认不自动弹零请求扰动）+TokenSettingsModal（保存/清除/
 *     关闭——零即时校验）；D4 自愈回路=useEffect 监听 AUTH_EVENT（401
 *     派发方 shared/api/http.ts）自动开 Modal，卸载移除监听；
 *   - M2 左侧 Sider=UnitLibrary 单元库浏览（app 层薄壳：四线分组树+
 *     搜索+Drawer 详情——组装面在 ./unitLibraryTree 纯函数；onNavigateTab
 *     复用 handleTabChange 切 canvas——AppRoute 七键冻结面零扩，单元库=
 *     Sider UI 态不进 URL）；C2-lib 图标行重制+libraryFocusId 受控
 *     （App 持态→Sider[Drawer 开闭]与 CanvasPane[画布定位光环]双穿线
 *     ——briefs/task-C2-lib-plan.md §二 U3）；
 *   - C1 滚动容器骨架（需求①根治——task-C1-plan.md §3c）：根 Layout
 *     100vh+overflow hidden，document 级整页滚动根除；滚动域下放=Tabs
 *     内容层（className wp-scroll-tabs——global.css 结构微调：content-
 *     holder overflow auto 每标签统一滚动域）+Sider 自滚（overflow auto
 *     ）+内层 Layout/Content minHeight 0 收敛——原 Content/Tabs 零约束
 *     致滚出窗口暴露 body 底色（c-analysis S3 实证）；画布标签内部
 *     CanvasFlow 560 固定高自含（React Flow fitView 自管，二期重制面）；
 *   - C1 顶栏品牌区+状态栏（方向 A「深海工程台」呈裁通过 2026-09-10）：
 *     品牌区=水滴标（radial-gradient+鎏金描边阴影）+「智水蓝图
 *     WaterPrint」双语名；顶栏底=wp-gold-edge 鎏金收边线（global.css）；
 *     StatusBar 挂根 Layout 内（flex 列末项——100vh 内不被推出视口）；
 *     Sider 宽 280→232+去 theme light（token siderBg 承载）。
 */
import { FolderOpenOutlined, SettingOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { Button, Layout, Tabs, Typography } from "antd";

import { CanvasPane } from "./canvasPane";
import { ComparePane } from "./comparePane";
import { CostPane } from "./costPane";
import { TrustPane } from "./trustPane";
import { DrawingsPane } from "./drawingsPane";
import { ElevationPane } from "./elevationPane";
import { ProjectManagerModal } from "./projectManagerModal";
import { Providers } from "./providers";
import type { AppRoute } from "./router";
import {
  clearTokenParam,
  parseEnumParam,
  parseTabParam,
  parseTaskParam,
  parseTokenParam,
  withTabParam,
} from "./projectParam";
import { SiteplanPane } from "./siteplanPane";
import { SolutionsPane } from "./solutionsPane";
import { StatusBar } from "./statusBar";
import { TokenSettingsModal } from "./tokenSettingsModal";
import { UnitLibrary } from "./unitLibrary";
import { Viewer3dPane } from "./viewer3dPane";
import { setApiToken } from "../shared/api/token";
import { AUTH_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";

const { Sider, Content, Header } = Layout;

// R2-A 批 2 D2：?token= 首参引导（模块加载期最早时点——先于任何 React
// Query 请求；StrictMode 双挂载安全：幂等写+剥离）。分享链带凭证形态：
// 读 ?token= →trim 非空写 localStorage+replaceState 剥离 token 键
// （防令牌驻留地址栏/进入分享截图——他键 project/task 原序保留）。
// R 轮 G1-02：node 面（无 window）守卫跳过——浏览器语义与时序不变
// （顶层块仍在任何 React 渲染/fetch 之前）。
// R 轮 G1-07 两条写入面口径：首参引导 trim 空=不写仅剥离（URL 引导
// 不覆盖既有 localStorage 配置）；Modal 保存 trim 空=清除（tokenSettings-
// Modal 用户显式动作剥令牌）——共通面=纯空白 token 永不落库。
// IDLE-Q4 G1-03（2026-09-02）：replaceState 重拼 URL 拼接 location.hash
// ——当前全库零 hash 消费面（二审实证在册），纯防御性收口：未来引入
// hash 路由时首参引导不再静默丢 hash。
if (typeof window !== "undefined") {
  const bootstrapToken = parseTokenParam(window.location.search);
  if (bootstrapToken !== null) {
    const trimmed = bootstrapToken.trim();
    if (trimmed !== "") {
      setApiToken(trimmed);
    }
    const stripped = clearTokenParam(window.location.search);
    const searchPart = stripped ? `?${stripped}` : "";
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${searchPart}${window.location.hash}`,
    );
  }
}

/** UX1 D2/S4 初值三级解析：?tab= 合法值→用之；无 ?tab= 有 ?task= 或
 * ?enum=→solutions（深链意图——两任务轨皆落方案浏览[ENG5 D6]；仅初值
 * 落点不跳转）；缺省 canvas（FE3 D1 面）。 */
function initialRoute(): AppRoute {
  const tab = parseTabParam(window.location.search);
  if (tab !== null) {
    return tab;
  }
  const hasTaskDeepLink =
    parseTaskParam(window.location.search) !== null ||
    parseEnumParam(window.location.search) !== null;
  return hasTaskDeepLink ? "solutions" : "canvas";
}

export function App() {
  const [activeKey, setActiveKey] = useState<AppRoute>(initialRoute);
  // R2-A 批 2 D5：连接设置 Modal 开态（入口=Header 齿轮按钮+401 自愈回路）
  const [settingsOpen, setSettingsOpen] = useState(false);
  // P2 生命周期 L4：项目管理 Modal 开态（入口=Header 文件夹钮+空态钮双入口）
  const [managerOpen, setManagerOpen] = useState(false);
  // C1 顶栏项目徽章（视觉稿件）：当前项目上下文指示（截断 id——全量在状态栏）
  const [projectId] = useProjectId();
  // C2-lib 联动态（U3）：单元库叶选中=Drawer 开闭+画布定位光环同源
  // （App 持态受控穿线——FE5 D2 selectedUnitId 同制；生命周期=Drawer
  // 开闭，关抽屉=解除）
  const [libraryFocusId, setLibraryFocusId] = useState<string | null>(null);

  // R2-A 批 2 D4/D5 自愈回路：customInstance 401 → AUTH_EVENT → 自动开
  // 连接设置（错 token 用户改对的引导面）；卸载移除监听。
  useEffect(() => {
    const openSettings = () => setSettingsOpen(true);
    window.addEventListener(AUTH_EVENT, openSettings);
    return () => window.removeEventListener(AUTH_EVENT, openSettings);
  }, []);

  /** UX1 D2/S4：切标签经 withTabParam replaceState 写 ?tab=（他键原序
   * 保留——project/task 不动；刷新/分享后落点保持）。 */
  const handleTabChange = (key: string) => {
    // items key 全集=AppRoute 冻结面（string 回调值收窄安全）
    const next = key as AppRoute;
    setActiveKey(next);
    const search = withTabParam(window.location.search, next);
    window.history.replaceState(
      null,
      "",
      search ? `${window.location.pathname}?${search}` : window.location.pathname,
    );
  };
  return (
    <Providers>
      {/* C1 滚动容器骨架（需求①根治）：100vh 布局+overflow 每层收敛——
          document 级整页滚动根除（原 Content/Tabs 零约束→滚出窗口暴露
          body 底色）；滚动域=Tabs 内容层（wp-scroll-tabs）+Sider 自滚 */}
      <Layout style={{ height: "100vh", overflow: "hidden" }}>
        <Header
          className="wp-gold-edge"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 16px",
            flex: "none",
          }}
        >
          {/* C1 品牌区：水滴标+双语名（G1-03 R 轮：--wp-water/--wp-gold
              经 var()/color-mix 消费；#1d5fd0/#0e3a8f/#cfe6ff 与投影
              rgba(29,95,208,.35)=品牌装饰色，不入语义轴——渐变造型
              专用值，登记于本注记） */}
          <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              aria-hidden
              style={{
                width: 26,
                height: 26,
                borderRadius: 7,
                position: "relative",
                display: "inline-block",
                background:
                  "radial-gradient(circle at 30% 25%, var(--wp-water) 0%, #1d5fd0 60%, #0e3a8f 100%)",
                boxShadow:
                  "0 0 0 1px color-mix(in srgb, var(--wp-gold) 45%, transparent), 0 2px 8px rgba(29, 95, 208, 0.35)",
              }}
            >
              <span
                style={{
                  position: "absolute",
                  left: 8,
                  top: 6,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#cfe6ff",
                  opacity: 0.85,
                }}
              />
            </span>
            <Typography.Text strong style={{ fontSize: 15, letterSpacing: 0.5 }}>
              智水蓝图
            </Typography.Text>
            <Typography.Text
              type="secondary"
              style={{ fontSize: 12, marginLeft: -2 }}
            >
              WaterPrint
            </Typography.Text>
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {/* C1 项目徽章（视觉稿件）：绿点=已选项目上下文+截断 id */}
            {projectId === null ? null : (
              <span
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  height: 28,
                  padding: "0 12px",
                  background: "var(--wp-bg-elevated)",
                  border: "1px solid var(--wp-border)",
                  borderRadius: 6,
                  color: "var(--wp-text-2)",
                  fontSize: 12,
                  userSelect: "none",
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "var(--wp-success)",
                  }}
                />
                <span style={{ fontFamily: "var(--wp-font-mono)" }}>
                  {projectId.slice(0, 8)}
                </span>
              </span>
            )}
            {/* P2 生命周期 L4：项目管理入口（治理面常驻——文件夹钮开
                ProjectManagerModal：重命名/复制/删除/打开） */}
            <Button
              type="text"
              icon={<FolderOpenOutlined />}
              onClick={() => setManagerOpen(true)}
              aria-label="项目管理"
              title="项目管理（重命名/复制/删除）"
              data-testid="wp-open-manager-header"
            />
            {/* R2-A 批 2 D5：设置按钮静默常驻（token 空默认不弹不扰动） */}
            <Button
              type="text"
              icon={<SettingOutlined />}
              onClick={() => setSettingsOpen(true)}
              aria-label="连接设置"
              title="连接设置"
            />
          </span>
        </Header>
        <Layout style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
          {/* M2：单元库浏览实装替换占位——C1 宽 280→232（工程密度）+自滚；
              C2-lib：图标行重制+focusId 受控（联动穿线）。
              C2-ALIGN A1：右缘浅色分割线（direction-a .sider border-right
              同构——--wp-border-2=#1b2c49=--colorBorderSecondary 同值轴）。 */}
          <Sider
            width={232}
            style={{
              overflow: "auto",
              flex: "none",
              borderRight: "1px solid var(--wp-border-2)",
            }}
          >
            <UnitLibrary
              focusId={libraryFocusId}
              onFocusChange={setLibraryFocusId}
              onNavigateTab={() => handleTabChange("canvas")}
            />
            {/* 工况面 UX 反馈批件 2：CheckedUnitsPanel 自 Sider 拆除归位
                comparePane 双页（ADR-018 D4 附勘正——Sider 减负为副产物） */}
          </Sider>
          <Content style={{ display: "flex", flexDirection: "column", minHeight: 0, flex: 1 }}>
            <Tabs
              className="wp-scroll-tabs"
              activeKey={activeKey}
              onChange={handleTabChange}
              items={[
                {
                  key: "canvas",
                  label: "工艺画布",
                  children: <CanvasPane libraryFocusId={libraryFocusId} />,
                },
                {
                  key: "siteplan",
                  label: "厂区布置",
                  children: <SiteplanPane />,
                },
                {
                  key: "solutions",
                  label: "方案浏览",
                  children: <SolutionsPane />,
                },
                {
                  key: "viewer3d",
                  label: "三维视图",
                  children: <Viewer3dPane />,
                },
                {
                  key: "elevation",
                  label: "高程纵断",
                  children: <ElevationPane />,
                },
                {
                  key: "drawings",
                  label: "图纸预览",
                  children: <DrawingsPane />,
                },
                {
                  key: "cost",
                  label: "概算",
                  children: <CostPane />,
                },
                {
                  key: "compare",
                  label: "工况对比",
                  children: <ComparePane />,
                },
                {
                  key: "trust",
                  label: "可信度",
                  children: <TrustPane />,
                },
              ]}
            />
          </Content>
        </Layout>
        {/* C1 状态栏：底部全局信息条（项目 id+就绪态——工程软件标配；
            在根 Layout 内=flex 列末项，不被 100vh 推出视口 */}
        <StatusBar />
      </Layout>
      <TokenSettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <ProjectManagerModal open={managerOpen} onClose={() => setManagerOpen(false)} />
    </Providers>
  );
}
