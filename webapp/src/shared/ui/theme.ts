/**
 * 主题 token：深色默认/亮色切换、语义色定义（AntD 6 dark algorithm）
 * （结构预留：随 M2 实装）。
 *
 * FE2 升版注记：antd 5→6（6.6.x）后 dark algorithm 契约延续，本骨架
 * 零代码改动；实装时按 v6 Token 体系核对语义色键名。
 *
 * 输入:  主题切换状态（UI slice）
 * 输出:  AntD ConfigProvider 主题配置
 *
 * 规格说明（骨架冻结，实装必须满足）：
 *   - 语义色纪律：绿合格/橙警告/红错误/蓝水线/棕泥线，其余灰阶（§19.3）；
 *   - 紧凑模式默认（small/12px/8px 栅格）。
 */
