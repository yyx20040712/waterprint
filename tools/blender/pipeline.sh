#!/usr/bin/env bash
# 模板资产管线一键编排（tools/blender/README.md 工序表——批3 主体）。
# 用法：bash tools/blender/pipeline.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-D:/blender5.0/blender.exe}"
WEBAPP="$(cd "$HERE/../.." && pwd)/webapp"
FAMILY="clarifier_radial"

echo "== 1/5 建模（水密快检+AABB 对拍——违例中止）"
"$BLENDER" -b --factory-startup -P "$HERE/build_clarifier_radial.py"
echo "== 2/5 glb 导出"
"$BLENDER" -b --factory-startup -P "$HERE/export_glb.py"
echo "== 3/5 meshopt 压缩（勿 optimize——节点合并毁 inst 原型 TRS）"
cd "$WEBAPP"
npx gltf-transform meshopt "$HERE/build/$FAMILY.raw.glb" "$HERE/build/$FAMILY.meshopt.glb"
echo "== 4/5 缩略图出图（Eevee 512² 透明底/50mm）"
"$BLENDER" -b --factory-startup -P "$HERE/render_thumb.py"
echo "== 5/5 调色板量化+资产落位"
python - "$HERE/build/$FAMILY.png" "$WEBAPP/public/assets/units/$FAMILY.png" <<'PY'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
Image.open(src).quantize(colors=256, method=Image.FASTOCTREE).save(dst, optimize=True)
PY
cp "$HERE/build/$FAMILY.meshopt.glb" "$WEBAPP/public/assets/units/$FAMILY.glb"
ls -la "$WEBAPP/public/assets/units/"
echo "== 完成（预算面：glb ≤150KB / PNG ≤80KB / tri ≤8k——check_templates.mjs 复验）"
