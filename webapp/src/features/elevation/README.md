# elevation —— 高程纵断视图

沿流程的水面/池底/埋深/地面纵断可视化（消费 /api/elevation 响应——core
ElevationProfile+PumpingPlan 服务端装配投影）。

## 文件清单（FE7 批 6b 段五实装 2026-08-29）

| 文件 | 职责 | 状态 |
|------|------|------|
| `lib/profileChart.ts` | 纯函数层：narrowElevationResponse 窄化门（顶层八字段+站位十字段+泵站五字段+警告 UF-17 六键逐项校验，非法抛 ElevationViewError 带键定位）+buildChartOption 四线 option 纯对象（地面/水面/池底/池顶——零 echarts import）+ELEVATION_LINE_COLORS 语义色集中一处 | FE7 实装 |
| `lib/profileChart.test.ts` | 投影层纯函数 vitest（node 环境——golden 内联夹具+负例族 17 用例） | FE7 实装（17 绿） |
| `api/useElevationQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/elevation/${projectId}', params?]（conditionKey 全量进键）+select 窄化收口 | FE7 实装 |
| `components/ProfileChart.tsx` | 纵断图组件壳：echarts/core 按需注册（五件恰合）+init/dispose/setOption 生命周期+ResizeObserver+基准面/损失口径注记（echarts 首消费——React.lazy 独立异步 chunk） | FE7 实装（薄壳不测） |
| `components/ConditionSwitcher.tsx` | 工况切换下拉（D9——服务端工况键清单透传；切换=查询键切换按需触发 §17.1） | FE7 实装 |
| `components/PumpStationsPanel.tsx` | 提升点位表+跌水警告列表（D4——core 判定前端仅渲染；空站位=全程自流合法终态） | FE7 实装 |
| `store/elevationStore.ts` | 视图态占位维持（组件内 useState——FE5 D2/FE6 先例） | 占位（激活挂账 UX 批） |

## 规格要点（FE7 后实况）

- 纵断数据全部来自服务端（latest done calc 按需投影——scene 服务模式）；
  前端零标高推算（纯展示投影）——crest_elev=water_level+freeboard 为
  服务端投影字段，前端直用不重算（D5 红线）；
- 四线=地面/水面/池底/池顶（M0.5 骨架「管底」措辞系笔误——
  ProfileStation 无管底字段，FE7 勘误记档）；
- 标高基准=±0.00 相对标高（datum_note 服务面下发——口径单一真源）；
  绝对标高设计输入通道挂账 server 批/M5 沿册；
- 「横纵比例分设」的实装面=echarts yAxis scale:true（标高真值原点）+
  xAxis category（站位序）——后端比例参数面不存在（骨架措辞「比例参数
  来自后端 options」修正记档，FE7）；
- 沿程损失未接线（head_losses 空段——管线几何归 M5 管线批）：loss_in
  恒 0 如实呈现+图表注记；
- 工况切换只读另一索引（§17.1：未算工况按需触发——查询键含工况全量）；
  ADR-007 双图并排对比挂账 UX 批。
