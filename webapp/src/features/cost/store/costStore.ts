/**
 * 概算视图 slice（占位维持：随 M3 实装——FE8 后仍占位）。
 *
 * 输入:  视图动作（无——工况态组件内 useState，FE8 D8 实况）
 * 输出:  视图态 store（无——激活挂账 UX 批；FE5/6/7 同款先例：
 *        展开行/选中条目等跨组件视图态出现时再立）
 *
 * 规格说明（骨架冻结+FE8 批 6b 段六实况注记）：
 *   - 概算绑定 condition_key（默认 design 档=服务端 D2 缺省回显，
 *     切换显式经查询键——costPane 组件内 useState 承载，未达立
 *     store 门槛）；展开行态由 antd Table 内部承载。
 */
