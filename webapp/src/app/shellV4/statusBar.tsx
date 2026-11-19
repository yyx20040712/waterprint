/**
 * v4 状态条（b2 壳重组批 2026-11-19——30px：连接/项目/运行标识+任务快
 * 速入口+主题切换器；沿革 M1 24px 位→b1 主题化→b2 挂主题切换器与单机
 * 标识槽〔视觉槽〕→联机第五批 2026-11-19 槽位接真：读 /api/runtime
 * 呈现运行角色〔server=服务端 · 局域网可被发现；失败/未知降级静态单机
 * 标识〕，点击开运行方式与联机设置 Modal〔稿 connection-status 位〕）。
 *
 * 输入:  nav（当前入口——AI 页任务入口自隐）+projectId/useProjectName
 *        （项目名单源）+onTaskEntry（任务入口点击——shellV4 setNav ai）
 *        +onOpenRuntime（运行标识点击——shellV4 运行方式 Modal 开态）
 * 输出:  状态条：● 已连接+项目：<名>（长名省略号+title 全名）+运行标识
 *        〔data-testid=wp-v4-runtime-mode——runtimeModeLabel 单源：真实
 *        角色/失败降级〕+任务 ▴（非 AI 页→AI 助手页）+ThemeSwitch 三
 *        主题切换器〔b1 件〕
 *
 * 规格说明（联机第五批任务书——状态栏真实连接态）：
 *   - 运行标识=真实态（/api/runtime；读不到=静态单机标识诚实降级，
 *     不虚报服务端态）——文案/降级单源 runtimeFace.ts；
 *   - 标识可点（稿 connection-status 链接位→运行方式 Modal 单通道
 *     onOpenRuntime）；server 态 water 色轴变体（global.css
 *     .wp-v4-standalone.server）；
 *   - 任务入口=非 AI 页在场（AI 页任务条本体在场——入口冗余自隐），
 *     点击经 onTaskEntry 单通道；
 *   - 主题切换器=b1 ThemeSwitch 原件（store 单源——本件零状态）；
 *   - R1-N3 项目名截断防护沿承（v2 笔3）。
 */
import { useProjectId } from "../useProjectId";
import { useProjectName } from "../useProjectName";
import { useGetRuntimeApiRuntimeGet } from "../../shared/api/generated/meta/meta";
import type { NavKey } from "../zoneParam";
import { runtimeModeLabel } from "./runtimeFace";
import { ThemeSwitch } from "./themeSwitch";

export function StatusBar({
  nav,
  onTaskEntry,
  onOpenRuntime,
}: {
  nav: NavKey;
  /** 任务快速入口（shellV4 setNav ai——AI 页任务条本体所在）。 */
  onTaskEntry: () => void;
  /** 运行标识点击（shellV4 承载 RuntimeSettingsModal——稿 connection 位）。 */
  onOpenRuntime: () => void;
}) {
  const [projectId] = useProjectId();
  const projectName = useProjectName();
  // 联机第五批：真实运行角色（读不到=undefined→runtimeModeLabel 降级单机）
  const runtimeQuery = useGetRuntimeApiRuntimeGet();
  const isServer = runtimeQuery.data?.role === "server";
  return (
    <footer className="wp-v4-statusbar" data-region="status-bar">
      <span style={{ color: "var(--wp-success)" }}>●</span>
      <span>已连接</span>
      {/* R1-N3 项目名截断防护：长名省略号+title 全名悬停（短名零影响） */}
      <span
        title={projectName ?? undefined}
        style={{
          maxWidth: 200,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        项目：
        {projectId === null ? "未选择" : projectName}
      </span>
      {/* 运行标识（真实态按钮——点击开运行方式与联机设置；失败降级单机） */}
      <button
        type="button"
        className={`wp-v4-standalone${isServer ? " server" : ""}`}
        data-testid="wp-v4-runtime-mode"
        title="运行角色与联机设置"
        onClick={onOpenRuntime}
      >
        {runtimeModeLabel(runtimeQuery.data)}
      </button>
      <span className="r">
        {nav !== "ai" ? (
          <button
            type="button"
            title="任务与 AI 对话在「AI 助手」页"
            onClick={onTaskEntry}
          >
            任务 ▴
          </button>
        ) : null}
        {/* b1 主题切换器迁入（zoneBand 工具区尾→状态条右端） */}
        <ThemeSwitch />
      </span>
    </footer>
  );
}
