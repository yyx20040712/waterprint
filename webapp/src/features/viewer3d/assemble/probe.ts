/**
 * viewer3d 探针面（批3 主体——验收可观测）。
 *
 * 输入:  模块加载（Scene onCreated 前注册——单例幂等）
 * 输出:  window.__probe.viewer3d = { templates, fallbacks, thumbnailFallbacks,
 *        glInfo }——验收脚本/测试读数
 *
 * 规格说明（S9 probe 增降级计数；P7 登记面；drawcalls 验收 ≤120——
 *   glInfo.render.calls=最近一帧读数）。探针只读聚合零业务逻辑
 *   （生产路径零消费——仅观测面）。
 */

import { fallbackEntries } from "./fallbackLog";
import { thumbnailCounters } from "./thumbSource";
import { useViewer3dStore } from "../store/viewer3dStore";

/** 模板实例计数（UnitTemplateInstance 挂载/降级递增——验收读数）。 */
export const templateCounters = { rendered: 0, fallbackBoxes: 0 };

export type Viewer3dProbe = {
  templates: typeof templateCounters;
  fallbacks: () => ReturnType<typeof fallbackEntries>;
  thumbnailFallbacks: typeof thumbnailCounters;
  glInfo: { render: { calls: number; triangles: number } } | null;
  /** 验收驱动位（§12.3 剖切无 UI 控件——S5 半剖工况探针直驱 store）。 */
  setClipping: (enabled: boolean, height: number) => void;
};

declare global {
  interface Window {
    __probe?: Record<string, unknown>;
  }
}

let registered = false;

/** 注册探针（幂等——dev/test 皆安全挂载）。 */
export function registerProbe(): void {
  if (registered) {
    return;
  }
  registered = true;
  const w = window as Window & { __probe?: Record<string, unknown> };
  w.__probe = w.__probe ?? {};
  const probe: Viewer3dProbe = {
    templates: templateCounters,
    fallbacks: fallbackEntries,
    thumbnailFallbacks: thumbnailCounters,
    glInfo: null,
    setClipping: (enabled: boolean, height: number) => {
      useViewer3dStore.setState({ clippingEnabled: enabled, clippingHeight: height });
    },
  };
  (w.__probe as Record<string, unknown>).viewer3d = probe;
}

/** 挂载渲染器信息（Scene Canvas onCreated——drawcalls 读数位）。 */
export function attachGlInfo(gl: {
  info: { render: { calls: number; triangles: number } };
}): void {
  registerProbe();
  const w = window as Window & { __probe?: { viewer3d?: Viewer3dProbe } };
  const probe = w.__probe?.viewer3d;
  if (probe !== undefined) {
    probe.glInfo = gl.info as Viewer3dProbe["glInfo"];
  }
}
