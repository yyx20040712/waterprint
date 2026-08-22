"""命令行入口：内核唯一可执行点（无头运行/脚手架/批量导出的落点）。

输入:  argv（子命令与参数）
输出:  进程退出码 / 控制台输出 / 产物文件（calc、export、new-unit…）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/app/test_cli.py）
#
# 【公开接口】
#   main(argv: Sequence[str] | None = None) -> int   入口（返回退出码）
#   子命令集（v1 冻结）：
#     wp calc <project.json> [--conditions design,avg]
#         [--out result.json]        全流程计算（app.run_full_calc）
#     wp export calcbook|audit|dxf|scene <project> <result>
#         批量导出（M1 起逐步启用）
#     wp new-unit <line> <name>
#         从 units_lib/_template 生成单元骨架（§15 工程细节 6：
#         结构一致性不靠文档靠工具；line ∈ 四业务线，重名拒绝）
#     wp validate <project.json>    项目校验（零计算，快速反馈）
#     wp selfcheck                  注册表静态校验 + 架构自检报告
#
# 【行为规格】
#   R1 参数解析零第三方依赖之争：argparse（标准库）；
#      stdout 结构化消息（成功摘要/失败清单），退出码：
#      0=成功 2=用法错误 3=校验失败 4=计算失败（诊断进 stderr）。
#   R2 new-unit 幂等保护：目标包已存在 = 拒绝（防误覆盖）；
#      生成后打印"下一步清单"（登记 file-contracts、写测试、锁定）。
#   R3 输出确定性：calc 输出 JSON 走 result_schema 确定性序列化
#      （脚本化 diff 友好）；日志含 repro 三元组。
#   R4 Windows 路径兼容：显式 encoding="utf-8" 读写；
#      PYTHONUTF8 提示在 --help 尾注（教训：GBK 双重编码）。
#
# 【测试要求】calc/validate 子命令管线（M1 起真数值）、
#   new-unit 生成结构完整且拒绝重名、退出码语义、乱码防线
#   （中文输出在 GBK 控制台不崩溃）。
#
# 【参照】重写计划 §13.3 cli 行/§15 工程细节 6
# ══════════════════════════════════════════════════════════════════
