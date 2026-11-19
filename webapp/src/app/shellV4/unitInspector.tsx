/**
 * 选中单元 inspector（b3 功能面重涂批 2026-11-19——稿 network.html 右栏
 * .pane.right 形：常驻侧栏〔常驻 vs 滑出判据=稿三栏并置〕——选中单元
 * 身份/当前参数/端口/操作组；未选=空态引导）。
 *
 * 输入:  projectId+unitId（?node= 选中真相）+onOpenParameters（参数方案
 *        入口导航）+onOpenEnumerate（重新枚举——ProcessZone EnumerateModal
 *        开态）+onDeleteUnit（删除单元——canvasStore.deleteNodes 通道
 *        经 ProcessZone 承接）+useUnitCatalog（名称/参数声明/端口/业务线）
 *        +useProjectDesign（当前参数值——params 通道同键缓存共享）
 * 输出:  右栏：pane-head〔中文名+id mono+已选中徽标〕+身份行〔域线徽标〕
 *        +当前参数键值行族+端口行族+操作组（参数与方案主钮/重新枚举/
 *        删除单元危险钮）+键位底注
 *
 * 规格说明（b3 批准稿 network.html 右栏段——信息组织重造，数据流零新）：
 *   - 参数行=design.nodeParams[unitId] 命中目录声明面（label_zh+dimUnit
 *     单位后缀；无覆盖值=空态行「取目录默认值」——不虚造数值）；
 *   - 端口行=目录 ports（port_id+方向）——流体色=单元业务线（水/泥轴
 *     变量；端口级流体标注=目录未达面，诚实呈现现有键）；
 *   - 操作组三钮均既有通道：导航/枚举 Modal/canvasStore 删除——本件
 *     零数据突变。
 */
import { useMemo } from "react";
import { Button } from "antd";

import { useProjectDesign } from "../../features/params/api/useProjectDesign";
import { useUnitCatalog } from "../../features/params/api/useUnitCatalog";
import { dimUnit } from "../../shared/dimLabels";
import { LINE_LABELS } from "./thumbnailNode";

/** 空态引导文案（白名单：空态引导）。 */
const NO_SELECTION_HINT = "在画布中选择单元后，参数与端口在此呈现";

export function UnitInspector({
  projectId,
  unitId,
  onOpenParameters,
  onOpenEnumerate,
  onDeleteUnit,
}: {
  projectId: string | null;
  /** ?node= 选中真相（null=空态引导）。 */
  unitId: string | null;
  /** 「参数与方案」主钮——跨入口导航（shellV4 setNav parameters）。 */
  onOpenParameters: () => void;
  /** 「重新枚举」钮——EnumerateModal 开态上抛（唯一提交入口件）。 */
  onOpenEnumerate: () => void;
  /** 「删除单元」钮——canvasStore.deleteNodes 通道（ProcessZone 承接）。 */
  onDeleteUnit: (unitId: string) => void;
}) {
  const catalog = useUnitCatalog();
  const designQuery = useProjectDesign(projectId ?? "");

  const meta = useMemo(() => {
    const units = catalog.data?.units ?? [];
    // builtin 通道：值含 kind → 目录查找键=kind（ParamForm 同口径）
    const kind = designQuery.data?.nodeKinds[unitId ?? ""] ?? null;
    return (
      units.find((unit) => unit.unit_id === (kind ?? unitId)) ?? null
    );
  }, [catalog.data, designQuery.data, unitId]);

  const params = useMemo(() => {
    if (unitId === null || meta === null) {
      return [] as { label: string; value: string; unit: string }[];
    }
    const values = designQuery.data?.nodeParams[unitId] ?? {};
    const rows: { label: string; value: string; unit: string }[] = [];
    for (const entry of meta.params ?? []) {
      const raw = values[entry.field_id];
      if (raw !== undefined) {
        rows.push({
          label: entry.label_zh ?? entry.field_id,
          value: String(raw),
          unit: dimUnit(entry.dim) ?? "",
        });
      }
    }
    return rows;
  }, [meta, designQuery.data, unitId]);

  if (unitId === null) {
    return (
      <aside className="wp-v4-pane right" data-region="unit-inspector">
        <div className="wp-v4-pane-head">
          <h3>单元属性</h3>
        </div>
        <div className="wp-v4-pane-body">
          <p
            data-testid="wp-v4-insp-empty"
            style={{ color: "var(--wp-text-2)", fontSize: 11, padding: "10px 12px" }}
          >
            {NO_SELECTION_HINT}
          </p>
        </div>
      </aside>
    );
  }

  const line = meta?.business_line ?? null;
  const lineLabel = line !== null ? (LINE_LABELS[line] ?? null) : null;

  return (
    <aside className="wp-v4-pane right" data-region="unit-inspector">
      <div className="wp-v4-pane-head">
        <div style={{ minWidth: 0 }}>
          <h3 title={unitId}>{meta?.name_zh ?? unitId}</h3>
          <span
            style={{
              display: "block",
              color: "var(--wp-text-3)",
              fontFamily: "var(--wp-font-mono)",
              fontSize: 10,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {unitId}
          </span>
        </div>
        <span className="wp-v4-badge accent">已选中</span>
      </div>
      <div className="wp-v4-pane-body">
        {lineLabel !== null ? (
          <div className="wp-v4-insp-sec">
            <span
              className={`wp-v4-badge ${line === "sludge" ? "sludge" : "water"}`}
              data-testid="wp-v4-insp-line"
            >
              {lineLabel}
            </span>
          </div>
        ) : null}
        <div className="wp-v4-insp-sec">
          <h4>当前参数</h4>
          {meta === null ? (
            <p style={{ color: "var(--wp-text-3)", fontSize: 11 }}>
              单元未在目录登记
            </p>
          ) : params.length === 0 ? (
            <p style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
              无覆盖参数——取目录默认值
            </p>
          ) : (
            params.map((row) => (
              <div className="wp-v4-kv" key={row.label}>
                <span className="k">{row.label}</span>
                <span className="v">
                  {row.value}
                  {row.unit === "" ? "" : ` ${row.unit}`}
                </span>
              </div>
            ))
          )}
        </div>
        <div className="wp-v4-insp-sec">
          <h4>端口</h4>
          {(meta?.ports ?? []).length === 0 ? (
            <p style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
              目录未声明端口
            </p>
          ) : (
            (meta?.ports ?? []).map((port) => (
              <div className="wp-v4-portrow" key={port.port_id}>
                <span
                  className={`wp-v4-portbar${line === "sludge" ? " sludge" : ""}`}
                  aria-hidden
                />
                <span>{port.port_id}</span>
                <span className="pid">{port.direction}</span>
              </div>
            ))
          )}
        </div>
        <div
          className="wp-v4-insp-sec"
          style={{ display: "grid", gap: 6, borderBottom: "none" }}
        >
          <Button
            type="primary"
            size="small"
            block
            onClick={onOpenParameters}
            data-testid="wp-v4-insp-open-params"
          >
            参数与方案
          </Button>
          <Button
            size="small"
            block
            onClick={onOpenEnumerate}
            data-testid="wp-v4-insp-enumerate"
          >
            重新枚举
          </Button>
          <Button
            size="small"
            block
            danger
            onClick={() => onDeleteUnit(unitId)}
            data-testid="wp-v4-insp-delete"
          >
            删除单元
          </Button>
        </div>
        <div className="wp-v4-pane-foot" style={{ borderTop: "none" }}>
          <span className="wp-v4-kbd">Del</span> 删除　<span className="wp-v4-kbd">F5</span> 计算
          <br />
          即时连线反馈，持久诊断进入分析面。
        </div>
      </div>
    </aside>
  );
}
