/**
 * 首启运行方式向导（联机架构第七批 b7 2026-11-19——批准稿
 * frontend-redesign/onboarding.html：桥在场且角色未配置时三选遮罩——
 * 单机/服务端/客户端+厚客户端说明）。
 *
 * 输入:  getDesktopBridge（探测——null=浏览器态不渲染向导〔诚实降级：
 *        浏览器打开的页面无角色概念〕）+bridge.getConfig()（四角色快照
 *        ——unconfigured 触发向导）+bridge.setNetworkRole（选择落地）
 *        +ClientConnectionPanel（客户端第二步：地址+token 配对）
 * 输出:  null（桥缺席/角色已配置/getConfig 失败=不拦壳）或全屏遮罩：
 *        三卡选择面→（单机/服务端）切换中态=壳窗口导航接管；（客户端）
 *        内嵌连接面板直到 reload 重装配
 *
 * 规格说明（b7 任务书——desktop 壳首启向导接线）：
 *   - 三选语义（稿 onboarding.html）：单机=本地引擎+本地项目（默认工作
 *     方式）；服务端=本机开房间（本地引擎照常+0.0.0.0+token 配对）；
 *     客户端=加入另一台电脑（界面本地、数据计算全走远程——厚客户端
 *     非网页瘦客户端；本地打包 UI 三方式都保留，切换不自动迁移项目）；
 *   - 选择落地=bridge.setNetworkRole（活体重启壳侧承担）；单机/服务端
 *     成功后壳窗口导航至引擎 origin（页面无需自处置——切换中态呈现）；
 *     客户端成功后壳保留静态壳 origin，向导转第二步=连接面板；
 *   - getConfig 失败=不渲染向导（桥协议异常的诚实降级——壳未就绪时
 *     常规壳面照常可用）；
 *   - 三主题零字面色：样式复用 global.css 既有 wp-v4-pair-card/
 *     wp-v4-badge 轴类+遮罩内联定位（不新增 CSS 文件面）。
 */
import { useEffect, useState, type ReactNode } from "react";
import { Button, Typography } from "antd";

import { ClientConnectionPanel } from "./clientConnectionPanel";
import {
  getDesktopBridge,
  type DesktopBootstrapRole,
  type DesktopNetworkRole,
} from "./desktopBridge";

/** 三卡选择面条目（稿 onboarding.html 三段——徽标+说明行两键）。 */
const CHOICES: ReadonlyArray<{
  role: Extract<DesktopBootstrapRole, DesktopNetworkRole>;
  title: string;
  badge: string;
  badgeClass: string;
  lines: readonly string[];
  action: string;
}> = [
  {
    role: "standalone",
    title: "单机模式",
    badge: "联机：关",
    badgeClass: "",
    lines: [
      "使用本地引擎和本地项目。与当前默认工作方式一致，不需要网络。",
      "本地项目列表 · 本地计算 · 无远程连接",
    ],
    action: "以单机模式进入",
  },
  {
    role: "server",
    title: "服务端模式",
    badge: "联机：开",
    badgeClass: "ok",
    lines: [
      "在这台电脑上开房间。本地引擎照常工作，局域网内他人使用地址与 token 配对。",
      "本地项目列表 · 本地计算 · 允许他人连接",
    ],
    action: "配置开房间",
  },
  {
    role: "client",
    title: "客户端模式",
    badge: "联机：开",
    badgeClass: "water",
    lines: [
      "加入另一台电脑。界面仍在本地，项目、计算与交付数据全部走远程 API。",
      "远程项目列表 · 远程计算 · 本地不起引擎",
    ],
    action: "配置加入房间",
  },
];

/** 遮罩容器（fixed 全屏+居中列——内联定位，内容面走 wp-v4 轴类）。 */
function Overlay({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        overflow: "auto",
        padding: 24,
      }}
      data-testid="wp-v4-onboarding-overlay"
    >
      <div style={{ maxWidth: 760, margin: "0 auto" }}>{children}</div>
    </div>
  );
}

export function OnboardingGate() {
  const bridge = getDesktopBridge();
  // undefined=探测中；null=桥缺席或 getConfig 失败（不拦壳）
  const [snapshotRole, setSnapshotRole] = useState<
    DesktopBootstrapRole | null | undefined
  >(bridge === null ? null : undefined);
  const [chosen, setChosen] = useState<DesktopNetworkRole | null>(null);
  const [switching, setSwitching] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    if (bridge === null) {
      return;
    }
    let alive = true;
    bridge
      .getConfig()
      .then((snapshot) => {
        if (alive) {
          setSnapshotRole(snapshot.role);
        }
      })
      .catch(() => {
        if (alive) {
          setSnapshotRole(null); // 桥协议异常=诚实降级不拦壳
        }
      });
    return () => {
      alive = false;
    };
  }, [bridge]);

  if (bridge === null || snapshotRole !== "unconfigured") {
    return null;
  }

  /** 选择落地（活体重启壳侧承担；客户端成功后向导转第二步）。 */
  const handleChoose = async (role: DesktopNetworkRole) => {
    if (switching) {
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

  if (chosen === "client" && !switching) {
    // 客户端第二步：远程地址+token 配对（既有面板复用；连接成功=
    // reload 重装配客户端模式，向导不再出现〔role 已配置〕）
    return (
      <Overlay>
        <Typography.Title level={4}>加入房间（客户端模式）</Typography.Title>
        <Typography.Paragraph type="secondary">
          界面已在本机运行；输入服务端的地址与配对 token 完成加入。本机
          不启动计算引擎。
        </Typography.Paragraph>
        <ClientConnectionPanel />
      </Overlay>
    );
  }

  return (
    <Overlay>
      <Typography.Title level={3}>选择 WaterPrint 的运行方式</Typography.Title>
      <Typography.Paragraph type="secondary">
        这是独立桌面窗口，界面始终在这台电脑上运行。只有客户端模式把项目
        数据与计算交给远程服务器。厚客户端，不是网页瘦客户端——本地打包
        UI 在三种方式下都保留；切换角色不会自动上传或迁移项目。
      </Typography.Paragraph>
      <div style={{ display: "grid", gap: 12 }}>
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
            <Button
              type="primary"
              data-testid={`wp-v4-onboarding-${choice.role}`}
              disabled={switching}
              loading={switching && chosen === choice.role}
              onClick={() => void handleChoose(choice.role)}
              style={{ marginTop: 8, justifySelf: "start" }}
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
      <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
        以后可在「运行角色与联机设置」中更改。
      </Typography.Paragraph>
    </Overlay>
  );
}
