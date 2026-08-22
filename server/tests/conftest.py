"""server 测试系统装配：httpx AsyncClient/TestClient fixtures（薄，禁业务断言）。

输入:  无
输出:  app/client/settings fixtures（供 routers/services/jobs 测试）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【fixtures】
#   test_settings：临时目录版 Settings（projects/exports/data 均
#     指向 tmp_path，隔离真实文件系统）；
#   client：create_app(test_settings) + httpx TestClient
#     （实现期改用 ASGITransport AsyncClient）。
# 【本文件只读锁定范围之外】——server/tests 全目录同样纳入
#   test-lock.manifest.json（scripts/lock_tests.py 统一处理）。
# ══════════════════════════════════════════════════════════════════
