/**
 * 工作台运行方式卡（联机架构第五批 2026-11-19——自 workbenchZone 拆件
 * 〔行数预算，reportExports 先例〕：稿 workbench.html/workbench-server.
 * html 运行方式段——真实角色两态呈现）。
 *
 * 输入:  onOpenRuntime（设置/配对钮——shellV4 承载 RuntimeSettingsModal）+
 *        useGetRuntimeApiRuntimeGet（/api/runtime——与状态栏/Modal 同键
 *        缓存共享，零额外请求语义）
 * 输出:  右列运行方式面板：standalone/读不到=单机徽标+单机说明+「运行
 *        角色与联机设置」钮；server=服务端徽标〔water 色轴〕+「局域网
 *        可被发现」地址行+「地址与配对 token」钮
 *
 * 规格说明（联机第五批任务书——用户裁决 Minecraft 式开关模型）：
 *   - 真实角色：读不到（失败/加载中）=单机态诚实降级（与状态栏
 *     runtimeModeLabel 同口径——不虚报服务端态）；
 *   - server 态文案=稿 workbench-server.html：本地引擎照常+局域网
 *     客户端凭地址与配对 token 加入；
 *   - 首选地址=runtimePrimaryAddress 单源（lan 首选→bind_host 回落）。
 */
import { Button } from "antd";

import { useGetRuntimeApiRuntimeGet } from "../../shared/api/generated/meta/meta";
import { runtimePrimaryAddress } from "./runtimeFace";

export function WorkbenchRuntimeCard({
  onOpenRuntime,
}: {
  /** 设置/配对入口（shellV4 承载 RuntimeSettingsModal——联机第五批）。 */
  onOpenRuntime: () => void;
}) {
  // 真实角色（读不到=undefined→单机态降级）
  const runtimeQuery = useGetRuntimeApiRuntimeGet();
  const runtime = runtimeQuery.data;

  return (
    <section className="wp-wb-panel" data-region="workbench-runtime">
      <div className="wp-wb-panel-head">
        <h3>运行方式</h3>
        <span
          className={`wp-v4-badge${runtime?.role === "server" ? " water" : ""}`}
          data-testid="wp-v4-wb-runtime-badge"
        >
          {runtime?.role === "server" ? "服务端模式" : "单机模式"}
        </span>
      </div>
      <div className="wp-wb-panel-body">
        {runtime?.role === "server" ? (
          <>
            <p style={{ margin: 0, color: "var(--wp-text-2)", fontSize: 11 }}>
              本地引擎照常，项目仍在本机；局域网客户端凭地址与配对 token
              加入。
            </p>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8,
                marginTop: 8,
                fontSize: 11,
              }}
            >
              <span style={{ color: "var(--wp-text-2)" }}>局域网可被发现</span>
              <span
                className="wp-v4-runtime-mono"
                data-testid="wp-v4-wb-runtime-address"
              >
                {runtimePrimaryAddress(runtime) ?? "未发现局域网地址"}
              </span>
            </div>
            <Button
              size="small"
              style={{ marginTop: 8 }}
              onClick={onOpenRuntime}
              data-testid="wp-v4-wb-settings"
            >
              地址与配对 token
            </Button>
          </>
        ) : (
          <>
            <p style={{ margin: 0, color: "var(--wp-text-2)", fontSize: 11 }}>
              本地引擎与本地项目。联机开关关闭——不向局域网开放项目，也不连接远程服务器。
            </p>
            <Button
              size="small"
              style={{ marginTop: 8 }}
              onClick={onOpenRuntime}
              data-testid="wp-v4-wb-settings"
            >
              运行角色与联机设置
            </Button>
          </>
        )}
      </div>
    </section>
  );
}
