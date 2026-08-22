# ADR-004：项目文件双态结构与确定性序列化

- 状态：**已接受**（计划 §12.3；M1 落地）
- 背景：窗口布局/相机/时间戳等易变字段污染 diff 与输入哈希（§11 R10），
  破坏可复算承诺。
- 决策：
  1. 项目文件三段：design（参与 content-hash 与可复算）+ view（不参与）
    + metadata（format_version / content_hash / engine_version / data_version）；
  2. 序列化确定性：键递归排序、round(x,10) 定点、无随机 ID、UTF-8、
     \n 换行——保存两次字节级相同；
  3. content_hash 只覆盖 design；view 变更不算 dirty 不触发重算；
  4. 可复算三元组：结果 = f(design_hash, engine_version, data_version)；
     计算迹与全部导出物记录三元组，任一变化即结果过期（§16 A8）；
  5. 迁移走 format_version 链（project/migration.py），未来版本拒绝打开。
- 后果：git diff 干净；缓存/结果失效判定唯一依据是三元组。
- 细化归属：M1 io/content_hash/migration 骨架实现。
