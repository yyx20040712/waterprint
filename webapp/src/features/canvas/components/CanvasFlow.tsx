/**
 * React Flow 画布容器：design 工艺图只读渲染（ADR-001 渲染面）。
 *
 * 输入:  projectId（useProjectQuery 数据通道→projectFlow 投影——组件薄壳
 *        唯一数据源，服务端数据不进 store §17.2/D5）
 * 输出:  工艺画布只读工作区（React Flow：UnitNode 卡片+方向端口+recycle
 *        虚线+fitView 视口适配；加载/空态/错误薄壳）
 *
 * 规格说明（FE4 批 6b 段一，D1/D4/D5/D7 裁决）：
 *   - 只读批交互面：视图态（缩放/平移/框选）开；编辑面全关——edges
 *     Connectable=false+不传 onConnect/onNodesChange（受控只喂投影产物，
 *     无编辑落盘）；nodesDraggable=false（受控无 onNodesChange 时拖动
 *     无效果——明示只读免误导光标；简报「可 true」裁量面记此取舍）；
 *     elementsSelectable=true（选中高亮非编辑）；
 *   - D4 不 lazy：canvas=默认标签首屏必渲染（App activeKey 默认 canvas）
 *     ——零动态 import 零 Suspense，xyflow 入口 bundle 接受（挂账 FE3
 *     A-2 打包优化统筹）；
 *   - D7 样式：@xyflow/react/dist/style.css 组件内引入+colorMode=dark
 *     官方暗色（ConfigProvider 深色同谱）+最小 style 覆盖集——禁引外部
 *     css 文件；
 *   - 投影层三类显式拒（D6 版本轻门/形状逐类/悬空边）在 useMemo
 *     try/catch 落错误薄壳（FE3 Scene R2 C2 围栏同构——ErrorBoundary
 *     之外的第二个错误出口，不白屏）；
 *   - nodeTypes 模块级常量（引用稳定——重渲染不触发 React Flow 内部
 *     重挂载告警）；编辑态 store（canvasStore）/连线规则/自动布局维持
 *     骨架挂账段二（D5：只读批无编辑态入 store）。
 */
import { useMemo } from "react";
import {
  ReactFlow,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useProjectQuery } from "../api/useProjectQuery";
import {
  ProjectFlowError,
  projectFlow,
  type ProjectFlow,
} from "../lib/projectFlow";
import { UnitNode } from "./UnitNode";

/** 自定义节点注册（模块级常量——引用稳定）。 */
const NODE_TYPES: NodeTypes = { unit: UnitNode };

export function CanvasFlow({ projectId }: { projectId: string }) {
  const query = useProjectQuery(projectId);
  // 投影围栏：D6 显式拒在此收编落错误薄壳（fetch isError 之外第二出口）
  const projection = useMemo<{
    flow: ProjectFlow | null;
    error: ProjectFlowError | null;
  }>(() => {
    if (!query.data) {
      return { flow: null, error: null };
    }
    try {
      return { flow: projectFlow(query.data), error: null };
    } catch (error) {
      return {
        flow: null,
        error:
          error instanceof ProjectFlowError
            ? error
            : new ProjectFlowError(String(error)),
      };
    }
  }, [query.data]);

  if (query.isError) {
    return (
      <div role="alert">
        工艺图加载失败：
        {query.error instanceof Error ? query.error.message : "未知错误"}
      </div>
    );
  }
  if (projection.error) {
    return (
      <div role="alert">工艺图投影失败：{projection.error.message}</div>
    );
  }
  const flow = projection.flow;
  if (!flow) {
    return <div>工艺图加载中…（{projectId.slice(0, 8)}）</div>;
  }
  if (flow.nodes.length === 0) {
    return (
      <div>
        该项目工艺图为空（design.nodes 无节点）——建图流程见
        docs/user-manual.md「快速开始」。
      </div>
    );
  }
  return (
    <div style={{ height: 560, border: "1px solid #434343" }}>
      <ReactFlow
        nodes={flow.nodes}
        edges={flow.edges}
        nodeTypes={NODE_TYPES}
        fitView
        colorMode="dark"
        nodesDraggable={false}
        nodesConnectable={false}
        edgesFocusable={false}
        elementsSelectable
        deleteKeyCode={null}
        proOptions={{ hideAttribution: true }}
        style={{ backgroundColor: "#141414" }}
      />
    </div>
  );
}
