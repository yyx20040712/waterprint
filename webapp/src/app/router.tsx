/**
 * 路由面：主视图五槽+studio 二级子面值域（B 线四区骨架——两级值域冻结面）。
 *
 * 输入:  无（纯类型与常量——消费面=projectParam〔parseTabParam/withTabParam〕
 *        +App〔槽条 activeKey/切槽状态机〕+测试）
 * 输出:  SlotId/StudioSubface/TabTarget 类型+SLOTS/STUDIO_SUBFACES 常量
 *        （?tab= 语法=<槽> 或 studio.<子面>——点分复合）
 *
 * 规格说明（沿革链：FE3 批 6b 段一 D1 十值面→M3 批 2026-09-03 扩七值→
 *   P2 批 2026-09-12 ADR-018 扩九/十值→P2 用户裁决 2026-10-03 解冻十页签→
 *   2B4 mapping-2b4 §B 终核〔R-D2 命名空间原则+新-06 边缘语义〕——M1 批
 *   2026-10-06 重写为两级值域；旧 AppRoute/ROUTES 十值面删除，兼容归一
 *   在 projectParam.parseTabParam 解析期单点收口）：
 *   - 五槽次序=canvas(默认)/siteplan/viewer3d/elevation/studio
 *     （draft-ia-v3 §3 B-1 L43 逐字——槽条页签次序单源）；
 *   - 子面五值仅 studio 槽可带（study/drawings/cost/compare/trust）——
 *     双段首段须 "studio"，其余槽带子面=非法（parse → null）；
 *   - 画布槽=默认且常驻（切换挂载隐藏不卸载，防画布状态丢失——R1）；
 *   - 路由态持久化=?tab= URL 参数（replaceState 模式——UX1 D2 承袭；
 *     不引入 react-router〔P-B1 用户实裁维持不豁免〕）；
 *   - 本文件只做类型与常量，禁止业务逻辑。
 */
export type SlotId = "canvas" | "siteplan" | "viewer3d" | "elevation" | "studio";
export type StudioSubface = "study" | "drawings" | "cost" | "compare" | "trust";
/** ?tab= 解析终态：subface 仅 studio 槽可带（parse 已归一——studio 恒带 subface）。 */
export type TabTarget = { slot: SlotId; subface?: StudioSubface };
export const SLOTS: readonly SlotId[] = ["canvas","siteplan","viewer3d","elevation","studio"];
export const STUDIO_SUBFACES: readonly StudioSubface[] = ["study","drawings","cost","compare","trust"];
