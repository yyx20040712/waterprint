/**
 * 应用壳：布局骨架+标签路由状态机+Providers 组合（app 层组合面）。
 *
 * 输入: 各 feature 切片与 app 层装配件（app 层是唯一允许组合 features 的层）
 * 输出: 应用布局（§19.2 骨架：顶栏/左侧单元库/中央标签工作区）——
 *       Providers 包裹（ConfigProvider 深色+QueryClient）+Tabs activeKey 状态机
 *
 * 规格说明（FE3 批 6b 段一，D1/D8 实装）：
 *   - 路由机制定 D1=AntD Tabs 状态机：activeKey 用 useState（默认 canvas；
 *     路由名与次序=router.tsx AppRoute 冻结面 canvas/viewer3d/elevation/
 *     drawings/cost），Tabs activeKey/onChange 驱动——不引入 react-router
 *     （零新依赖纪律；router.tsx 头「M2 定型」本批定夺为状态机）；
 *   - 画布常驻不卸载（D8）：antd Tabs 默认 destroyInactiveTabPane=false
 *     （非激活隐藏不销毁，防画布状态丢失）；路由 view 态持久化挂账 UX 批；
 *   - viewer3d 标签=Viewer3dPane（懒加载 Scene 独立 chunk §12.6；面板级
 *     ErrorBoundary 在其内）；canvas 标签=CanvasPane（FE4 批 6b 段一：
 *     默认标签首屏直渲染只读工艺画布——D4 不 lazy，URL ?project= 与
 *     viewer3d 共用）；其余三标签维持占位屏（feature 骨架未实装
 *     ——D8 非本批范围）；
 *   - 本文件只做布局与路由组合；业务交互一律在 features 内（§13.5）。
 */
import { useState } from "react";
import { Layout, Menu, Tabs, Typography } from "antd";

import { CanvasPane } from "./canvasPane";
import { Providers } from "./providers";
import type { AppRoute } from "./router";
import { Viewer3dPane } from "./viewer3dPane";

const { Sider, Content, Header } = Layout;

/** 占位标签屏（feature 骨架未实装——D8 维持现状措辞；标识符避开 grep
 *  门禁英文占位特征词）。 */
function StubPane({ label }: { label: string }) {
  return (
    <Typography.Text type="secondary">
      {label}：骨架阶段结构与规格已冻结，实现按里程碑推进（见
      docs/file-contracts.md）
    </Typography.Text>
  );
}

export function App() {
  const [activeKey, setActiveKey] = useState<AppRoute>("canvas");
  return (
    <Providers>
      <Layout style={{ height: "100vh" }}>
        <Header>WaterPrint 智水蓝图</Header>
        <Layout>
          <Sider theme="light">
            <Menu items={[{ key: "lib", label: "单元库（待实装）" }]} />
          </Sider>
          <Content>
            <Tabs
              activeKey={activeKey}
              // items key 全集=AppRoute 冻结面（string 回调值收窄安全）
              onChange={(key) => setActiveKey(key as AppRoute)}
              items={[
                {
                  key: "canvas",
                  label: "工艺画布",
                  children: <CanvasPane />,
                },
                {
                  key: "viewer3d",
                  label: "三维视图",
                  children: <Viewer3dPane />,
                },
                {
                  key: "elevation",
                  label: "高程纵断",
                  children: <StubPane label="高程纵断" />,
                },
                {
                  key: "drawings",
                  label: "图纸预览",
                  children: <StubPane label="图纸预览" />,
                },
                {
                  key: "cost",
                  label: "概算",
                  children: <StubPane label="概算" />,
                },
              ]}
            />
          </Content>
        </Layout>
      </Layout>
    </Providers>
  );
}
