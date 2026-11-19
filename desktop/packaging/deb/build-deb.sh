#!/usr/bin/env bash
# deb 构建骨架（联机第七批 b7——诚实标注：未冒烟）
#
# 形态参照：dpkg-deb 布局（DEBIAN/control + usr/ 树）。本脚本当前只
# 装配目录骨架并打印 TODO 清单即退出（不产出可安装 deb）——打包批
# 工作项见 packaging/README.md。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKGROOT="${1:-${REPO_ROOT}/desktop/packaging/deb/pkgroot}"

mkdir -p "${PKGROOT}/DEBIAN" \
         "${PKGROOT}/usr/bin" \
         "${PKGROOT}/usr/share/waterprint/webapp-dist" \
         "${PKGROOT}/usr/share/waterprint/data"

cp "${REPO_ROOT}/desktop/packaging/deb/control" "${PKGROOT}/DEBIAN/control"

echo "[骨架] deb 布局就位：${PKGROOT}"
cat <<'TODO'
[TODO 打包批工作项——未冒烟]
1. venv/wheel 集装配（uv export requirements 安装到 /usr/share/waterprint/venv
   或系统 python3 包形态待定）
2. webapp dist + 数据包五目录装配
3. /usr/bin/waterprint-desktop 包装脚本（env 布局钉死：
   WATERPRINT_DESKTOP_WEBAPP_DIST / WATERPRINT_DATA_DIR）
4. dpkg-deb --build + 干净环境安装冒烟（首启三选→三角色切换→局域网双机配对）
TODO
exit 3  # 骨架态显式非成功退出（防误当可发布产物）
