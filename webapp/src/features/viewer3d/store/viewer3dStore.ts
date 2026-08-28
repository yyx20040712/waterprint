/**
 * 三维视图 slice：相机/剖切/显示开关（FE1 v1 最小集）。
 *
 * 输入:  视图动作（setCameraPreset/toggleClipping/setClippingHeight/toggleLayer）
 * 输出:  useViewer3dStore（zustand——纯 view 态，禁业务数据，§12.3）
 *
 * 规格说明（FE1 实装 v1）：
 *   - 剖切 clipping plane 参数（enabled+height——Y-up 高度面）与相机位姿
 *     属 view 态，不入 URL/项目文件；
 *   - 显示开关=图层级（水面/内部构件/标注）——渲染密度控制；
 *   - 禁业务字段（工况/尺寸等数据一律走 useSceneQuery 数据通道）。
 */
import { create } from "zustand";

export type CameraPreset = "iso" | "top" | "side";

export type Viewer3dLayer = "water" | "internals" | "annotations";

type Viewer3dState = {
  cameraPreset: CameraPreset;
  clippingEnabled: boolean;
  clippingHeight: number;
  showWater: boolean;
  showInternals: boolean;
  showAnnotations: boolean;
  setCameraPreset: (preset: CameraPreset) => void;
  toggleClipping: () => void;
  setClippingHeight: (height: number) => void;
  toggleLayer: (layer: Viewer3dLayer) => void;
};

export const useViewer3dStore = create<Viewer3dState>((set) => ({
  cameraPreset: "iso",
  clippingEnabled: false,
  clippingHeight: 0,
  showWater: true,
  showInternals: true,
  showAnnotations: true,
  setCameraPreset: (preset) => set({ cameraPreset: preset }),
  toggleClipping: () => set((state) => ({ clippingEnabled: !state.clippingEnabled })),
  setClippingHeight: (height) => set({ clippingHeight: height }),
  toggleLayer: (layer) =>
    set((state) => ({
      showWater: layer === "water" ? !state.showWater : state.showWater,
      showInternals: layer === "internals" ? !state.showInternals : state.showInternals,
      showAnnotations: layer === "annotations" ? !state.showAnnotations : state.showAnnotations,
    })),
}));
