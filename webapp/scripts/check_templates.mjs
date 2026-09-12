/**
 * 模板水密性/registry CI 校验（spec.md §8——check_templates 首版）。
 *
 * 输入:  src/features/viewer3d/assemble/registry.json +public/assets/units/
 *        资产（status:ready 族）
 * 输出:  违规清单（退出码 1）或 OK 摘要（退出码 0）
 *
 * 规格说明（spec §8 四步水密+§9 registry 门+§10 预算门；运行与 CI 同
 *   口径：node scripts/check_templates.mjs / pnpm check:templates）：
 *   - 解码走 GLTFLoader.parse+MeshoptDecoder（与 FE 运行时同路径——
 *     校验在解码后网格上做，§8 容差条款前提）；
 *   - 四步：位置焊接（ε=壳外接盒幅×2⁻¹³ 网格）→边入射恰二面→绕序
 *     有符号体积正→shell 逐件汇总；trim/equipment/instance 不校验
 *     （§8；天然非水密）；
 *   - 归一化 AABB 对拍：shell 世界外接盒=registry templateSize（同 ε
 *     容差——§2 归一基准）；
 *   - registry 语法门：schema 字段/域声明闭性/equipment 与 glb equip
 *     节点双向对账/trim 掩码竖直违例；
 *   - 预算门：glb ≤150KB/PNG ≤80KB/单族 tri ≤8000（§9 注记/§10）。
 */

import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/examples/jsm/libs/meshopt_decoder.module.js";

const WEBAPP = join(dirname(fileURLToPath(import.meta.url)), "..");
const REGISTRY_PATH = join(
  WEBAPP, "src/features/viewer3d/assemble/registry.json",
);
const ASSET_ROOT = join(WEBAPP, "public/assets/units");

/** §8 容差起点：ε=外接盒最大幅×2⁻¹³（量化步长 2 倍——首族实测标定位）。 */
const WELD_EPS_FACTOR = 2 ** -13;
const GLB_BUDGET = 150 * 1024;
const PNG_BUDGET = 80 * 1024;
const TRI_BUDGET = 8000;

const problems = [];
const notes = [];

function fail(message) {
  problems.push(message);
}

/** 命名解析（§10——与 FE groupScan 同式；返回 null=非规约名）。 */
function parseName(name) {
  const segments = name.split("__");
  if (segments.length < 3) {
    return null;
  }
  const group = { shell: "shell", trim: "trim", equip: "equipment", inst: "instance" }[segments[1]];
  if (!group) {
    return { group: "?", part: segments[2], mask: null, nc: false, bad: `组词表外 ${segments[1]}` };
  }
  let mask = null;
  let nc = false;
  for (const tail of segments.slice(3)) {
    if (tail.startsWith("ax") && tail.length > 2) {
      mask = tail.slice(2);
    } else if (tail === "nc") {
      nc = true;
    } else {
      return { group, part: segments[2], mask, nc, bad: `尾段非法 ${tail}` };
    }
  }
  return { group, part: segments[2], mask, nc, bad: null };
}

/** registry 语法门（§9 schema v1）。 */
function validateRegistry(registry) {
  if (registry.version !== 1) {
    fail(`registry.version 非法：${registry.version}（期望 1）`);
  }
  for (const [unitId, entry] of Object.entries(registry.families ?? {})) {
    const tag = `${unitId}`;
    for (const key of ["family", "prefix", "glb", "thumb", "dimSource", "templateSize", "ratioDomain", "equipment", "status"]) {
      if (entry[key] === undefined) {
        fail(`${tag}: 缺字段 ${key}（§9 schema v1）`);
      }
    }
    const { L0, W0, H0 } = entry.templateSize ?? {};
    if (!(L0 > 0) || !(W0 > 0) || !(H0 > 0)) {
      fail(`${tag}: templateSize 非正（${JSON.stringify(entry.templateSize)}）`);
    }
    if (!["cylinder", "box"].includes(entry.dimSource?.primitiveKind)) {
      fail(`${tag}: dimSource.primitiveKind 非法（${entry.dimSource?.primitiveKind}）`);
    }
    for (const domain of entry.ratioDomain ?? []) {
      if (!(domain.min < domain.max) || !["L", "W", "H"].includes(domain.numerator) || !["L", "W", "H"].includes(domain.denominator)) {
        fail(`${tag}: ratioDomain 条目非法（${JSON.stringify(domain)}）`);
      }
    }
    for (const [part, spec] of Object.entries(entry.equipment ?? {})) {
      if (!(spec.templateFeature > 0) || !(spec.actualFactor > 0)) {
        fail(`${tag}.equipment.${part}: 非正（${JSON.stringify(spec)}——§5）`);
      }
      if (spec.anchor !== undefined && !["pool_center_bottom", "aabb_min"].includes(spec.anchor)) {
        fail(`${tag}.equipment.${part}: anchor 非法（${spec.anchor}）`);
      }
    }
    if (!["ready", "pending"].includes(entry.status)) {
      fail(`${tag}: status 非法（${entry.status}）`);
    }
    notes.push(`${tag} → ${entry.family}（${entry.status}）`);
  }
}

/** GLB 解析（GLTFLoader.parse+MeshoptDecoder——与运行时同路径）。 */
function parseGlb(glbPath) {
  const data = readFileSync(glbPath);
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  return new Promise((resolve, reject) => {
    const buffer = data.buffer.slice(
      data.byteOffset, data.byteOffset + data.byteLength,
    );
    loader.parse(buffer, "", resolve, reject);
  });
}

/** §8 四步水密（焊接网格上：边入射/绕序体积）。 */
function watertightCheck(name, position, index, eps) {
  // 1. 位置焊接（ε 网格哈希——§8 禁按索引边直配对前提）
  const cell = Math.max(eps, 1e-9);
  const weldMap = new Map();
  const welded = [];
  const remap = new Int32Array(position.length / 3);
  for (let i = 0; i < remap.length; i += 1) {
    const x = position[i * 3];
    const y = position[i * 3 + 1];
    const z = position[i * 3 + 2];
    const key = `${Math.round(x / cell)},${Math.round(y / cell)},${Math.round(z / cell)}`;
    const existing = weldMap.get(key);
    if (existing === undefined) {
      const next = welded.length;
      weldMap.set(key, next);
      welded.push([x, y, z]);
      remap[i] = next;
    } else {
      remap[i] = existing;
    }
  }
  // 2. 边入射计数（无向边恰二面）
  const incidence = new Map();
  const faces = [];
  for (let i = 0; i < index.length; i += 3) {
    const tri = [remap[index[i]], remap[index[i + 1]], remap[index[i + 2]]];
    if (tri[0] === tri[1] || tri[1] === tri[2] || tri[0] === tri[2]) {
      fail(`${name}: 退化三角形（焊接后共点）`);
      return;
    }
    faces.push(tri);
    for (let e = 0; e < 3; e += 1) {
      const a = tri[e];
      const b = tri[(e + 1) % 3];
      const key = a < b ? `${a}_${b}` : `${b}_${a}`;
      incidence.set(key, (incidence.get(key) ?? 0) + 1);
    }
  }
  const badEdges = [...incidence.values()].filter((n) => n !== 2).length;
  if (badEdges > 0) {
    fail(`${name}: 边入射非二面 ${badEdges} 条（开口/非流形——§8 第 2 步）`);
    return;
  }
  // 3. 绕序一致性（有符号体积 V=Σ(v0·(v1×v2))/6 正号=外法线）
  let volume = 0;
  for (const [a, b, c] of faces) {
    const v0 = welded[a];
    const v1 = welded[b];
    const v2 = welded[c];
    volume +=
      (v0[0] * (v1[1] * v2[2] - v1[2] * v2[1])
        - v0[1] * (v1[0] * v2[2] - v1[2] * v2[0])
        + v0[2] * (v1[0] * v2[1] - v1[1] * v2[0])) / 6;
  }
  if (!(volume > 1e-6)) {
    fail(`${name}: 有符号体积非正 V=${volume.toFixed(6)}（绕序翻转/退化——§8 第 3 步）`);
  }
}

async function checkFamily(unitId, entry) {
  if (entry.status !== "ready") {
    notes.push(`${unitId}: pending——资产门跳过（合法降级）`);
    return;
  }
  const glbPath = join(ASSET_ROOT, entry.glb.replace("/assets/units/", ""));
  const pngPath = join(ASSET_ROOT, entry.thumb.replace("/assets/units/", ""));
  for (const [label, path, budget] of [["glb", glbPath, GLB_BUDGET], ["png", pngPath, PNG_BUDGET]]) {
    if (!existsSync(path)) {
      fail(`${unitId}: ${label} 资产缺位 ${path}`);
      return;
    }
    const size = statSync(path).size;
    if (size > budget) {
      fail(`${unitId}: ${label} ${size} B 超预算 ${budget} B`);
    }
  }
  const gltf = await parseGlb(glbPath).catch((error) => {
    fail(`${unitId}: GLB 解析失败——${error.message}`);
    return null;
  });
  if (gltf === null) {
    return;
  }
  const root = gltf.scene;
  root.updateMatrixWorld(true);
  const eps = Math.max(
    entry.templateSize.L0, entry.templateSize.W0, entry.templateSize.H0,
  ) * WELD_EPS_FACTOR;
  let totalTris = 0;
  const equipParts = new Set();
  let shellSeen = false;
  root.traverse((object) => {
    const parsed = parseName(object.name);
    if (parsed === null) {
      return;
    }
    if (parsed.bad) {
      fail(`${object.name}: 命名违例（${parsed.bad}——§10）`);
      return;
    }
    if (parsed.group === "trim" && parsed.mask !== null && parsed.mask.includes("z")) {
      fail(`${object.name}: trim 掩码含 Blender 竖直轴 z（S1 违例）`);
    }
    if (parsed.group === "equipment") {
      equipParts.add(parsed.part);
    }
    if (parsed.group !== "shell" || parsed.nc) {
      return;
    }
    shellSeen = true;
    const mesh = object;
    const geometry = mesh.geometry;
    const position = geometry.getAttribute("position");
    const index = geometry.getIndex();
    if (position === undefined || index === null) {
      fail(`${object.name}: 缺 position/index 属性`);
      return;
    }
    const world = new THREE.Vector3();
    const worldPosition = new Float32Array(position.count * 3);
    for (let i = 0; i < position.count; i += 1) {
      world.fromBufferAttribute(position, i).applyMatrix4(object.matrixWorld);
      worldPosition[i * 3] = world.x;
      worldPosition[i * 3 + 1] = world.y;
      worldPosition[i * 3 + 2] = world.z;
    }
    watertightCheck(object.name, worldPosition, index.array, eps);
    totalTris += index.count / 3;
  });
  if (!shellSeen) {
    fail(`${unitId}: 零 shell 水密子件（§2 前提硬约束）`);
  }
  // §2 归一化 AABB 对拍（shell 全组世界外接盒=templateSize）
  const box = new THREE.Box3();
  root.traverse((object) => {
    const parsed = parseName(object.name);
    if (parsed !== null && parsed.group === "shell" && object.isMesh) {
      box.expandByObject(object);
    }
  });
  if (box.isEmpty()) {
    fail(`${unitId}: shell AABB 空`);
  } else {
    const want = {
      x: [-entry.templateSize.L0 / 2, entry.templateSize.L0 / 2],
      y: [0, entry.templateSize.H0],
      z: [-entry.templateSize.W0 / 2, entry.templateSize.W0 / 2],
    };
    const got = {
      x: [box.min.x, box.max.x],
      y: [box.min.y, box.max.y],
      z: [box.min.z, box.max.z],
    };
    for (const axis of ["x", "y", "z"]) {
      for (const bound of [0, 1]) {
        if (Math.abs(got[axis][bound] - want[axis][bound]) > eps) {
          fail(
            `${unitId}: shell AABB ${axis}${bound === 0 ? "min" : "max"}=`
            + `${got[axis][bound].toFixed(4)} 期望 ${want[axis][bound]}（templateSize 对拍）`,
          );
        }
      }
    }
  }
  // §5 双向对账：glb equip 节点 ↔ registry equipment 键
  for (const part of equipParts) {
    if (entry.equipment[part] === undefined) {
      fail(`${unitId}: equip 节点 ${part} 缺 registry 规格（§5 数据链断）`);
    }
  }
  for (const part of Object.keys(entry.equipment ?? {})) {
    if (!equipParts.has(part)) {
      fail(`${unitId}: registry equipment.${part} 在 glb 无对应节点`);
    }
  }
  if (totalTris > TRI_BUDGET) {
    fail(`${unitId}: tri ${totalTris} 超预算 ${TRI_BUDGET}（§10）`);
  }
  notes.push(
    `${unitId}: 水密四步过+AABB 对拍过（tris=${totalTris}, ε=${eps.toFixed(4)}m）`,
  );
}

async function main() {
  if (!existsSync(REGISTRY_PATH)) {
    console.error(`[FAIL] registry 缺位：${REGISTRY_PATH}`);
    process.exit(1);
  }
  const registry = JSON.parse(readFileSync(REGISTRY_PATH, "utf-8"));
  validateRegistry(registry);
  for (const [unitId, entry] of Object.entries(registry.families ?? {})) {
    // eslint-disable-next-line no-await-in-loop —— 族序校验（输出序稳定）
    await checkFamily(unitId, entry);
  }
  console.log("== check_templates（spec §8 四步水密+registry/资产/预算门）");
  for (const note of notes) {
    console.log(`  · ${note}`);
  }
  if (problems.length > 0) {
    console.error(`[FAIL] 模板校验违规 ${problems.length} 处：`);
    for (const item of problems) {
      console.error(`  - ${item}`);
    }
    process.exit(1);
  }
  console.log("[OK] 模板校验全绿");
}

await main();
