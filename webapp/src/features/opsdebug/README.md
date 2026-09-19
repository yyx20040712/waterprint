# opsdebug —— 操作链诊断视图

操作链集中 debug 观测面（消费 GET /api/debug/ops-chain/{project_id} 响应
——B4-1 实现批《裁决书》方案五①：项目任务时间线+最新 done calc 三源
深度聚合[诊断摘要/警告计数/trace 公式应用统计]一次呈现）。

## 文件清单（B4-1 实装 2026-09-19）

| 文件 | 职责 | 状态 |
|------|------|------|
| `lib/opsChainView.ts` | 纯函数层：narrowOpsChainResponse 窄化门（顶层 3 键+任务条目 13 键域+聚合块 8 键逐项校验，非法抛 OpsChainViewError）+stateTone 任务状态语义色（done 绿/failed 红/cancelled 灰/进行态蓝）+kindLabel 任务类中文+formatUnix/formatSci/formatProgress 格式化 | B4-1 实装 |
| `lib/opsChainView.test.ts` | 投影层纯函数 vitest（窄化正负例族+状态语义色/标签词典/格式化对照） | B4-1 实装 |
| `api/useOpsChainQuery.ts` | orval 生成 hook 薄封装：queryKey ['/api/debug/ops-chain/${projectId}']+select 窄化收口（useTrustQuery 同构先例；全任务时间线无工况参数） | B4-1 实装 |
| `components/OpsChainView.tsx` | 观测面主体（纯展示薄壳）：状态条（stale 黄条+latest_calc 空块蓝条+诊断降级蓝条）+任务时间线卡（注册序表+状态 Tag+错误诊断列）+三源聚合卡（诊断摘要计数极值/警告计数/trace 三桶统计——明细走「可信度」标签） | B4-1 实装（薄壳不测） |

## 规格要点（B4-1 实况）

- 数据全部来自服务端（GET /api/debug/ops-chain：manager 注册表任务面
  +latest_calc_result 共享件[B3-a 槽位第七消费面]+calc-diag 独立
  artifact[ADR-012]+PlantResult.trace 总线聚合）；
- latest_calc=null 单义空块（无 done calc 或结果文件不可读）——面板
  蓝条降级呈现不猜因，时间线对照自明（与 trust 端点 404 消费面语义
  分立）；
- 时间轴口径：注册序=操作序（server 任务档案无时钟字段）；完成时刻
  列=server 内存 WP4 值，进程重启后恢复记录=恢复时刻新租约（悬浮注记
  诚实呈现）；
- trace 不回全量节点（万级体积面——全量迹经 calcbook/audit 导出面）；
- 刷新联动：TASK_EVENT 事件桥（第七处监听）invalidate 键。
