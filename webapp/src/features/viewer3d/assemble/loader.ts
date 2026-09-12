/**
 * 模板资产加载器（spec.md §9 预算注记/§11 P3 meshopt——批3 主体）。
 *
 * 输入:  registry 条目（glb 路径——public/assets 静态 fetch 非代码分包）
 * 输出:  LoadedTemplate（glTF scene+扫描面节点）——族级缓存 Promise
 *        （同族多实例单次解析；GLTFLoader/MeshoptDecoder 动态 import
 *        保首屏 chunk 零成本）
 *
 * 规格说明（P3 签核=EXT_meshopt_compression+KHR_mesh_quantization——
 *   MeshoptDecoder 注入；P7 前提=节点 TRS 保留[勿 apply——inst 原型
 *   基座读数]；扫描锚点恒用世界 AABB[量化重定心补偿后]）。
 */

import type * as THREE_NS from "three";
import type { ScannedNode } from "./groupScan";
import { groupScan } from "./groupScan";
import type { FamilyEntry } from "./registry";

export type LoadedTemplate = {
  readonly root: THREE_NS.Object3D;
  readonly nodes: readonly ScannedNode[];
};

const cache = new Map<string, Promise<LoadedTemplate>>();

/** 模板族加载（族级缓存——重复调用共享同一 Promise/解析产物）。 */
export function loadTemplate(entry: FamilyEntry): Promise<LoadedTemplate> {
  const hit = cache.get(entry.family);
  if (hit !== undefined) {
    return hit;
  }
  const pending = Promise.all([
    import("three/examples/jsm/loaders/GLTFLoader.js"),
    import("three/examples/jsm/libs/meshopt_decoder.module.js"),
  ])
    .then(([{ GLTFLoader }, { MeshoptDecoder }]) => {
      const loader = new GLTFLoader();
      loader.setMeshoptDecoder(MeshoptDecoder);
      return loader.loadAsync(entry.glb);
    })
    .then((gltf) => {
      const root = gltf.scene;
      const nodes = groupScan(root, entry);
      return { root, nodes };
    });
  cache.set(entry.family, pending);
  // 失败不缓存（下次重试——网络瞬断自愈；调用方 catch 走原语回退）
  pending.catch(() => cache.delete(entry.family));
  return pending;
}

/** 测试复位（生产面零消费）。 */
export function resetTemplateCache(): void {
  cache.clear();
}
