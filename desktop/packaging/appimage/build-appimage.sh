#!/usr/bin/env bash
# AppImage 构建骨架（联机第七批 b7——诚实标注：未冒烟）
#
# 形态参照：linuxdeploy AppDir 布局 + AppRun 包装 python 入口。
# 本脚本当前只装配目录骨架并打印 TODO 清单即退出（不产出可运行
# AppImage）——打包批工作项见 packaging/README.md。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
APPDIR="${1:-${REPO_ROOT}/desktop/packaging/appimage/AppDir}"

mkdir -p "${APPDIR}/usr/bin" \
         "${APPDIR}/usr/share/waterprint/webapp-dist" \
         "${APPDIR}/usr/share/waterprint/data" \
         "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

cp "${REPO_ROOT}/desktop/packaging/appimage/waterprint-desktop.desktop" \
   "${APPDIR}/usr/share/applications/"

echo "[骨架] AppDir 就位：${APPDIR}"
cat <<'TODO'
[TODO 打包批工作项——未冒烟]
1. venv/wheel 集装配（uv export 或 uv build 产物 + PyPI 离线镜像面）
2. webapp dist 装配：pnpm -C webapp build → usr/share/waterprint/webapp-dist
3. 数据包装配：data/ 五目录 → usr/share/waterprint/data
4. AppRun 包装脚本：设 WATERPRINT_DESKTOP_WEBAPP_DIST /
   WATERPRINT_DATA_DIR / WATERPRINT_DESKTOP_CONFIG ·
   WATERPRINT_DESKTOP_DATA_DIR 指向 AppDir 布局后 exec python -m
   waterprint_desktop.main
5. webkit2gtk 依赖面（bundle 携带或系统依赖声明）
6. linuxdeploy --appimage-extract-and-run 产出与干净环境冒烟
TODO
exit 3  # 骨架态显式非成功退出（防误当可发布产物）
