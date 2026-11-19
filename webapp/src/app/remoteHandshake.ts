/**
 * 远程握手探测与版本比对（联机架构第六批 2026-11-19——连接测试面：
 * 稿 connection.html 客户端段「测试连接+版本握手结果」）。
 *
 * 输入:  performHandshake(baseUrl, token)（候选远程地址+token——设置面
 *        测试连接钮）；compareServerVersions(meta)（/api/meta 载荷——
 *        supervisor 在线复核同消费）
 * 输出:  HandshakeOutcome 四态（ok/unreachable/token_invalid/version_
 *        mismatch）+VersionCheck 纯函数比对结果
 *
 * 规格说明（联机第六批任务书——版本握手策略 v1 缺省，用户「瑕疵后置」
 *   授权）：
 *   - 三步探测：①GET {base}/api/meta（b5 豁免端点——无 token 可达，
 *     不可达/非 2xx=unreachable）②GET {base}/api/projects 带 Bearer
 *     （受保端点探针——401=token_invalid；非 401 失败=unreachable 口径）
 *     ③版本比对（compareServerVersions——api_version 不匹配或
 *     data_version 三包不匹配=version_mismatch 阻断并陈双方值）；
 *   - token 先于版本判：凭据无效时版本面板无意义（先修 token 再看
 *     契约）；meta 数据在两态下都已取到——结果面板可展示服务器版本；
 *   - 期望值单源=shared/api/clientProtocol（构建期常量——取舍记档在彼）；
 *   - 本件零 React 面零 store 面——fetch 全局直调（vitest stubGlobal
 *     可测；浏览器/jsdom 同形）。
 */
import {
  EXPECTED_API_VERSION,
  EXPECTED_DATA_VERSION,
} from "../shared/api/clientProtocol";
import type { MetaInfo } from "../shared/api/generated/model";

/** 版本比对结果（ok=true 放行；false=kind 两面+双方值并陈）。 */
export type VersionCheck =
  | { ok: true }
  | { ok: false; kind: "api" | "data"; expected: string; actual: string };

/** 握手探测四态结果（连接测试 UI + 阻断逻辑消费）。 */
export type HandshakeOutcome =
  | { status: "ok"; meta: MetaInfo }
  | { status: "unreachable" }
  | { status: "token_invalid" }
  | {
      status: "version_mismatch";
      meta: MetaInfo;
      check: Extract<VersionCheck, { ok: false }>;
    };

/** 版本比对纯函数（api 先 data 后——api 契约不匹配优先呈报）。 */
export function compareServerVersions(meta: MetaInfo): VersionCheck {
  if (meta.api_version !== EXPECTED_API_VERSION) {
    return {
      ok: false,
      kind: "api",
      expected: EXPECTED_API_VERSION,
      actual: meta.api_version,
    };
  }
  if (meta.data_version !== EXPECTED_DATA_VERSION) {
    return {
      ok: false,
      kind: "data",
      expected: EXPECTED_DATA_VERSION,
      actual: meta.data_version,
    };
  }
  return { ok: true };
}

/** 单步 fetch 判定助手（网络异常/非 2xx 归一 false——不区分病因）。 */
async function reachableJson(url: string): Promise<unknown | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as unknown;
  } catch {
    return null; // 网络不可达/DNS 失败/中止——unreachable 单一归一
  }
}

/**
 * 远程握手探测（连接测试）：meta 豁免面取版本 → 受保面探 token → 比对。
 *
 * token 空串=匿名探测（远程 standalone 态可过）；Bearer 通道与运行期
 * http.ts 一致（Authorization 头——events SSE 的 ？token= 通道不涉本面）。
 */
export async function performHandshake(
  baseUrl: string,
  token: string,
): Promise<HandshakeOutcome> {
  const meta = await reachableJson(`${baseUrl}/api/meta`);
  if (
    meta === null ||
    typeof meta !== "object" ||
    !("app_version" in meta) ||
    !("api_version" in meta) ||
    !("data_version" in meta) ||
    typeof (meta as Record<string, unknown>).app_version !== "string" ||
    typeof (meta as Record<string, unknown>).api_version !== "string" ||
    typeof (meta as Record<string, unknown>).data_version !== "string"
  ) {
    return { status: "unreachable" }; // 载荷面不完整（非 WaterPrint 服务？）
  }
  let probeStatus = 0;
  try {
    const trimmed = token.trim();
    // 匿名探测=零 headers 键（与 http.ts 零注入零行为变同口径）
    const probe = await fetch(
      `${baseUrl}/api/projects`,
      trimmed === "" ? {} : { headers: { Authorization: `Bearer ${trimmed}` } },
    );
    probeStatus = probe.status;
  } catch {
    return { status: "unreachable" };
  }
  if (probeStatus === 401) {
    return { status: "token_invalid" };
  }
  if (probeStatus < 200 || probeStatus >= 300) {
    return { status: "unreachable" };
  }
  const serverMeta = meta as MetaInfo;
  const check = compareServerVersions(serverMeta);
  return check.ok
    ? { status: "ok", meta: serverMeta }
    : { status: "version_mismatch", meta: serverMeta, check };
}
