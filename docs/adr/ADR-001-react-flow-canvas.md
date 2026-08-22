# ADR-001：节点画布采用 React Flow（含三维参数化 schema 与 R3F）

- 状态：**已接受**（计划 §2/§10；M2 落地）
- 背景：旧系统 tkinter 自研画布是核心痛点；三维标杆（数字孪生平台）面向
  运维非设计，无现成品可搬。
- 决策：
  1. 工艺画布用 React Flow（xyflow）：端口/连线/缩放/小地图/自动布局开箱即用；
  2. 三维用 three.js + React Three Fiber：参数化组件库（图元组合优先，
     CSG 仅限开口），与计算结果同 schema 驱动——改参数即变模型；
  3. 三维几何投影在 core/geometry（CPU 场景图 JSON），前端只做类型化
     渲染器，禁止 TS 侧推导业务几何（§16 A7）；
  4. 图纸用 ezdxf 参数化 DXF（ADR-006）。
- 后果：前端依赖 xyflow/three 生态；节点契约（自包含+端口类型化+
  画布只管连接不管计算）成为核心架构（contracts/unit_api 对应物）。
- 细化归属：M2 画布 MVP + 首批三维组件。
