# ADR-028：桌面壳（pywebview）与联机三角色装配

- 状态：已接受（2026-11-19，联机架构第七批 b7——用户裁决模型在案）
- 关联：ADR-027（agent 面本地化）；architecture §4.1 安全红线（token）；
  联机第五批（/api/runtime「绑定地址即角色」+desktopBridge 契约冻结）、
  第六批（厚客户端通路+WATERPRINT_ALLOWED_ORIGINS CORS 面）；
  批准稿 `frontend-redesign/onboarding.html`、`connection.html`

## 背景与决策

联机架构前六批落完 webapp 与 server 两侧通路（版本握手/厚客户端基址
切换/配对卡），第七批落**桌面壳本体**：一个安装包永远全量
（core+server+webapp 构建+壳），联机由两级开关在三种角色间切换——

| 角色 | 引擎 | UI 装载 | 联机面 |
|---|---|---|---|
| 单机 standalone | 本地引擎 127.0.0.1:8621 | 引擎 origin（UI 与 API 同源） | 无 |
| 服务端 server | 本地引擎照常，0.0.0.0+token 强制 | 引擎 origin（同上） | 局域网客户端配对连接 |
| 客户端 client | **不起引擎** | 本地静态壳 127.0.0.1:8620 | API 全走远程（b6 通路） |

决策要点：

1. **窗口技术=pywebview**（js_api 桥直投 Python 对象；Linux 后端
   webkit2gtk）。备选 Electron/Tauri 弃——引入第二 Node 工具链/第二前端
   构建面，与既有 pnpm+vite 单前端栈冲突；pywebview 复用 webapp 构建产物
   零第二 UI 面。
2. **进程模型=单进程多线程**：uvicorn `Server` 对象显式启停（不经
   `uvicorn.run` 子命令面——不抢信号处理），引擎与静态壳各一线程句柄
   （`server_thread.UvicornServeHandle`）；角色切换=活体重启（stop 旧
   句柄→按新方案 start），窗口主线程不受影响。引擎角色间切换必经重启
   （uvicorn 绑定 start 期固化——127.0.0.1↔0.0.0.0 换绑定无法热改）。
3. **绑定面=角色派生单源**：联机第五批「role=绑定地址即角色」的逆命
   题在壳侧成立——角色配置（desktop.json）是绑定与 token 门槛的唯一
   真源，`WATERPRINT_HOST` 在壳内被忽略（防双真源打架）；其余 env 通道
   （数据包根/端口/CORS）原样沿用。
4. **token 流程**：首次进入 server 角色时 `secrets.token_hex(16)`（32
   位 hex，≥16 红线一倍余量）生成并持久化于 desktop.json，重启稳定
   （配对卡「服务端重启或重新生成前有效」语义）；注入沿 server 既有
   `WATERPRINT_API_TOKEN` 的 Settings 字段通道（kwarg=该通道程序面），
   **不造第二通道**；0.0.0.0+空 token 由 server Settings 构造即拒
   （R-6 机器防线复用非重实现）。standalone/client 不消费 token。
5. **UI 装载选型 A（静态面挂 server app）**：standalone/server 角色
   把 webapp dist 以 `StaticFiles(html=True)` 挂引擎 app 的 "/"——
   `/api` 路由先注册先生效，UI 与 API 同源，零 CORS 依赖零反代件。
   弃选型 B（独立静态线程+反代语义）：多一个反代组件与端口，同源语义
   靠反代维护，复杂度无对价收益。客户端/引导态则是**纯静态壳**
   （Starlette 仅 StaticFiles，零 waterprint_server import——「本地不
   起引擎」由 import 面结构保证，check_module_graph 真实 import 扫描
   强制）。
6. **端口约定**：静态壳 127.0.0.1:8620（=server CORS 缺省白名单
   `WATERPRINT_ALLOWED_ORIGINS` 约定值——客户端模式跨 origin 通道即
   此端口，两面同批冻结）；引擎缺省 8621（8620 相邻+1；8000 留给裸机
   dev server），`WATERPRINT_PORT` 可覆盖。
7. **桥契约**（Python 实现对齐 webapp `desktopBridge.ts` 冻结类型）：
   `setNetworkRole(role)->{ok,restartRequired}`——ok+restartRequired=
   false=活体重启已在本调用内完成；ok=false+restartRequired=true=装配
   失败但配置已持久化（下次应用启动按新角色装配，诚实信号）；b7 扩
   联合成员 `"client"`（首启三选需要，签名形状不变）；新增
   `getConfig()->{role,shellOrigin,engineOrigin}`（unconfigured=首启
   向导注入态）。桥方法名 camelCase（pywebview js_api 按名直投）。
8. **首启向导**：desktop 壳以「角色未配置」态启动（静态壳 8620 供 UI，
   不起引擎），webapp `OnboardingGate` 探测桥 getConfig().role==
   unconfigured 时渲染三选遮罩（批准稿 onboarding.html：单机/服务端/
   客户端+厚客户端说明）；选择落地经 setNetworkRole，单机/服务端由壳
   窗口导航至引擎 origin，客户端转第二步内嵌既有 ClientConnectionPanel。
   桥缺席（浏览器态）/getConfig 失败=不拦壳诚实降级。
9. **测试红线**：pywebview 窗口装配是薄 main 层不进测试（前台焦点
   红线——测试禁开任何窗口）；逻辑层（配置/决策/装配/静态服务/桥）全部
   无头测试，冒烟起 uvicorn/静态壳后台线程但不 create window；窗口本体
   真实验证=用户手测。
10. **配置与数据面**：desktop.json=~/.config/waterprint/desktop.json
    （env WATERPRINT_DESKTOP_CONFIG 覆盖；UTF-8+原子写+schema_version
    判版）；项目/导出基点=~/.local/share/waterprint/{projects,exports}
    （env WATERPRINT_DESKTOP_DATA_DIR 覆盖——桌面 CWD 不可靠，server
    CWD 相对缺省不适用）；数据包根=仓库 data/ 包定位上溯（安装态经
    WATERPRINT_DATA_DIR 指向安装器布局——与 server 部署同通道）。

## 分层与执法面

- 节点=`waterprint_desktop`（L6 第三客户端，structure-graph §1a 生成
  面 FIXED_NODES）；依赖边恰两条（§1b）：→`waterprint_server.main`
  （create_app 消费）与→`waterprint_server.settings`（角色化覆写）。
- **不另设 import-linter 契约**：desktop 单消费面包，check_module_graph
  真实 import ⊆ §1b 边声明已机器强制（比 forbidden 契约更强且零配置）。
- grep 三查/模型代号/行数预算全域纳管（gate_patterns SCAN_DIRS/
  check_model_names/check_file_budgets 扩面，agent 纳管先例同款）；
  ruff 现行口径=desktop/pyproject 配置+本地 `uv run ruff check .`（已
  绿），check_ruff 三根扩面随锁面解锁批（锁面 test_check_ruff runs
  迭代器钉三根——b7 不解锁 core/tests）；desktop/tests 纳入 test-lock
  manifest（用户 2026-11-19 授权，[HUMAN-LOCK] 提交）。

## 放弃项与挂账

- **自动发现服务端**（配对卡「后续批提供」沿承）：不在本批。
- **token 重新生成入口**：本批只做生成与保管；重生成 UI 挂账。
- **打包面**：AppImage/deb 仅脚本骨架（desktop/packaging），**未冒烟**
  （ODA AppImage 冒烟挂账先例同款诚实标注）；Linux 窗口后置依赖
  webkit2gtk 的安装器集成为打包批工作。
- **客户端态回切单机/服务端的 UX**：经设置 Modal（读失败警示下开关仍
  可用——桥在场即可切换）；专用回切入口挂账。
- **CI 桌面套件 job**：desktop pytest 尚未入 CI workflow（本地
  `cd desktop && uv sync && uv run pytest` 口径先行），挂账下批。
- **uv 路径依赖快照陈旧坑**：desktop venv 的 waterprint-server 为非
  editable 拷贝安装（core 先例同族）——server 改动后须
  `uv sync --reinstall-package waterprint-server` 刷新再跑 desktop 测试。

## 后果

- 联机三级开关模型全链路闭环（server 角色面+b6 客户端通路+本批壳与
  首启向导）；一个安装包三形态，用户无需理解部署概念。
- webapp 桥契约自 b5 冻结后首次扩面（+client 联合成员+getConfig），
  两面（TS 类型/Python 实现）逐名对齐并有镜像测试互锚。
