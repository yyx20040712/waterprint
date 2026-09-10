/**
 * 建项入口纯函数面（P0-1——F1/F3/F4-文案面收口）。
 *
 * 输入:  项目显示名+project_id（下拉 label 格式化）/导入 JSON 文本（解析）
 * 输出:  下拉 label「名称 (id 前 8)」（无名回退全 id）/解析结果判别联合
 *
 * 规格说明（op-chain-fix-plan §一——2026-09-11 用户裁定批）：
 *   - F3 显示面：项目下拉「名称 (id8)」——name 非空=`名称 (id 前 8 位)`；
 *     空 name（历史项目/未命名）=回退全 id（裸 hex 诚实显示，禁猜默认名）；
 *   - 导入面：JSON.parse 包裹为判别联合（ok: parsed / error: 用户语消息）
 *     ——Modal 消费；文件体校验（schema/版本门）归 server parse_project
 *     422（InvalidProjectPayloadError——FE 不做第二业务源，红线②）；
 *   - 名称口径与 core ViewState.name 同源：strip 后 1~100（空白新建
 *     必填校验在此；导入覆盖名留空=不传）。
 */

/** 名称长度上限（与 core ViewState.name 同口径）。 */
export const PROJECT_NAME_MAX = 100;

/** 去空白名称校验（空白新建必填面；导入可选面同限长）。 */
export function normalizeProjectName(raw: string): { name: string; valid: boolean } {
  const name = raw.trim();
  return { name, valid: name.length > 0 && name.length <= PROJECT_NAME_MAX };
}

/** 项目下拉 label：`名称 (id 前 8)`；无名回退全 id（F3 显示面——
 * id=null 守备面返回名称裸值，列表契约 id 恒非空实际不可达）。 */
export function projectOptionLabel(
  name: string,
  projectId: string | null,
): string {
  const id = projectId ?? "";
  const trimmed = name.trim();
  return trimmed && id ? `${trimmed} (${id.slice(0, 8)})` : id || trimmed;
}

/** 导入 JSON 解析结果（判别联合——错误消息为用户语）。 */
export type ImportedProject =
  | { ok: true; project: Record<string, unknown> }
  | { ok: false; error: string };

/** 解析导入文件文本为项目载荷对象（结构校验归 server 422 面）。 */
export function parseProjectJson(text: string): ImportedProject {
  try {
    const parsed: unknown = JSON.parse(text);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return { ok: false, error: "项目文件应为 JSON 对象（顶层非对象无法导入）" };
    }
    return { ok: true, project: parsed as Record<string, unknown> };
  } catch (error) {
    return {
      ok: false,
      error: `文件不是合法 JSON：${error instanceof Error ? error.message : "解析失败"}`,
    };
  }
}
