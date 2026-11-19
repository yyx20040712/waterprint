/**
 * v4 窄导航轨（b2 壳重组批 2026-11-19——八入口垂直导航轨：批准稿
 * workbench.html .rail 形〔74px 竖轨+图标上/文字下+active=accent〕，
 * 替换 B1 顶带横向页签）。
 *
 * 输入:  target（当前导航——NAV_KEYS 声明序渲染）+onNavChange（切换
 *        唯一通道——shellV4 setNav）
 * 输出:  竖轨：八条 rail-link（button 元素 data-testid=wp-v4-nav-<key>
 *        锚+aria-current=page 选中语义；图标=设计稿 monoline 1.7px
 *        SVG 族 currentColor——三主题随轴换肤）
 *
 * 规格说明（b2 任务书——批准稿 workbench.html 导航轨段）：
 *   - 八入口序=NAV_KEYS 单源（工作台→AI 助手）；切换经 onNavChange
 *     单通道（点当前入口=重置子页到缺省——deliverables 三子页回 sheets
 *     的返回面）；不设管网伪入口（规划中说明面在工作台）；
 *   - 图标+文字同现（稿「重要动作保留文字」——纯图标禁用）；
 *   - 选中态=.on 类（accent 字色+accent-soft 底——选中不与流体域色
 *     共用，稿色彩条）。
 */
import type { ReactNode } from "react";

import { NAV_KEYS, NAV_LABELS, type NavKey, type NavTarget } from "../zoneParam";

/** 八入口图标（设计稿 monoline 符号族——24 视窗 stroke 1.7 currentColor）。 */
const NAV_ICONS: Record<NavKey, ReactNode> = {
  workbench: (
    <>
      <rect x="4" y="4" width="6" height="6" rx="1" />
      <rect x="14" y="4" width="6" height="6" rx="1" />
      <rect x="4" y="14" width="6" height="6" rx="1" />
      <rect x="14" y="14" width="6" height="6" rx="1" />
    </>
  ),
  process: (
    <>
      <rect x="3" y="4" width="6" height="5" rx="1" />
      <rect x="15" y="15" width="6" height="5" rx="1" />
      <path d="M9 6.5h5a4 4 0 0 1 4 4V15M6 9v6a3 3 0 0 0 3 3h6" />
    </>
  ),
  parameters: (
    <>
      <path d="M4 7h10M18 7h2M4 17h3M11 17h9M14 4v6M7 14v6" />
    </>
  ),
  analysis: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
  compare: (
    <path d="M8 5 4 9l4 4M4 9h13M16 19l4-4-4-4M20 15H7" />
  ),
  deliverables: (
    <>
      <path d="M6 3h8l4 4v14H6Z" />
      <path d="M14 3v5h5M9 12h6M9 16h6" />
    </>
  ),
  viewer3d: (
    <>
      <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9Z" />
      <path d="m4 7.5 8 4.5 8-4.5M12 12v9M8 5.3l8 4.5" />
    </>
  ),
  ai: (
    <>
      <path d="M4 4h16v13H9l-5 4Z" />
      <path d="M8 9h8M8 13h5" />
    </>
  ),
};

export function NavRail({
  target,
  onNavChange,
}: {
  target: NavTarget;
  /** 导航切换唯一通道（shellV4 setNav——replaceState 写 ?tab=）。 */
  onNavChange: (next: NavTarget) => void;
}) {
  return (
    <nav className="wp-v4-rail" aria-label="功能导航" data-region="nav-rail">
      {NAV_KEYS.map((key) => {
        const active = target.nav === key;
        return (
          <button
            key={key}
            type="button"
            className={`wp-v4-rail-link${active ? " on" : ""}`}
            data-testid={`wp-v4-nav-${key}`}
            data-nav={key}
            aria-current={active ? "page" : undefined}
            onClick={() =>
              onNavChange(
                key === target.nav
                  ? { nav: key }
                  : ({ nav: key } as NavTarget),
              )
            }
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              {NAV_ICONS[key]}
            </svg>
            <span>{NAV_LABELS[key]}</span>
          </button>
        );
      })}
    </nav>
  );
}
