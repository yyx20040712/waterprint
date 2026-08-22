# elevation —— 高程纵断视图

沿流程的水面/池底/埋深/地面纵断可视化（消费 core ElevationProfile 数据）。

## 文件规划（实装期创建，先登记 file-contracts.md）

| 文件 | 职责 |
|------|------|
| `components/ProfileChart.tsx` | 纵断图（ECharts 折线：四线 + 标高标注） |
| `components/ConditionSwitcher.tsx` | 工况切换（结果按 condition_key 索引） |
| `components/PumpStationsPanel.tsx` | 提升点位/跌水警告列表 |
| `store/elevationStore.ts` | 当前工况/缩放 slice |
| `api/` | 生成客户端调用 |

## 规格要点

- 纵断数据全部来自 core（elevation/profile.py 产出）；
  前端零标高推算（纯展示投影）；
- 横纵比例分设显示（与图纸版一致的比例参数来自后端 options）；
- 工况切换只读另一索引（§17.1：未算工况按需触发）。
