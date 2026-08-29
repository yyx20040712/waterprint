/**
 * 高程视图 slice：视图态占位（结构预留——实装期裁决维持）。
 *
 * 输入:  无（视图态在组件内 useState 消费）
 * 输出:  无运行期导出（占位维持——纵断数据在 Query 缓存）
 *
 * 规格说明（FE7 批 6b 段五刷新）：
 *   - 视图态组件内 useState（工况切换/图表态——FE5 D2/FE6 D9 先例：
 *     单面板无跨组件共享态即不建 store；elevationPane 消费面）；
 *     zustand 首例留 canvas 编辑批（FE6 记档口径）；
 *   - 纵断数据在 Query 缓存（useElevationQuery queryKey
 *     ['/api/elevation/${projectId}', params?]——本文件零数据面）；
 *     跨标签图表态共享需求出现时再激活本 slice（挂账 UX 批）。
 */
