"""项目文件确定性序列化读写（design/view 双态一起落盘，字节级稳定）。

输入:  ProjectFile 对象（save） / 磁盘 JSON（load）
输出:  JSON 文件（保存两次字节级相同） / ProjectFile 对象（往返无损）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/project/test_io.py）
#
# 【公开接口】
#   save_project(project: ProjectFile, path: Path) -> None
#   load_project(path: Path) -> ProjectFile
#   dumps(project) -> str / loads(text) -> ProjectFile   内存形态正门
#
# 【行为规格】
#   R1 确定性序列化（ADR-004）：键递归排序、浮点 round(x, 10) 定点
#      表示、无时间戳/随机 ID 进入输出、ensure_ascii=False + 显式
#      encoding="utf-8"、换行统一 \n——同对象两次保存字节级相同
#      （CI 常驻断言）。
#   R2 往返无损：save→load→save 字节相同；对象级 roundtrip 相等
#      （view 态含时间戳字段除外——时间戳只存在于 view 态，
#      不影响 design 哈希）。
#   R3 load 侧防弹（§18 上传面）：JSON 深度/大小上限、
#      parse_project 严格校验（extra=forbid）、错误消息指明路径
#      （如 design.nodes[3].params）；永不 pickle。
#   R4 保存原子性：写临时文件 + rename（防半截文件）；临时文件
#      在目标目录内命名（同分区 rename 原子性）。
#   R5 文件锁（§17.3）：同项目并发打开防护——.lock 探测 + 明确警告
#      （最低成本方案，v1 定位单用户）。
#
# 【测试要求】双跑字节相同、往返无损、深度/大小炸弹拒绝、
#   原子保存（模拟中断不留半截）、锁探测。
#
# 【参照】重写计划 §12.3/§17.3/§18；ADR-004
# ══════════════════════════════════════════════════════════════════
