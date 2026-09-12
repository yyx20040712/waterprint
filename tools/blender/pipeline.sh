#!/usr/bin/env bash
# 模板资产管线一键编排（tools/blender/README.md 工序表——批3 主体；
# 段二 family 参数化：用法 bash pipeline.sh [family ...]——缺省
# clarifier_radial[辐流已冻结资产——非必要不重跑]；build 脚本名=族名
# 映射（aao_corridor→build_aao.py / cass_batch→build_cass.py）。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-D:/blender5.0/blender.exe}"
WEBAPP="$(cd "$HERE/../.." && pwd)/webapp"

build_script() {
  case "$1" in
    clarifier_radial) echo "build_clarifier_radial.py" ;;
    aao_corridor) echo "build_aao.py" ;;
    cass_batch) echo "build_cass.py" ;;
    *) echo "未知族：$1（合法 clarifier_radial|aao_corridor|cass_batch）" >&2; exit 2 ;;
  esac
}

FAMILIES="${*:-clarifier_radial}"
for FAMILY in $FAMILIES; do
  echo "== [$FAMILY] 1/5 建模（水密快检+AABB 对拍——违例中止）"
  "$BLENDER" -b --factory-startup -P "$HERE/$(build_script "$FAMILY")"
  echo "== [$FAMILY] 2/5 glb 导出"
  FAMILY="$FAMILY" "$BLENDER" -b --factory-startup -P "$HERE/export_glb.py"
  echo "== [$FAMILY] 3/5 meshopt 压缩（勿 optimize——节点合并毁 inst 原型 TRS）"
  (cd "$WEBAPP" && npx gltf-transform meshopt "$HERE/build/$FAMILY.raw.glb" "$HERE/build/$FAMILY.meshopt.glb")
  echo "== [$FAMILY] 4/5 缩略图出图（Eevee 512² 透明底/50mm）"
  FAMILY="$FAMILY" "$BLENDER" -b --factory-startup -P "$HERE/render_thumb.py"
  echo "== [$FAMILY] 5/5 调色板量化+资产落位"
  python - "$HERE/build/$FAMILY.png" "$WEBAPP/public/assets/units/$FAMILY.png" <<'PY'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
Image.open(src).quantize(colors=256, method=Image.FASTOCTREE).save(dst, optimize=True)
PY
  cp "$HERE/build/$FAMILY.meshopt.glb" "$WEBAPP/public/assets/units/$FAMILY.glb"
done
ls -la "$WEBAPP/public/assets/units/"
echo "== 完成（预算面：glb ≤150KB / PNG ≤80KB / tri ≤8k——check_templates.mjs 复验）"
