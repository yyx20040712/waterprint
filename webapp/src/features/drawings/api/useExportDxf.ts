/**
 * dxf 导出下载薄壳：手写 fetch（POST 文件流——orval POST hook 返回
 * unknown 无 blob 面，不消费）。
 *
 * 输入:  {projectId, unitId, conditionKey, force?}（force=true=stale 旧
 *        结果显式重发——?force=true）
 * 输出:  useMutation 句柄（2xx→blob+anchor 下载[文件名 Content-Disposition
 *        解析，缺省客户端构造 {project}-dxf-{cond}.dxf]+导出列表键失效；
 *        非 2xx→WaterprintApiError[shared/api/http.ts 同款归一：code=
 *        error_type、message=detail]→消费面错误分级呈现）
 *
 * 规格说明（FE9 批 6b 段七，D8）：
 *   - POST /api/exports/dxf 响应=文件流（FileResponse）——orval 生成
 *     hook 按 JSON 反序列化（unknown），文件流下载走本手写 fetch 薄壳；
 *   - 错误归一与 http.ts 同款（409 StaleExportError[stale 二选一消费面]/
 *     501 ArtifactKindNotReady/ExportTemplateMissingError[诚实未就绪]/
 *     404 ExportSourceNotFoundError[先提交计算引导面]——code 判别）；
 *   - 成功后 invalidate ['/api/exports'] 前缀键（列表+工况源子键全失效
 *     ——新产物入目录表；'wp:task' 事件桥之外的主动刷新面）；
 *   - anchor 下载不携 CSS 类名（webapp 零 CSS 文件——download 属性直挂）。
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { WaterprintApiError } from "../../../shared/api/http";

/** 导出提交变量（force=stale 二选一的「仍导出旧结果」支线）。 */
export type ExportDxfInput = {
  projectId: string;
  unitId: string;
  conditionKey: string;
  force?: boolean;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** Content-Disposition 文件名解析（RFC 5987 filename* 优先，次 filename）。 */
function parseDisposition(header: string | null): string | null {
  if (!header) {
    return null;
  }
  const star = /filename\*=(?:UTF-8|utf-8)''([^;]+)/.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1]);
    } catch {
      return star[1]; // 非 URI 编码形态原样透传（服务端 ascii 命名面）
    }
  }
  const plain = /filename="?([^";]+)"?/.exec(header);
  return plain?.[1] ?? null;
}

/** dxf 导出下载（POST 文件流→blob+anchor；非 2xx→WaterprintApiError）。 */
async function exportDxf(input: ExportDxfInput): Promise<{ fileName: string }> {
  const search = input.force === true ? "?force=true" : "";
  const response = await fetch(`/api/exports/dxf${search}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: input.projectId,
      condition_key: input.conditionKey,
      options: { unit_id: input.unitId },
    }),
  });
  if (!response.ok) {
    // 错误归一（http.ts 同款）：{detail, error_type} → WaterprintApiError
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      payload = null; // 非 JSON 错误体（网关页等）——detail 留空
    }
    const body = isRecord(payload) ? payload : {};
    const code =
      typeof body.error_type === "string"
        ? body.error_type
        : `HTTP_${response.status}`;
    const rawDetail = body.detail;
    const message =
      typeof rawDetail === "string" && rawDetail
        ? rawDetail
        : `导出失败：POST /api/exports/dxf → ${response.status}`;
    throw new WaterprintApiError(code, message, payload ?? undefined);
  }
  const blob = await response.blob();
  const fileName =
    parseDisposition(response.headers.get("content-disposition")) ??
    `${input.projectId}-dxf-${input.conditionKey || "all"}.dxf`;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  return { fileName };
}

/** dxf 导出 mutation（成功后导出列表键失效——新产物入目录表）。 */
export function useExportDxf() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: exportDxf,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["/api/exports"] });
    },
  });
}
