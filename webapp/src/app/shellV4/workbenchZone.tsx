/**
 * v4 工作台区（b2 壳重组批 2026-11-19——八入口着陆页：项目列表+规划中
 * 说明；沿革 B1 projectsZone〔独立 zone〕→b2 归工作台入口〔ProjectsZone
 * 原件零改挂载〕+旧 networkZone 占位区退役〔「管网定线 规划中」诚实
 * 说明条迁本区——不设伪导航入口，稿 workbench.html 规划能力段〕）。
 *
 * 输入:  onOpenProject（打开项目后落工艺页——shellV4 setNav process）
 * 输出:  工作台：ProjectsZone 原件（列表/新建/导入/搜索/打开/复制/
 *        重命名/删除——B1/V3 D4 逻辑零改）+规划能力条（wp-pending-
 *        network 锚族沿承——G5 在场断言面）
 *
 * 规格说明（b2 任务书——批准稿 workbench.html）：
 *   - 打开项目=切项目+落工艺页（旧动线落 design 画布子页——迁移映射
 *     design→process 同源）；
 *   - 规划能力条=诚实说明（非教学性——微文案白名单内挂起说明族）；
 *     管网定线不进八入口导航（不设虚假入口）。
 */
import { ProjectsZone } from "./projectsZone";

export function WorkbenchZone({
  onOpenProject,
}: {
  /** 打开项目动线（shellV4 承接——setNav process）。 */
  onOpenProject: () => void;
}) {
  return (
    <section
      data-region="workbench"
      style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}
    >
      <ProjectsZone onOpen={onOpenProject} />
      {/* 规划能力条（旧 networkZone 占位语义迁入——锚族沿承） */}
      <div
        data-region="workbench-pending"
        style={{
          flex: "none",
          display: "flex",
          alignItems: "center",
          gap: 10,
          margin: "0 18px 14px",
          padding: "8px 12px",
          border: "1px solid var(--wp-border-2)",
          borderRadius: 6,
          background: "var(--wp-bg-elevated)",
          color: "var(--wp-text-2)",
          fontSize: 11,
        }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 44 44"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          aria-hidden
        >
          <circle cx="22" cy="22" r="17" />
          <path d="M22 5v34M5 22h34M10 10l24 24M34 10L10 34" strokeDasharray="3 3" />
        </svg>
        <span data-testid="wp-pending-network">
          管网定线模块 · 规划中（未实装）
        </span>
      </div>
    </section>
  );
}
