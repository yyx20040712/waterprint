/**
 * 客户端模式协议期望值（联机架构第六批 2026-11-19——版本握手比对面）。
 *
 * 输入:  无（构建期常量——与所配套服务端发行同源声明的期望值）
 * 输出:  EXPECTED_API_VERSION（API 语义版本期望）/EXPECTED_DATA_VERSION
 *        （数据包三包聚合串期望）——remoteHandshake.compareServerVersions
 *        消费（连接测试/在线握手两面）
 *
 * 规格说明（联机第六批任务书——v1 缺省，用户「瑕疵后置」授权）：
 *   - 策略=同源常量（b5 端点 API_SEMANTIC_VERSION 同款制式）：webapp
 *     是不含引擎的界面包，无法运行期自算数据面期望值，故随构建声明
 *     与配套服务端同源的常量；api_version 镜像 server services.runtime
 *     API_SEMANTIC_VERSION（仅 API 面不兼容变更时人工同步抬版），
 *     data_version 镜像 core load_run_env 三包聚合串形态
 *     （assumptions@..+coefficients@..+unit_prices@.. 包名排序拼接）；
 *   - 漂移防线=clientProtocol.test.ts：自仓库 data/ 三 manifest 重算
 *     聚合串并与常量对拍——数据包抬版未同步常量即 webapp 测试红；
 *   - 取舍记档：常量与 server 端真值无机器级单源（跨 py/ts 无共享
 *     真源载体），靠测试重算锚定——发行流程裁记：数据包抬版批须同批
 *     改本常量（测试红会拦）；桌面客户端 b7 打包时本文件随 UI 包固化
 *     即「本客户端配套的期望值」。
 */

/** API 语义版本期望（镜像 server API_SEMANTIC_VERSION——不兼容变更抬版）。 */
export const EXPECTED_API_VERSION = "1.0";

/** 数据包三包聚合串期望（镜像 core load_run_env 聚合形态——clientProtocol.test 锚定）。 */
export const EXPECTED_DATA_VERSION =
  "assumptions@1.0.0+coefficients@1.8.0+unit_prices@1.2.0";
