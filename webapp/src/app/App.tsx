/**
 * 应用壳（骨架期最小接线：布局骨架 + 各 feature 占屏，非业务代码）。
 *
 * 输入: 各 feature 切片（app 层是唯一允许组合 features 的层）
 * 输出: 应用布局（§19.2 骨架：顶栏/左侧单元库/中央标签工作区/右侧面板/底栏）
 *
 * 规格说明（骨架冻结）：
 *   - 本文件只做布局与路由组合；业务交互一律在 features 内；
 *   - features 之间禁止互相 import（§13.5），由本层组合；
 *   - 每个 feature 一个 ErrorBoundary（画布崩溃不清空应用，§15 细节 4）。
 */
import { Layout, Menu, Tabs, Typography } from "antd";

const { Sider, Content, Header } = Layout;

/** M0 骨架屏：feature 实装后由各切片组件替换（占屏文字仅骨架期存在）。 */
export function App() {
  return (
    <Layout style={{ height: "100vh" }}>
      <Header>WaterPrint 智水蓝图 · M0 骨架</Header>
      <Layout>
        <Sider theme="light">
          <Menu items={[{ key: "lib", label: "单元库（待实装）" }]} />
        </Sider>
        <Content>
          <Tabs
            items={[
              { key: "canvas", label: "工艺画布" },
              { key: "viewer3d", label: "三维视图" },
              { key: "elevation", label: "高程纵断" },
              { key: "drawings", label: "图纸预览" },
              { key: "cost", label: "概算" },
            ]}
          />
          <Typography.Text type="secondary">
            骨架阶段：结构与规格已冻结，实现按里程碑推进（见 docs/file-contracts.md）
          </Typography.Text>
        </Content>
      </Layout>
    </Layout>
  );
}
