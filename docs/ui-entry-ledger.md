# UI 入口与按钮清点账（V-3 销项——b3-20261010 入口与按钮清点批）

> **生成性质=人工清点账（非机检生成物）**：源=.workflow/b3-prep-20261009/
> inventory.md（主轨 Explore 只读探查四组），B3 批逐项复核落账；行号以
> B3 开工 HEAD（2927a928a77）实测为准，prep 期行号漂移已勘正（勘正处
> 备注「行勘正」）。本账=V-3「全量清点+旧入口退役」销项件——后续批
> 的 legacy 物理删除以本账「退役行」为清单（B3 边界裁定：legacy 面
> 冻结零触碰，v4 承载全部「迁」类功能后，删除=用户终验后续批）。
>
> 列：入口 id｜源组件:行（HEAD 实测）｜去向（迁=v4 锚〔testid〕/R=退役）
> ｜测试引用与同步态｜备注。测试同步态口径：legacy 件测试**随物理删除
> 批同步退役**（B3 冻结不动——在场=正常绿，非欠账）；v4 侧新锚测试在
> 本批 U4/U5 落位。

## 组1 Ribbon 族（legacy 顶栏——App.tsx:404 挂载）

| 入口 id | 源组件:行 | 去向 | 测试引用与同步态 | 备注 |
|---|---|---|---|---|
| wp-ribbon-run「全项目计算」主钮 | ribbon.tsx:385（Dropdown.Button 364-393） | 迁=zoneBand wp-v4-run〔zoneBand.tsx:315〕 | ribbon.test.tsx（15 例）在场 | decideRunCalc 复用导入（M1 件零改） |
| 菜单「单元枚举…」（unit-enum） | ribbon.tsx:370 | 迁=enumerateModal wp-v4-enumerate-modal〔enumerateModal.tsx:152〕 | ribbon.test.tsx:176-230 在场 | ⟳唯一入口=solutionCards wp-v4-reenumerate:276；提交钮=EnumerateBar「提交枚举」enumerateBar.tsx:102（行勘正：prep 记 96） |
| 菜单「联合枚举…」（joint-enum）+Modal | ribbon.tsx:371（Modal 463-472） | 迁=designZone wp-v4-joint-open〔designZone.tsx——B3 U2 补面〕+wp-v4-joint-modal 承载 JointSubmitForm 复用件 | ribbon.test.tsx/JointSolutionsPanel.test.tsx/jointSolutionCards.test.tsx 在场 | 提交钮「提交联合枚举」jointSolutions.tsx:117；提交回路零新写（useRunJointEnumeration 单源） |
| wp-ribbon-validate「校验」 | ribbon.tsx:419 | 迁=zoneBand wp-v4-validate〔zoneBand.tsx:300〕 | ribbon.test.tsx:157-162 在场 | Popover 报告→v4 message 即时反馈（B2 挂账收口） |
| wp-ribbon-export+菜单两锚（total-dxf/open-pane） | ribbonExportMenu.tsx:122/130/136 | 迁=draftingZone ExportButton 复用〔draftingZone.tsx:105〕+树导航 | ribbon.test.tsx:232-278 在场 | 导出域=制图区（v4-2 终裁） |
| wp-ribbon-viewer3d「三维快访」 | ribbon.tsx:454（行勘正：prep 记 453-460 区段） | 迁=zoneBand 页签 wp-v4-zone-viewer3d | ribbon.test.tsx:157-162,275 在场 | viewer3dZone 全幅 |
| wp-open-manager-header「项目管理」 | App.tsx:413 | 迁=projectsZone wp-v4-proj-open-*〔projectsZone.tsx:156〕 | projectManagerModal.test.tsx 在场（复用件内核） | 新建/导入/复制/重命名四动作齐 |
| AiConnectButton「AI 接入」 | App.tsx:415 | 迁=dockBar AI 窗头行〔dockBar.tsx——B3 U3 补面〕 | AiConnectButton.test.tsx/AiConnectModal.test.tsx 在场（共享件） | 共享件 import 复用零改 |
| 「连接设置」钮（SettingOutlined） | App.tsx:418-424 | 迁=dockBar wp-v4-open-settings〔dockBar.tsx——B3 U3 补面〕 | tokenSettings 语义面由 dockBar 新测试承载（U5） | TokenSettingsModal 共享件复用；AUTH_EVENT 401 自愈 parity |

## 组2 AI 席位三分页（aiSeat.tsx——App.tsx:549-553 data-region=ai-seat）

| 入口 id | 源组件:行 | 去向 | 测试引用与同步态 | 备注 |
|---|---|---|---|---|
| Segmented 三分页（对话/任务/回执） | aiSeat.tsx:104-110 | 对话=迁 dockBar AiDockWindow（wp-v4-ai-input:117/send:141/log:101）；任务=迁 TaskStrip（wp-v4-task-row:227）；回执=R（见下） | aiSeat.test.tsx（15）/seatTaskPage.test.tsx（15）/seatReceipts.test.tsx（8）在场 | v4 形态=凝缩窗+窄任务条（B1 视觉微裁决） |
| 连接徽标 wp-seat-conn | aiSeat.tsx:97 | **R**（B3 裁定——v4 dockBar 会话状态行承载：AI 接入钮+发送态+会话错误行） | aiSeat.test.tsx 相关例在场 | 已接入/未接入 Tag 语义归 AiConnectModal 状态列表 |
| 任务页 ops 折叠段 wp-seat-ops | seatTaskPage.tsx:164（+features/solutions/components/TaskPanel.tsx:143） | **R**（B3 裁定——v4 凝缩任务条承载：进度+状态+失败错误行） | seatTaskPage.test.tsx 相关例在场 | 深读面不迁（凝缩形终裁） |
| 回执页整面 | seatReceipts.tsx（SeatReceipts 组件） | **R**（写通道未接=交接遗留——store 状态机占位） | seatReceipts.test.tsx（8 例）在场 | B1 已裁「回执页退役=B3」——本账销项 |
| 回执三钮 确认/拒绝/撤销 | seatReceipts.tsx:88-98（行勘正：prep 记 87-97） | **R**（同上） | seatReceipts.test.tsx:70-120 在场 | 动作真执行体=store 注释占位（原件头注自述） |

## 组3 单元库列（unitLibrary.tsx——App.tsx:445-449 data-region=unit-library）

| 入口 id | 源组件:行 | 去向 | 测试引用与同步态 | 备注 |
|---|---|---|---|---|
| 搜索框 | unitLibrary.tsx:227-233 | **R**（B1 已改 hierarchicalCatalog 右键分级目录取代整面） | unitLibraryTree.test.ts 在场 | 已迁行：wp-v4-catalog/-level1/-level2〔hierarchicalCatalog.tsx:83/85/99〕 |
| 树叶行「＋」添加钮 | unitLibrary.tsx:184（行勘正：prep 记 173-186 区段） | **R**（同上——右键目录落点取代） | unitLibraryTree.test.ts 在场 | useAddUnitToCanvas 单源两消费点之一（legacy 侧冻结） |
| 错误「重试」钮 | unitLibrary.tsx:208-209 | **R**（同上） | unitLibraryTree.test.ts 在场 | 取数三态面随整面退役 |
| 计数条（N 单元/M 组） | unitLibrary.tsx:260-277 | **R**（同上） | catalogCategories.test.ts 在场 | 目录数据面由 catalog 单源承接 |
| 详情「添加到画布」主钮 | unitDetailPanel.tsx:276 | **R**（B3 裁定——v4 无 Settings 详情窗） | unitDetailPanel.test.tsx 在场 | 画布添加=右键目录（thumbnailFlow） |
| 详情「到工艺画布」钮 | unitDetailPanel.tsx:287 | **R**（同上） | unitDetailPanel.test.tsx 在场 | 导航=zone 切换（v4 zoneBand） |
| 详情「✕」解除钮 | unitDetailPanel.tsx（Drawer 关闭钮） | **R**（同上） | unitDetailPanel.test.tsx 在场 | 解除三通道语义随 Drawer 退役 |

## 组4 画布编辑工具条（canvasEditToolbar.tsx——legacy 画布槽）

| 入口 id | 源组件:行 | 去向 | 测试引用与同步态 | 备注 |
|---|---|---|---|---|
| 「编辑」钮（只读态） | canvasEditToolbar.tsx:148（行勘正：prep 记 139-149 区段） | **R**（B3 裁定——v4 无编辑模式终态，plan 终裁） | canvasEditToolbar.test.ts 在场 | thumbnailFlow raw 就绪自动 beginEdit |
| 「退出编辑」+Popconfirm | canvasEditToolbar.tsx:86-98 | **R**（同上） | canvasEditToolbar.test.ts 在场 | 误退护语义随编辑态退役 |
| 「保存」钮（带徽标） | canvasEditToolbar.tsx:101-136 | **R**（同上） | canvasEditToolbar.test.ts 在场 | v4 保存=zoneBand wp-v4-save〔zoneBand.tsx:268〕手动通道 |

## 组5 新结构面已在钮（v4——本账「去向」目标面基准，B3 实测复核）

| 入口 id | 源组件:行 | 状态 | 测试引用 | 备注 |
|---|---|---|---|---|
| wp-v4-save/undo/redo/validate/run | zoneBand.tsx:268/281/291/300/315 | 在场 | zoneBand 面归 shellV4 组测+probe-b1 | 撤销/重做=骨架禁用挂账 |
| wp-v4-enumerate-modal（EnumerateBar 承载） | enumerateModal.tsx:152 | 在场 | probe-b1 M 族+U4 结构锚（本批） | ⟳=枚举唯一提交入口 |
| wp-v4-reenumerate | solutionCards.tsx:276 | 在场 | solutionCards.test.tsx+U4 结构锚 | 开枚举 Modal 唯一触发 |
| wp-v4-joint-open+wp-v4-joint-modal | designZone.tsx（B3 U2 补面） | **本批新增** | U4 结构锚+U5 组件测+probe-b3 M0/M3 | 联合枚举唯一提交入口 |
| wp-v4-ai-input/send/log | dockBar.tsx:117/141/101 | 在场 | dockBar.test.tsx | AI 唯一窗凝缩形 |
| wp-v4-task-row/error | dockBar.tsx:227/290 | 在场 | dockBar.test.tsx | 任务凝缩条 |
| wp-v4-open-settings+wp-ai-connect-open | dockBar.tsx（B3 U3 补面） | **本批新增** | U5 组件测+probe-b3 M1/M2 | AUTH_EVENT 401 自愈 parity |
| wp-v4-catalog/-level1/-level2 | hierarchicalCatalog.tsx:83/85/99 | 在场 | unitLibraryTree.test.ts（目录纯函数面） | 组3 整面的取代面 |
| wp-v4-proj-open-* | projectsZone.tsx:156 | 在场 | projectManagerModal.test.tsx（复用内核） | 项目管理迁入 |
| ParamForm「提交重算」三式 | ParamForm（复用件——检查器底钮） | 在场 | paramFormThreeWay.test.tsx | 复用零改 |
| wp-v4-report-rerun/nav/export 三钮 | reportZone.tsx:118/345/55-57 | 在场 | reportZone.test.tsx | B6 实装 |
| wp-v4-drafting-{siteplan,profile,process}+back-sheets | draftingZone.tsx:274/205 | 在场 | probe-b1/B4 面探针 | 制图域入口 |
| 「任务 ▴」状态条入口 | shellV4.tsx:210 | 在场 | probe-b1 | 非 design 区 dock 收起入口 |
| 分析面入口 5 钮 | designZone.tsx:370-390 | 在场 | probe-b2 M8 | 全厂页→分析表 |

## B3 裁定落账（任务书 §三.U1 裁定表逐项）

| 裁项 | B3 处置 | 落点 |
|---|---|---|
| 联合枚举轨（新/裁） | **迁** | U2 补面 wp-v4-joint-open+wp-v4-joint-modal（designZone） |
| AiConnectButton/连接设置（新/裁） | **迁** | U3 补面 dockBar AI 窗头行（wp-v4-open-settings+wp-ai-connect-open） |
| 连接徽标 wp-seat-conn（裁） | **R** | v4 dockBar 会话状态行承载（组2 行） |
| 任务页 ops 折叠段（裁） | **R** | v4 凝缩任务条承载（组2 行） |
| canvasEditToolbar 两态（裁） | **R** | v4 无编辑模式终态——plan 终裁（组4 行） |
| unitDetailPanel 详情三钮（裁） | **R** | v4 无 Settings 详情窗（组3 行） |
| 单元库列整面（R/裁） | **R** | B1 hierarchicalCatalog 右键目录已迁取代（组3 行） |
| 回执页/回执三钮（R） | **R** 沿册 | 写通道未接=交接遗留（组2 行） |

## 退役行清单口径（后续批消费）

上表「R」行=legacy 物理删除候选全集（用户终验后后续批执行）；删除批
须同批退役对应 legacy 测试件（本账「测试引用」列即清单）并回读本账
销项。v4 侧「迁」行全部落锚后，本账由 B3 收口（V-3 销项）。
