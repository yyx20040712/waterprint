/**
 * 首启运行方式向导（联机架构第七批 b7 2026-11-19；e2e-fix-r3 批同日
 * 重制——独立三卡页形态〔稿 frontend-redesign/onboarding.html 整页〕：
 * 桥在场且角色未配置时整壳换页——不透明全屏页盖住工作台〔F9-④：原
 * 透明遮罩露出背后壳的错误〕；gate 命中/probing 期壳面不挂载=后台
 * API 查询零发出〔F9-②：projects/runtime/units 404 噪声根除〕；页内
 * 状态行「运行方式：未配置」中性呈现〔F9-①：不再虚报「已连接」〕）。
 *
 * 输入:  getDesktopBridge（探测——null=浏览器态直通）+bridge.getConfig()
 *        （四角色快照——unconfigured 触发换页）+bridge.setNetworkRole
 *        （选择落地）+ClientConnectionPanel（客户端第二步：地址+token
 *        配对）
 * 输出:  useBootstrapGate（壳接线 hook——pass/probing/unconfigured 三相）
 *        +BootstrapProbePane（探测占位——壳不挂载防闪查询）+
 *        OnboardingGate（独立三选页：三卡→〔单机/服务端〕切换中态=壳
 *        窗口导航接管/〔客户端〕内嵌连接面板直到 reload 重装配）
 *
 * 规格说明（b7 任务书+e2e-fix-r3 批——稿 onboarding.html 独立页形）：
 *   - 三选语义（稿 onboarding.html）：单机=本地引擎+本地项目（默认工作
 *     方式）；服务端=本机开房间（本地引擎照常+0.0.0.0+token 配对）；
 *     客户端=加入另一台电脑（界面本地、数据计算全走远程——厚客户端
 *     非网页瘦客户端；本地打包 UI 三方式都保留，切换不自动迁移项目）；
 *   - 探测三相（useBootstrapGate）：pass=桥缺席/角色已配置/getConfig
 *     失败（桥协议异常的诚实降级——壳未就绪时常规壳面照常可用）；
 *     probing=桥在场快照未回（占位页——壳不挂载）；unconfigured=换页；
 *   - 选择落地=bridge.setNetworkRole（活体重启壳侧承担）；单机/服务端
 *     成功后壳窗口导航至引擎 origin（页面无需自处置——切换中态呈现）；
 *     客户端成功后壳保留静态壳 origin，向导转第二步=连接面板；
 *   - 三主题零字面色：样式复用 global.css 既有 wp-v4-pair-card/
 *     wp-v4-badge 轴类+页面内联布局（不新增 CSS 文件面）；
 *   - 图标=稿 symbol 族内联 SVG monoline（fill none stroke currentColor
 *     1.7 round——与稿 .icon 同口径，无 emoji）。
 */
import { useEffect, useState, type ReactNode } from "react";
import { Button, Spin, Typography } from "antd";

import { ClientConnectionPanel } from "./clientConnectionPanel";
import {
  getDesktopBridge,
  type DesktopBootstrapRole,
  type DesktopNetworkRole,
} from "./desktopBridge";

/** 壳接线三相（useBootstrapGate 返回——ShellV4 换页判定单源）。 */
export type BootstrapPhase = "pass" | "probing" | "unconfigured";

/** monoline 图标（稿 onboarding.html symbol 族——fill none stroke 1.7）。 */
function MonoIcon({ d, children }: { d?: string; children?: ReactNode }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      style={{
        width: 20,
        height: 20,
        flex: "none",
        fill: "none",
        stroke: "currentColor",
        strokeWidth: 1.7,
        strokeLinecap: "round",
        strokeLinejoin: "round",
      }}
    >
      {d ? <path d={d} /> : null}
      {children}
    </svg>
  );
}

/** 三卡选择面条目（稿 onboarding.html 三段——图标+徽标+说明+动作钮）。 */
const CHOICES: ReadonlyArray<{
  role: Extract<DesktopBootstrapRole, DesktopNetworkRole>;
  title: string;
  badge: string;
  badgeClass: string;
  lines: readonly string[];
  facts: readonly string[];
  action: string;
}> = [
  {
    role: "standalone",
    title: "单机模式",
    badge: "联机：关",
    badgeClass: "",
    lines: [
      "使用本地引擎和本地项目。与当前默认工作方式一致，不需要网络。",
    ],
    facts: ["本地项目列表", "本地计算", "无远程连接"],
    action: "以单机模式进入",
  },
  {
    role: "server",
    title: "服务端模式",
    badge: "联机：开",
    badgeClass: "ok",
    lines: [
      "在这台电脑上开房间。本地引擎照常工作，局域网内他人使用地址与 token 配对。",
    ],
    facts: ["本地项目列表", "本地计算", "允许他人连接"],
    action: "配置开房间",
  },
  {
    role: "client",
    title: "客户端模式",
    badge: "联机：开",
    badgeClass: "water",
    lines: [
      "加入另一台电脑。界面仍在本地，项目、计算与交付数据全部走远程 API。",
    ],
    facts: ["远程项目列表", "远程计算", "本地不起引擎"],
    action: "配置加入房间",
  },
];

/**
 * 首启探测 hook（ShellV4 壳接线单源——三相判定；消费面=ShellV4 单处
 * 调用，OnboardingGate 页组件不再探测——同页不双发 getConfig）。
 */
export function useBootstrapGate(): BootstrapPhase {
  const bridge = getDesktopBridge();
  const [phase, setPhase] = useState<BootstrapPhase>(
    bridge === null ? "pass" : "probing",
  );

  useEffect(() => {
    if (bridge === null) {
      setPhase("pass");
      return;
    }
    let alive = true;
    bridge
      .getConfig()
      .then((snapshot) => {
        if (alive) {
          setPhase(snapshot.role === "unconfigured" ? "unconfigured" : "pass");
        }
      })
      .catch(() => {
        if (alive) {
          setPhase("pass"); // 桥协议异常=诚实降级不拦壳
        }
      });
    return () => {
      alive = false;
    };
  }, [bridge]);

  return phase;
}

/** 探测占位页（桥在场快照未回——壳不挂载，中性确认文案零查询噪声）。 */
export function BootstrapProbePane() {
  return (
    <div
      data-testid="wp-v4-bootstrap-probe"
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 10,
        background: "var(--wp-bg-page)",
        color: "var(--wp-text-2)",
        fontSize: 13,
      }}
    >
      <Spin size="small" />
      <span>正在确认运行方式…</span>
    </div>
  );
}

/** 独立页容器（稿 onboard-main——不透明整页盖住壳，三卡响应式栅格）。 */
function OnboardingPage({ children }: { children: ReactNode }) {
  return (
    <div
      data-testid="wp-v4-onboarding-page"
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--wp-bg-page)",
        color: "var(--wp-text)",
        padding: "40px 32px 16px",
      }}
    >
      <div style={{ maxWidth: 1160, width: "100%", margin: "0 auto", flex: 1 }}>
        {children}
      </div>
      {/* F9-①：未配置中性状态行（替代状态栏「已连接」虚报——无成功色轴） */}
      <footer
        data-region="bootstrap-status"
        style={{
          maxWidth: 1160,
          width: "100%",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          gap: 8,
          borderTop: "1px solid var(--wp-border-2)",
          paddingTop: 8,
          color: "var(--wp-text-2)",
          fontSize: 11,
        }}
      >
        <span data-testid="wp-v4-bootstrap-status">
          ● 运行方式：未配置
        </span>
      </footer>
    </div>
  );
}

export function OnboardingGate() {
  const bridge = getDesktopBridge();
  // 防御：非 gate 命中路径直挂（桥缺席）不渲染——正常接线由 ShellV4
  // 在 unconfigured 相换页渲染本件
  const [chosen, setChosen] = useState<DesktopNetworkRole | null>(null);
  const [switching, setSwitching] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);

  /** 选择落地（活体重启壳侧承担；客户端成功后向导转第二步）。 */
  const handleChoose = async (role: DesktopNetworkRole) => {
    if (bridge === null || switching) {
      return;
    }
    setChosen(role);
    setFailed(null);
    setSwitching(true);
    try {
      const result = await bridge.setNetworkRole(role);
      if (!result.ok) {
        setFailed(
          result.restartRequired
            ? "切换未能完成——配置已保存，重启桌面应用后按新角色运行。"
            : "切换请求被拒绝——请重试或查看桌面端提示。",
        );
        setSwitching(false);
        return;
      }
      // ok：单机/服务端=壳窗口导航接管（页面保持切换中态）；客户端=
      // 壳保留本 origin，切换完成——向导转第二步（连接面板）
      if (role === "client") {
        setSwitching(false);
      }
    } catch {
      setFailed("切换请求失败——请在桌面端重试。");
      setSwitching(false);
    }
  };

  if (bridge === null) {
    return null;
  }

  if (chosen === "client" && !switching) {
    // 客户端第二步：远程地址+token 配对（既有面板复用；连接成功=
    // reload 重装配客户端模式，向导不再出现〔role 已配置〕）
    return (
      <OnboardingPage>
        <Typography.Title level={4}>加入房间（客户端模式）</Typography.Title>
        <Typography.Paragraph type="secondary">
          界面已在本机运行；输入服务端的地址与配对 token 完成加入。本机
          不启动计算引擎。
        </Typography.Paragraph>
        <ClientConnectionPanel />
      </OnboardingPage>
    );
  }

  return (
    <OnboardingPage>
      <header style={{ marginBottom: 20 }}>
        <span
          style={{
            display: "inline-grid",
            placeItems: "center",
            width: 34,
            height: 34,
            borderRadius: 17,
            color: "var(--wp-accent)",
            background: "var(--wp-accent-soft)",
            marginBottom: 14,
          }}
        >
          <MonoIcon d="M12 3C9 7 6 10.2 6 14a6 6 0 0 0 12 0c0-3.8-3-7-6-11ZM9 15.2c.4 1.5 1.4 2.2 3 2.3" />
        </span>
        <Typography.Title level={3} style={{ marginTop: 0 }}>
          选择 WaterPrint 的运行方式
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ maxWidth: 760 }}>
          这是独立桌面窗口，界面始终在这台电脑上运行。只有客户端模式把项目
          数据与计算交给远程服务器。
        </Typography.Paragraph>
      </header>
      <div
        className="wp-v4-pair-card"
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 8,
          marginBottom: 20,
        }}
      >
        <span style={{ color: "var(--wp-accent)", flex: "none" }}>
          <MonoIcon>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v6M12 7.5v.1" />
          </MonoIcon>
        </span>
        <span style={{ fontSize: 12.5, lineHeight: 1.7 }}>
          <strong>厚客户端，不是网页瘦客户端。</strong>
          本地打包 UI 在三种方式下都保留；切换角色不会自动上传或迁移项目。
        </span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 16,
        }}
      >
        {CHOICES.map((choice) => (
          <div className="wp-v4-pair-card" key={choice.role}>
            <div className="wp-v4-pair-head">
              <div>
                <h4>{choice.title}</h4>
                {choice.lines.map((line) => (
                  <span
                    className="wp-v4-runtime-sub"
                    style={{ display: "block" }}
                    key={line}
                  >
                    {line}
                  </span>
                ))}
              </div>
              <span className={`wp-v4-badge ${choice.badgeClass}`}>
                {choice.badge}
              </span>
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
              {choice.facts.map((fact) => (
                <span
                  key={fact}
                  style={{
                    fontSize: 10.5,
                    color: "var(--wp-text-3)",
                    border: "1px solid var(--wp-border-2)",
                    borderRadius: 4,
                    padding: "1px 6px",
                  }}
                >
                  {fact}
                </span>
              ))}
            </div>
            <Button
              type="primary"
              data-testid={`wp-v4-onboarding-${choice.role}`}
              disabled={switching}
              loading={switching && chosen === choice.role}
              onClick={() => void handleChoose(choice.role)}
              style={{ marginTop: 12, justifySelf: "start" }}
            >
              {choice.action}
            </Button>
          </div>
        ))}
      </div>
      {switching && chosen !== "client" ? (
        <Typography.Paragraph style={{ marginTop: 12 }}>
          正在切换运行方式——窗口将转入本地引擎页面…
        </Typography.Paragraph>
      ) : null}
      {failed !== null ? (
        <Typography.Paragraph type="warning" style={{ marginTop: 12 }}>
          {failed}
        </Typography.Paragraph>
      ) : null}
      <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
        以后可在「运行角色与联机设置」中更改。
      </Typography.Paragraph>
    </OnboardingPage>
  );
}
