/**
 * 产物下载 hook（EXPD 甲案）：GET /api/exports/{file_name} 手写 fetch 薄壳
 * （orval 生成的对应 GET hook 无 blob 通道[customInstance 强制 JSON.parse]
 * 不被消费，仅契约同步存在）。
 *
 * 输入:  download(fileName)——行键=服务端 file_name（SheetList 行模型
 *        唯一数据源）；Bearer 条件注入（getApiToken() 非空才带
 *        Authorization 头——空态不发送空头[auth.py 空头行为未冻结；
 *        仅新 hook 修复 M5 既存缺口，useExportArtifact 旧面零触碰挂账]）
 * 输出:  {download, pendingFileName}——download 顺序 fetchExportFile→
 *        saveBlob（浏览器下载动作即反馈，成功零额外消息）；
 *        pendingFileName 行级状态（null=空闲——仅当前行禁用转圈不阻塞
 *        他行）；异常上抛由调用面呈现（SheetList messageApi.error）
 *
 * 规格说明（EXPD 简报 §2.4 D5+总控修正②③ 2026-09-05）：
 *   - fetchExportFile 可测核（node 环境零 DOM 红线——断言面=返回值与
 *     fetch 调用形态）：GET /api/exports/${encodeURIComponent(fileName)}
 *     ——路径段编码防特殊字符破 URL；非 2xx→统一错误体
 *     {detail,error_type}→WaterprintApiError（useExportArtifact :88-107
 *     同款归一：code=error_type 缺省 HTTP_<status>、message=detail）；
 *     2xx→blob+文件名 parseDisposition ?? fileName（服务端真源优先）；
 *   - saveBlob DOM 薄壳不测（useExportArtifact :112-119 同款：
 *     createObjectURL+anchor.download+click+revoke——anchor 不携 CSS
 *     类名，webapp 零 CSS 文件口径）；
 *   - 网络错原样上抛（不吞不饰——调用面按 I-3 分级呈现，不挂误导引导）；
 *   - 不走 TanStack mutation（无缓存失效面——下载不改服务端态，列表键
 *     恒真；行级 pending 本地 state 即足）。
 */
import { useState } from "react";

import { WaterprintApiError } from "../../../shared/api/http";
import { getApiToken } from "../../../shared/api/token";
import { parseDisposition } from "../lib/drawingsView";

/** 下载产物束（blob=文件字节；fileName=落盘名——Content-Disposition 真源优先）。 */
export type ExportDownloadResult = {
  blob: Blob;
  fileName: string;
};

/** 窄化工具：plain object（非 null 非数组——useExportArtifact 同款）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 产物下载可测核（手写 fetch GET 文件流——Bearer 条件注入+错误归一）。 */
export async function fetchExportFile(fileName: string): Promise<ExportDownloadResult> {
  const headers: Record<string, string> = {};
  const apiToken = getApiToken();
  if (apiToken !== null) {
    headers.Authorization = `Bearer ${apiToken}`; // token 运行期真相（空态零注入零行为变化）
  }
  const response = await fetch(`/api/exports/${encodeURIComponent(fileName)}`, {
    method: "GET",
    headers,
  });
  if (!response.ok) {
    // 错误归一（useExportArtifact :88-107 同款）：{detail, error_type} → WaterprintApiError
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
        : `下载失败：GET /api/exports/${fileName} → ${response.status}`;
    throw new WaterprintApiError(code, message, payload ?? undefined);
  }
  const blob = await response.blob();
  const dispositionName = parseDisposition(response.headers.get("content-disposition"));
  return { blob, fileName: dispositionName ?? fileName };
}

/** DOM 薄壳：blob→anchor 下载（useExportArtifact :112-119 同款——薄壳不测）。 */
export function saveBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** 产物下载 hook（行级 pending；异常上抛由调用面呈现——成功零额外消息）。 */
export function useExportDownload(): {
  download: (fileName: string) => Promise<void>;
  pendingFileName: string | null;
} {
  const [pendingFileName, setPendingFileName] = useState<string | null>(null);
  const download = async (fileName: string): Promise<void> => {
    setPendingFileName(fileName);
    try {
      const artifact = await fetchExportFile(fileName);
      saveBlob(artifact.blob, artifact.fileName);
    } finally {
      setPendingFileName(null); // 异常同样清 pending（行可重试）
    }
  };
  return { download, pendingFileName };
}
