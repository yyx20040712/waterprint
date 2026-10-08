/**
 * v4 管网系统区（B1 骨架批 2026-10-09——未实装占位：诚实说明文案+G5 挂起
 * 锚族承接；wireframe-d-v4 屏 7b 形）。
 *
 * 输入:  无（纯占位面）
 * 输出:  network-placeholder 区：简笔网形图标+「管网定线模块 · 规划中」
 *        诚实说明+wp-pending-network 锚族（M1 树徽标同名锚承接——B7 终验
 *        G5 在场断言面）
 *
 * 规格说明（B1 任务书 §三.4——plan §九.3）：
 *   - 点击功能区的诚实响应：占位说明而非无响应；
 *   - 文案=诚实说明（非教学性——微文案白名单外零装饰）。
 */
export function NetworkZone() {
  return (
    <section
      data-region="network-placeholder"
      className="wp-v4-placeholder"
      style={{ flex: 1 }}
    >
      <svg
        width="44"
        height="44"
        viewBox="0 0 44 44"
        fill="none"
        stroke="#b8c0c9"
        strokeWidth="1.4"
        aria-hidden
      >
        <circle cx="22" cy="22" r="17" />
        <path d="M22 5v34M5 22h34M10 10l24 24M34 10L10 34" strokeDasharray="3 3" />
      </svg>
      <span data-testid="wp-pending-network">管网定线模块 · 规划中（未实装）</span>
    </section>
  );
}
