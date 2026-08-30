/**
 * dxf 导出下载薄壳：手写 fetch（POST 文件流——orval POST hook 返回
 * unknown 无 blob 面，不消费）+导出 blob 直接喂 dxfScene 投影（Ruling B
 * 路径：预览渲染绑定导出动作——零契约改动）。
 *
 * 输入:  {projectId, unitId, conditionKey, force?}（force=true=stale 旧
 *        结果显式重发——?force=true）
 * 输出:  useMutation 句柄（2xx→blob+anchor 下载[文件名 Content-Disposition
 *        解析，缺省客户端构造 {project}-dxf-{cond}.dxf]+blob.text()→
 *        projectDxf→ExportDxfResult{fileName,scene,sceneError} 供预览消费；
 *        非 2xx→WaterprintApiError[shared/api/http.ts 同款归一：code=
 *        error_type、message=detail]→消费面错误分级呈现）
 *
 * 规格说明（FE9 批 6b 段七 D8+B 批 D4 扩展；UX1 DS-05 迁出沿册）：
 *   - POST /api/exports/dxf 响应=文件流（FileResponse）——orval 生成
 *     hook 按 JSON 反序列化（unknown），文件流下载走本手写 fetch 薄壳；
 *   - B 批 D4：下载落盘先行（anchor 语义不变），随后 blob.text()→
 *     projectDxf try/catch——成功 scene；失败 scene=null+sceneError=
 *     DxfSceneError 中文消息（I-3 分级：预览是增强非门禁，解析失败
 *     不扰下载成功）；
 *   - 错误归一与 http.ts 同款（409 StaleExportError[stale 二选一消费面]/
 *     501 ArtifactKindNotReady/ExportTemplateMissingError[诚实未就绪]/
 *     404 ExportSourceNotFoundError[先提交计算引导面]——code 判别）；
 *   - UX1 DS-05：Content-Disposition 文件名解析迁 lib/drawingsView
 *     parseDisposition（本文件消费 import，约束维持零 antd/除 dxfScene
 *     外零直接库依赖）；
 *   - 成功后 invalidate ['/api/exports'] 前缀键=导出列表键失效（新产物
 *     入目录表；R5[DS-07]：工况源键 ['/api/cost/${projectId}'] 不在该
 *     前缀下，由 costPane 同键缓存联动）；
 *   - anchor 下载不携 CSS 类名（webapp 零 CSS 文件——download 属性直挂）。
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { WaterprintApiError } from "../../../shared/api/http";
import { projectDxf, type SvgScene } from "../lib/dxfScene";
import { parseDisposition } from "../lib/drawingsView";

/** 导出提交变量（force=stale 二选一的「仍导出旧结果」支线）。 */
export type ExportDxfInput = {
  projectId: string;
  unitId: string;
  conditionKey: string;
  force?: boolean;
};

/** 导出结果（B 批 D4：scene/sceneError 供 DrawingPreview 线稿渲染消费）。 */
export type ExportDxfResult = {
  fileName: string;
  scene: SvgScene | null;
  sceneError: string | null;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** dxf 导出下载（POST 文件流→blob+anchor；下载后 blob 喂投影；非 2xx→WaterprintApiError）。 */
async function exportDxf(input: ExportDxfInput): Promise<ExportDxfResult> {
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
  // 下载落盘先行；随后导出 blob 直接喂解析器（Ruling B 路径——预览是
  // 增强非门禁：解析失败不扰下载成功，sceneError 降级注记呈现）
  let scene: SvgScene | null = null;
  let sceneError: string | null = null;
  try {
    scene = projectDxf(await blob.text());
  } catch (error) {
    scene = null;
    sceneError =
      error instanceof Error ? error.message : "DXF 解析失败：未知错误";
  }
  return { fileName, scene, sceneError };
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
