/**
 * 地面/灯光台（C2-3d V1/V2——Scene.tsx 行数预算墙拆件，F5 D1 批 2026-09-25；
 * 沿 groundPlan.ts 数据面抽离先例，渲染 JSX 原位迁移零逻辑变更）。
 *
 * 输入:  GroundPlan（groundPlan 产物——Scene effective bounds 派生）+
 *        sceneBg（雾色/底色——草地开关派生）+showGrass（草地层开关）
 * 输出:  雾边融+方向光 target 锚+环境光/方向光（阴影正交半幅随对角线）+
 *        双层工程网格+可隐藏草地（空 ground=全不挂——零场景零尺度基准）
 *
 * 规格说明（C2-3d V1/V2 原位迁移；F5 D1 起 ground 消费 effective
 *   bounds——池组足迹并盒后取景）：
 *   - 灯位/阴影正交半幅/雾档距全对角线派生（bounds 派生面）；
 *   - 草地=可隐藏图层（关=深蓝工程底+蓝网格恒在——Scene 传入 sceneBg）；
 *   - y 分层避 z-fight：地面 -0.02<次格 -0.012<主格 -0.008；
 *   - 阴影面 D8（F5）：Scene Canvas shadows="basic"——本件 castShadow/
 *     receiveShadow 消费面不变。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";

import type { GroundPlan } from "../lib/groundPlan";

const GRID_MAJOR = "#3d619c";
const GRID_MINOR = "#1b2c49";

type GroundStageProps = {
  readonly ground: GroundPlan | null;
  readonly sceneBg: string;
  readonly showGrass: boolean;
};

export function GroundStage({ ground, sceneBg, showGrass }: GroundStageProps) {
  // V2 方向光 target（bounds 中心——阴影相机随场景中心覆盖；primitive
  // 挂载进场景使 target 变换生效）
  const lightTarget = useMemo(() => new THREE.Object3D(), []);
  useEffect(() => {
    if (ground !== null) {
      lightTarget.position.set(ground.centerX, 0, ground.centerZ);
      lightTarget.updateMatrixWorld();
    }
  }, [lightTarget, ground]);
  return (
    <>
      {/* C2-3d V1 雾边融：远缘网格/地面淡出至场景底色（近/远=对角线
          档距——bounds 空零地面时雾不挂；批3 迭代二：雾色随草地开关） */}
      {ground !== null && (
        <>
          <fog attach="fog" args={[sceneBg, ground.diagonal * 1.2, ground.diagonal * 3.2]} />
          <primitive object={lightTarget} />
        </>
      )}
      {/* C2-3d V2 光影：环境光降档+方向光提档（阴影对比度）；灯位/阴影
          正交半幅按对角线适配+target=bounds 中心（覆盖随场景） */}
      <ambientLight intensity={0.4} />
      {ground !== null ? (
        <directionalLight
          position={[
            ground.centerX + ground.diagonal * 0.5,
            ground.diagonal * 0.8,
            ground.centerZ + ground.diagonal * 0.35,
          ]}
          intensity={1.4}
          castShadow
          target={lightTarget}
          shadow-mapSize-width={4096}
          shadow-mapSize-height={4096}
          shadow-camera-left={-ground.diagonal * 0.75}
          shadow-camera-right={ground.diagonal * 0.75}
          shadow-camera-top={ground.diagonal * 0.75}
          shadow-camera-bottom={-ground.diagonal * 0.75}
          shadow-camera-far={ground.diagonal * 2.5}
          onUpdate={(light) => light.shadow.camera.updateProjectionMatrix()}
        />
      ) : (
        // 空场景回退档（bounds=null 零尺度基准——对角线派生面[灯位/
        // 阴影幅]不可得，v1 常量灯保持；非 V2 调档对象——A 二审
        // GD-N-04 口径记档）
        <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
      )}
      {/* C2-3d V1 地面（V2 阴影承接面——批3 迭代二：草地=可隐藏图层，
          关=深蓝工程底+蓝网格恒在；y 分层避 z-fight：地面 -0.02<
          次格 -0.012<主格 -0.008） */}
      {ground !== null && showGrass && (
        <mesh
          position={[ground.centerX, -0.02, ground.centerZ]}
          rotation={[-Math.PI / 2, 0, 0]}
          receiveShadow
        >
          <planeGeometry args={[ground.size, ground.size]} />
          <meshStandardMaterial color="#2e5239" />
        </mesh>
      )}
      {ground !== null && (
        <>
          <gridHelper
            args={[ground.size, ground.majorDivisions, GRID_MAJOR, GRID_MAJOR]}
            position={[ground.centerX, -0.008, ground.centerZ]}
          />
          <gridHelper
            args={[ground.size, ground.minorDivisions, GRID_MINOR, GRID_MINOR]}
            position={[ground.centerX, -0.012, ground.centerZ]}
          />
        </>
      )}
    </>
  );
}
