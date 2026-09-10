/**
 * 状态栏：底部全局信息条（C1 视觉稿新增件——工程软件标配，GPS-X 同款位）。
 *
 * 输入:  useProjectId 共享 hook 订阅面（URL ?project= 单一真相——S3 机制）
 * 输出:  24px 高信息条：左=当前项目 id（等宽字体）+右=就绪态（绿点+文案）
 *
 * 规格说明（task-C1-plan.md §3d；用户裁选「一期即做」2026-09-10）：
 *   - 版本号面减配：server 无现成引擎/数据版本端点（openapi 28 操作内
 *     无 /api/meta 族），webapp-only 批纪律不新增 server 面——引擎/
 *     数据版本列随二期或后续批有端点再上（设计书 §3d 预案）；
 *   - 连接态：一期静态「就绪」（连接错误自愈回路已有 AUTH_EVENT→
 *     TokenSettingsModal 面，状态栏不重复建设错误通道）；
 *   - projectId 空（未选项目）=「未选择项目」次色文案（不渲染 id）；超
 *     16 字符截断显示（glm 实现评审：全量哈希过长——完整值在 URL 与
 *     顶栏徽章处各有截断形态）；
 *   - app 层薄壳不测裁量（useProjectId 头注惯例：app 层零测试+
 *     jsdom 零新依赖红线）——行为面归实现后无头 DOM 断言验证。
 */
import { Typography } from "antd";

import { useProjectId } from "./useProjectId";

const STATUS_READY = "就绪";
const STATUS_NO_PROJECT = "未选择项目";

export function StatusBar() {
  const [projectId] = useProjectId();
  return (
    <footer
      style={{
        flex: "none",
        height: 24,
        display: "flex",
        alignItems: "center",
        gap: 18,
        padding: "0 14px",
        background: "#0a1220",
        borderTop: "1px solid var(--wp-border-2)",
        fontSize: 11,
        color: "var(--wp-text-3)",
        userSelect: "none",
      }}
    >
      {projectId === null ? (
        <span>{STATUS_NO_PROJECT}</span>
      ) : (
        <span>
          项目{" "}
          <Typography.Text
            style={{ fontFamily: "var(--wp-font-mono)", color: "var(--wp-text-2)", fontSize: 11 }}
          >
            {projectId.length > 16 ? `${projectId.slice(0, 16)}…` : projectId}
          </Typography.Text>
        </span>
      )}
      <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 5, color: "var(--wp-success)" }}>
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "var(--wp-success)",
            boxShadow: "0 0 6px rgba(61, 220, 151, 0.7)",
          }}
        />
        {STATUS_READY}
      </span>
    </footer>
  );
}
