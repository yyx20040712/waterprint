# desktop 桌面壳（waterprint_desktop）

> WaterPrint 的第三种客户端形态（L6）：pywebview 桌面窗口 + 联机三角色
> 装配（ADR-028，联机第七批 b7 2026-11-19）。一个安装包永远全量
> （core+server+webapp 构建+壳），联机两级开关在三种角色间切换。

## 结构（逐文件规格见各源码头"规格说明"节+docs/file-contracts.md §7）

| 件 | 职责 |
|---|---|
| `waterprint_desktop/config.py` | 角色配置持久化（desktop.json 原子读写+token 生成保管+路径解析） |
| `waterprint_desktop/roles.py` | 三角色装配决策单源（plan_for 纯函数+端口约定常量） |
| `waterprint_desktop/server_thread.py` | uvicorn 显式启停线程句柄（引擎/静态壳共用） |
| `waterprint_desktop/engine.py` | 引擎装配（角色化 Settings+create_app 消费+UI 同源挂载） |
| `waterprint_desktop/static_shell.py` | 客户端模式静态壳（127.0.0.1:8620 serve webapp dist） |
| `waterprint_desktop/runtime.py` | 运行监督（角色切换活体重启+生命周期编排） |
| `waterprint_desktop/bridge.py` | pywebview 桥（getConfig/setNetworkRole——TS 契约对齐） |
| `waterprint_desktop/main.py` | 薄窗口层（不进测试——pywebview 装配+窗口导航回调） |
| `tests/` | 无头测试（禁开窗口）：配置/决策/装配/静态壳/桥/活体重启/双实例联调 |
| `packaging/` | AppImage/deb 打包面骨架（未冒烟——诚实标注） |

## 运行与测试

```bash
# 环境引导（唯一正确建法——一次性；前置 sudo apt install python3-gi gir1.2-webkit2-4.1）
# 为什么不能裸 uv sync：窗口后端 gi（PyGObject）仅系统 Python 3.12 可用（PyPI
# 只发 sdist），venv 须 --system-site-packages 基于系统解释器建——裸 sync 自建
# 的 venv 开关=false，gi 不可见，启动即"QT or GTK ..."失败（bootstrap.sh 头注同口径）
cd desktop && ./bootstrap.sh

# 测试（无头——窗口面永不 create window）
cd desktop && uv run pytest

# 桌面应用
cd desktop && uv run python -m waterprint_desktop.main
```

注：uv 路径依赖为非 editable 快照安装——server/core 改动后须
`uv sync --reinstall-package waterprint-server --reinstall-package waterprint-core`
刷新再跑测试（architecture §4.1 同族注记；日常 uv sync 不会动 venv 开关，
venv 被删后重跑 bootstrap.sh 而非裸 sync）。

## 三角色模型（ADR-028）

| 角色 | 引擎 | UI | 联机 |
|---|---|---|---|
| unconfigured（首启） | 不起 | 静态壳 8620（向导三选） | — |
| standalone 单机 | 127.0.0.1:8621 | 引擎 origin 同源 | 无 |
| server 服务端 | 0.0.0.0:8621+token 强制 | 引擎 origin 同源 | 局域网配对 |
| client 客户端 | 不起 | 静态壳 8620 | API 全走远程 |

- 配置：`~/.config/waterprint/desktop.json`（env `WATERPRINT_DESKTOP_CONFIG`
  覆盖）；数据基点 `~/.local/share/waterprint`（env
  `WATERPRINT_DESKTOP_DATA_DIR` 覆盖）；webapp 产物根缺省=仓库
  `webapp/dist`（env `WATERPRINT_DESKTOP_WEBAPP_DIST` 覆盖）。
- 端口：壳 8620=server CORS 缺省白名单约定值（b5/b6 契约——两面同批
  冻结，改端口须同批改 server settings 缺省）；引擎缺省 8621
  （`WATERPRINT_PORT` 可覆盖）。
- 分层执法：依赖边恰两条（→waterprint_server.main/settings，
  structure-graph §1b）；真实 import ⊆ 边声明由 check_module_graph
  机器强制（desktop 不另设 import-linter 契约——单消费面包）。

## 打包面（诚实标注：未冒烟）

`packaging/` 提供 AppImage/deb 骨架脚本与桌面文件；**从未在干净环境
端到端冒烟**（ODA AppImage 冒烟挂账先例同款口径）——打包批工作项见
`packaging/README.md`。
