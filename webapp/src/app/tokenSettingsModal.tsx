/**
 * 连接设置 Modal（R2-A 批2 D5）：API token 查看/保存/清除——零即时校验。
 *
 * 输入:  open（Modal 开态——App.tsx 设置按钮/AUTH_EVENT 自愈回路两入口）
 *        +onClose 关闭回调；Input.Password 本地受控值（开态同步现读
 *        localStorage 既有令牌）
 * 输出:  Modal（标题「连接设置」+说明文案[示意粘贴令牌+留空保存语义]
 *        +密码框+保存[setApiToken 后 onClose]/清除[clearApiToken 后
 *        onClose]/关闭三按钮）
 *
 * 规格说明（R2-A 批2 D5）：
 *   - 零即时校验：保存后下一次请求自然验证（错 token→401→AUTH_EVENT
 *     →App.tsx 重开本 Modal=自愈回路），不在本组件发探测请求；
 *   - 保存语义：输入 trim 后非空写 setApiToken（同步现读即时生效）；
 *     空=清除（null 单一空态——与「清除」按钮同归一，不造第二空态）；
 *   - 不动 router.tsx AppRoute 六值冻结面（Tabs 状态机路由面零扩，
 *     R9 冻结语义保持——Modal 形态预裁）；
 *   - token 空默认：入口按钮静默常驻（App.tsx），本 Modal 不自动弹、
 *     零请求扰动。
 */
import { Button, Input, Modal, Typography } from "antd";
import { useEffect, useState } from "react";

import { clearApiToken, getApiToken, setApiToken } from "../shared/api/token";

export function TokenSettingsModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [value, setValue] = useState("");

  // 开态同步现读既有令牌（非受控外泄——每次打开回显运行期真相）
  useEffect(() => {
    if (open) {
      setValue(getApiToken() ?? "");
    }
  }, [open]);

  /** 保存：trim 后非空写令牌、空=清除（单一空态）；零校验直接关闭。 */
  const handleSave = () => {
    const trimmed = value.trim();
    if (trimmed === "") {
      clearApiToken();
    } else {
      setApiToken(trimmed);
    }
    onClose();
  };

  /** 清除：剥令牌回落零注入态（下一次请求即生效）。 */
  const handleClear = () => {
    clearApiToken();
    onClose();
  };

  return (
    <Modal
      title="连接设置"
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="save" type="primary" onClick={handleSave}>
          保存
        </Button>,
        <Button key="clear" onClick={handleClear}>
          清除
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
        粘贴部署方分发的 API 访问令牌（保存在本浏览器，仅用于本站 API
        请求鉴权；留空保存=清除）。保存后下一次请求自然验证：令牌有误时
        本窗口会自动重新打开。
      </Typography.Paragraph>
      {/* 不设输入框占位提示属性：该英文属性名是 grep 门禁未完成标记禁词
          （全库零使用面）——示意语义由上方说明文案承载（R2-A 批2 裁量） */}
      <Input.Password
        value={value}
        onChange={(event) => setValue(event.target.value)}
        autoComplete="new-password"
      />
    </Modal>
  );
}
