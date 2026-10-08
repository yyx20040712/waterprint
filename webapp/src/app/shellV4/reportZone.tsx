/**
 * v4 计算说明区（B1 骨架批 2026-10-09——左分类导航+右文档阅读壳（空态）；
 * wireframe-d-v4 屏 6 形；内容=B6 公式批）。
 *
 * 输入:  无（B1 空态壳——文档面=B6 批 wp_export_report 再生阅读态）
 * 输出:  report 区：report-nav（分类导航骨架——封面/设计原始资料/工艺流程
 *        与单元计算/水力与高程/概算/达标判定/公式溯源）+report-doc（文档
 *        阅读壳空态引导）
 *
 * 规格说明（B1 任务书 §三.7——plan §九.6：数据源=最近完成计算·report
 * 再生；导出=语境区 calcbook/audit〔B6〕）。空态文案=白名单内引导。
 */
const NAV_SECTIONS: readonly string[] = [
  "封面与目录",
  "1 设计原始资料",
  "2 工艺流程与单元计算",
  "3 水力与高程计算",
  "4 工程概算",
  "5 出水达标判定",
  "附录 公式溯源",
];

export function ReportZone() {
  return (
    <section style={{ flex: 1, minWidth: 0, display: "flex" }}>
      <aside
        data-region="report-nav"
        style={{
          width: 190,
          flex: "none",
          background: "var(--wp-bg-container)",
          borderRight: "1px solid var(--wp-border-2)",
          padding: "6px 4px",
          overflow: "auto",
        }}
      >
        <div
          style={{
            fontSize: 11,
            color: "var(--wp-text-2)",
            letterSpacing: 1,
            padding: "4px 8px 6px",
          }}
        >
          说明书导航
        </div>
        {NAV_SECTIONS.map((label) => (
          <div
            key={label}
            style={{ padding: "4px 8px", fontSize: 11.5, color: "var(--wp-text)" }}
          >
            {label}
          </div>
        ))}
      </aside>
      <div
        data-region="report-doc"
        style={{
          flex: 1,
          minWidth: 0,
          margin: 8,
          padding: "20px 26px",
          background: "#ffffff",
          border: "1px solid var(--wp-border-2)",
          borderRadius: 6,
          color: "var(--wp-text-2)",
          fontSize: 12,
        }}
      >
        计算说明在完成计算后生成
      </div>
    </section>
  );
}
