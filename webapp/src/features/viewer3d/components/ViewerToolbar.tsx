/**
 * 三维视图工具条（ENG6 preset 按钮组+图层开关面+剖切入口——Canvas 前兄弟元素）。
 *
 * 输入:  viewer3dStore（cameraPreset/四图层显隐/剖切 enabled+height——纯
 *        view 态直连，零业务数据）+可选 clippingMaxHeight（取景 bounds
 *        高度——Scene effective bounds 派生，F5 D1 同源）
 * 输出:  antd Space 工具条（当前 preset=primary 高亮[siteplan 工具栏
 *        先例]；图层=Checkbox 开关；F5 D3 剖切=Switch+高度 Slider
 *        [0..bounds 高度，步 0.5]——store 两动作 toggleClipping/
 *        setClippingHeight 唯一 UI 入口，probe.ts 半剖直驱面退役为验收位）
 *
 * 规格说明（批3 迭代二 2026-09-13 抽件——Scene.tsx 行数预算门 500；
 *   F5 D3 增剖切入口）：
 *   - preset 点击=store.cameraPreset 一次（CameraRig effect 落机位）；
 *     四字标签避 antd 两字插空格坑（教训 24）；
 *   - 图层开关面：store 三键本无 UI 调用方（交接所设「现有开关面」实
 *     不存在，同制补齐）+批3 迭代二新增草地共四层（用户批注 b-①
 *     草地可隐藏——Checkbox 无 Button 两字插空坑）；
 *   - 剖切（F5 D3）：开启且现行高度≤0 时滑移 glideHeight 半高默认
 *     （S5 半剖工况先例——0 高度全剖黑幕防线；两 store 动作组合调用，
 *     store 语义零改）；Slider 随关态禁用；bounds 高度≤0（空场景）
 *     时 Slider 禁用（无有效剖切域）。
 */
import { Button, Checkbox, Slider, Space, Switch } from "antd";

import { useViewer3dStore, type CameraPreset } from "../store/viewer3dStore";

const PRESETS: ReadonlyArray<readonly [CameraPreset, string]> = [
  ["iso", "等轴视角"],
  ["top", "俯视视角"],
  ["side", "侧视视角"],
];

/** 开启滑移默认高度：max 四舍五入取半（S5 半剖先例——步 0.5 网格值）。 */
export function glideHeight(maxHeight: number): number {
  return Math.round(maxHeight) / 2;
}

export function ViewerToolbar({
  clippingMaxHeight = 0,
}: {
  /** 剖切高度上限（取景 effective bounds 高度——空场景 0=禁用域）。 */
  clippingMaxHeight?: number;
}) {
  const cameraPreset = useViewer3dStore((state) => state.cameraPreset);
  const setCameraPreset = useViewer3dStore((state) => state.setCameraPreset);
  const showGrass = useViewer3dStore((state) => state.showGrass);
  const showWater = useViewer3dStore((state) => state.showWater);
  const showInternals = useViewer3dStore((state) => state.showInternals);
  const showAnnotations = useViewer3dStore((state) => state.showAnnotations);
  const toggleLayer = useViewer3dStore((state) => state.toggleLayer);
  const clippingEnabled = useViewer3dStore((state) => state.clippingEnabled);
  const clippingHeight = useViewer3dStore((state) => state.clippingHeight);
  const toggleClipping = useViewer3dStore((state) => state.toggleClipping);
  const setClippingHeight = useViewer3dStore((state) => state.setClippingHeight);
  const layers = [
    ["grass", "草地", showGrass],
    ["water", "水面", showWater],
    ["internals", "内部构件", showInternals],
    ["annotations", "标注", showAnnotations],
  ] as const;
  const sliderMax = clippingMaxHeight > 0 ? clippingMaxHeight : 1;
  return (
    <Space size="small" wrap style={{ padding: "4px 0", rowGap: 4 }}>
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
      {/* F5 D3：剖切入口（Switch+高度 Slider——store 两动作；
          bounds 高度上限由 Scene effective bounds 传入） */}
      <Switch
        size="small"
        checked={clippingEnabled}
        checkedChildren="剖切"
        unCheckedChildren="剖切"
        aria-label="剖切开关"
        onChange={() => {
          toggleClipping();
          if (!clippingEnabled && clippingHeight <= 0 && clippingMaxHeight > 0) {
            setClippingHeight(glideHeight(clippingMaxHeight));
          }
        }}
      />
      <Slider
        style={{ width: 120, minWidth: 120, margin: 0 }}
        min={0}
        max={sliderMax}
        step={0.5}
        value={Math.min(clippingHeight, sliderMax)}
        disabled={!clippingEnabled || clippingMaxHeight <= 0}
        onChange={(value) => setClippingHeight(value as number)}
        aria-label="剖切高度"
      />
    </Space>
  );
}
