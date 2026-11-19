/**
 * 客户端连接状态机 store（联机架构第六批 2026-11-19——zustand，app 层；
 * themeStore/shared store 先例外落 app：消费面全在 app 壳〔statusBar/
 * projectsZone/runtime 卡/设置 Modal〕，shared 不 import app 分层禁令
 * 下 http.ts 只读 remoteBase localStorage 不经本件）。
 *
 * 输入:  useClientConnectionStore（状态：phase 六态+remoteBase+serverMeta
 *        +mismatch；动作：六转移函数）——初始态自 localStorage 同步水合
 * 输出:  ClientPhase 类型+useClientConnectionStore（消费面经 selector 订阅）
 *
 * 规格说明（联机第六批任务书——状态机形态裁量）：
 *   - 六态：local（本地模式——远程档案缺席）/connecting（客户端模式
 *     装配期：meta 握手在途）/online（握手过+数据面可达）/offline
 *     （远程不可达——网络错/服务停）/token_invalid（数据面 401——配对
 *     凭据失效）/version_mismatch（api 或 data 版本不匹配——契约阻断）；
 *   - 驱动面=useClientConnection 单例 supervisor（meta 查询+queryCache
 *     订阅），本件只持状态不发起请求——转移语义单点可测；
 *   - remoteBase/phase 初始水合：模块创建期同步读 localStorage
 *     （themeStore 同制式——import 期先于首帧，首渲染即正确态）；
 *     连接/断开动作（写档案+整页 reload 重装配）在 clientConnectionPanel
 *     ——本件不持 reload 副作用（jsdom 测试可直测转移零 reload 干扰）；
 *   - token_invalid 粘性：置位后仅 supervisor 收到数据面 success 才回
 *     online（重试/换 token 后首个成功请求即恢复——不留悬挂错误态）。
 */
import { create } from "zustand";

import type { MetaInfo } from "../shared/api/generated/model";
import { getRemoteBaseUrl } from "../shared/api/remoteBase";

/** 客户端连接六态（local=本地模式；余五态=客户端模式内部态）。 */
export type ClientPhase =
  | "local"
  | "connecting"
  | "online"
  | "offline"
  | "token_invalid"
  | "version_mismatch";

/** 版本不匹配明细（api/data 两面——期望值与服务器实际值并陈展示）。 */
export interface VersionMismatch {
  kind: "api" | "data";
  expected: string;
  actual: string;
}

interface ClientConnectionState {
  /** 当前态（init=水合：有档案 connecting 起点/无档案 local）。 */
  phase: ClientPhase;
  /** 远程基址（init=localStorage 水合；null=本地模式）。 */
  remoteBase: string | null;
  /** 最近一次成功握手的服务器 meta（offline/token_invalid 态保留旧值展示）。 */
  serverMeta: MetaInfo | null;
  /** 版本不匹配明细（仅 version_mismatch 态非 null）。 */
  mismatch: VersionMismatch | null;
  setPhaseConnecting: () => void;
  setOnline: (meta: MetaInfo) => void;
  setOffline: () => void;
  setTokenInvalid: () => void;
  setVersionMismatch: (meta: MetaInfo, mismatch: VersionMismatch) => void;
}

/** 模块创建期水合（import 期同步——先于首帧）。 */
const initialRemoteBase = getRemoteBaseUrl();

export const useClientConnectionStore =
  create<ClientConnectionState>()((set) => ({
    phase: initialRemoteBase === null ? "local" : "connecting",
    remoteBase: initialRemoteBase,
    serverMeta: null,
    mismatch: null,
    setPhaseConnecting: () =>
      set((state) =>
        state.remoteBase === null
          ? {}
          : { phase: "connecting", mismatch: null },
      ),
    setOnline: (meta) =>
      set((state) =>
        state.remoteBase === null
          ? {}
          : { phase: "online", serverMeta: meta, mismatch: null },
      ),
    setOffline: () =>
      set((state) =>
        state.remoteBase === null ? {} : { phase: "offline" },
      ),
    setTokenInvalid: () =>
      set((state) =>
        state.remoteBase === null ? {} : { phase: "token_invalid" },
      ),
    setVersionMismatch: (meta, mismatch) =>
      set((state) =>
        state.remoteBase === null
          ? {}
          : { phase: "version_mismatch", serverMeta: meta, mismatch },
      ),
  }));
