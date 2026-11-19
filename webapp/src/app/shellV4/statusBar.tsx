/**
 * v4 状态条（b2 壳重组批 2026-11-19——30px：连接/项目/单机标识+任务快
 * 速入口+主题切换器；沿革 M1 24px 位→b1 主题化→b2 挂主题切换器与单机
 * 标识槽〔稿 dockBar 位置——联机逻辑后续批，本轮仅视觉槽位〕）。
 *
 * 输入:  nav（当前入口——AI 页任务入口自隐）+projectId/useProjectName
 *        （项目名单源）+onTaskEntry（任务入口点击——shellV4 setNav ai）
 * 输出:  状态条：● 已连接+项目：<名>（长名省略号+title 全名）+「单机
 *        模式 · 本地引擎」静态标识〔data-testid=wp-v4-standalone-mode
 *        ——视觉槽，无联机行为〕+任务 ▴（非 AI 页→AI 助手页）+
 *        ThemeSwitch 三主题切换器〔b1 件自 zoneBand 工具区迁入〕
 *
 * 规格说明（b2 任务书——批准稿 statusbar 段+任务书裁决）：
 *   - 单机标识=静态槽位（不接联机开关/角色切换——后续批实装；稿
 *     connection-status 位置形，缺 href 行为）；
 *   - 任务入口=非 AI 页在场（AI 页任务条本体在场——入口冗余自隐），
 *     点击经 onTaskEntry 单通道；
 *   - 主题切换器=b1 ThemeSwitch 原件（store 单源——本件零状态）；
 *   - R1-N3 项目名截断防护沿承（v2 笔3）。
 */
import { useProjectId } from "../useProjectId";
import { useProjectName } from "../useProjectName";
import type { NavKey } from "../zoneParam";
import { ThemeSwitch } from "./themeSwitch";

export function StatusBar({
  nav,
  onTaskEntry,
}: {
  nav: NavKey;
  /** 任务快速入口（shellV4 setNav ai——AI 页任务条本体所在）。 */
  onTaskEntry: () => void;
}) {
  const [projectId] = useProjectId();
  const projectName = useProjectName();
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
      {/* 单机标识视觉槽（联机逻辑后续批——静态文案非交互） */}
      <span className="wp-v4-standalone" data-testid="wp-v4-standalone-mode">
        单机模式 · 本地引擎
      </span>
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
