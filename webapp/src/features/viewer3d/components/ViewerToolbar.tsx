/**
 * 三维视图工具条（ENG6 preset 按钮组+图层开关面——Canvas 前兄弟元素）。
 *
 * 输入:  viewer3dStore（cameraPreset/四图层显隐——纯 view 态直连，
 *        零 props 零业务数据）
 * 输出:  antd Space 工具条（当前 preset=primary 高亮[siteplan 工具栏
 *        先例]；图层=Checkbox 开关）
 *
 * 规格说明（批3 迭代二 2026-09-13 抽件——Scene.tsx 行数预算门 500）：
 *   - preset 点击=store.cameraPreset 一次（CameraRig effect 落机位）；
 *     四字标签避 antd 两字插空格坑（教训 24）；
 *   - 图层开关面：store 三键本无 UI 调用方（交接所设「现有开关面」实
 *     不存在，同制补齐）+批3 迭代二新增草地共四层（用户批注 b-①
 *     草地可隐藏——Checkbox 无 Button 两字插空坑）。
 */
import { Button, Checkbox, Space } from "antd";

import { useViewer3dStore, type CameraPreset } from "../store/viewer3dStore";

const PRESETS: ReadonlyArray<readonly [CameraPreset, string]> = [
  ["iso", "等轴视角"],
  ["top", "俯视视角"],
  ["side", "侧视视角"],
];

export function ViewerToolbar() {
  const cameraPreset = useViewer3dStore((state) => state.cameraPreset);
  const setCameraPreset = useViewer3dStore((state) => state.setCameraPreset);
  const showGrass = useViewer3dStore((state) => state.showGrass);
  const showWater = useViewer3dStore((state) => state.showWater);
  const showInternals = useViewer3dStore((state) => state.showInternals);
  const showAnnotations = useViewer3dStore((state) => state.showAnnotations);
  const toggleLayer = useViewer3dStore((state) => state.toggleLayer);
  const layers = [
    ["grass", "草地", showGrass],
    ["water", "水面", showWater],
    ["internals", "内部构件", showInternals],
    ["annotations", "标注", showAnnotations],
  ] as const;
  return (
    <Space size="small" wrap style={{ padding: "4px 0" }}>
      {PRESETS.map(([value, label]) => (
        <Button
          key={value}
          size="small"
          type={cameraPreset === value ? "primary" : "default"}
          onClick={() => setCameraPreset(value)}
        >
          {label}
        </Button>
      ))}
      {layers.map(([layer, label, checked]) => (
        <Checkbox key={layer} checked={checked} onChange={() => toggleLayer(layer)}>
          {label}
        </Checkbox>
      ))}
    </Space>
  );
}
