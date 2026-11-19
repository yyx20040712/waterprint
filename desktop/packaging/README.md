# 打包面骨架（诚实标注：未冒烟）

> 联机第七批 b7（ADR-028）交付**骨架**——AppImage/deb 的脚本与元数据
> 形态参照；**从未在干净环境端到端构建/安装/运行冒烟**（repo 已有 ODA
> AppImage 冒烟挂账先例同款口径，architecture §6.1 在册）。打包批工作
> 项在此逐条挂账。

## 布局

| 件 | 形态 |
|---|---|
| `appimage/build-appimage.sh` | AppImage 构建骨架（linuxdeploy 预设——TODO 段为打包批工作项） |
| `appimage/waterprint-desktop.desktop` | 桌面入口文件（Desktop Entry） |
| `deb/control` | Debian control 骨架（依赖面占位） |
| `deb/build-deb.sh` | deb 构建骨架（dpkg-deb 布局装配——TODO 段为打包批工作项） |

## 打包批工作项（挂账）

1. **运行时集合装配**：venv（uv 导出 requirements 或 `uv build` wheel
   集）+ webapp dist（`pnpm -C webapp build` 产物）+ 数据包（`data/`
   五目录）+ TYPST/ODA 可选外挂（缺失=相应导出端点显式报错，非阻断）。
2. **env 布局钉死**：安装器须设 `WATERPRINT_DESKTOP_WEBAPP_DIST`/
   `WATERPRINT_DATA_DIR`/（可选）`WATERPRINT_DESKTOP_CONFIG`·
   `WATERPRINT_DESKTOP_DATA_DIR` 指向安装布局（桌面壳缺省=仓库开发态
   包定位，安装态不适用——engine.resolve_data_dir/static_shell.
   resolve_webapp_dist 注记）。
3. **Linux 窗口后置依赖**：webkit2gtk（Debian/Ubuntu：
   `python3-gi gir1.2-webkit2-4.1`）——AppImage 形态需随 bundle 携带
   或声明系统依赖；deb 形态入 Depends。
4. **干净环境冒烟**：构建→安装→首启三选→三角色切换→局域网双机配对
   （当前唯一验证=开发态无头测试+用户手测窗口面）。
5. **Windows/macOS 形态**：未立项（当前仅 Linux 骨架）。
