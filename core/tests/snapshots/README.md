# snapshots —— syrupy 输出快照

输出快照回归（§6.5）：计算书 Excel、DXF 图纸、审计报告 HTML 的
**内容哈希快照**锁定结构——任何输出变化必须显式 `--snapshot-update`
并过审查。

- 快照文件由 syrupy 生成于本目录（`__snapshots__/`，不入锁定清单：
  更新走显式命令 + 审查，与只读测试的"人类解锁"流程互补）；
- 接入节奏：M1（calcbook 单单元）→ M2（DXF 首批单元）→ M4（审计报告）。
