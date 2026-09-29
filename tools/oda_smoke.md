# ODA File Converter 本地手动冒烟——验证清单（批6j）

> 工件：`tools/oda_smoke.py`（**不入 pytest 收集/不入 CI**——tools/ 不在
> core/server testpaths；CI 无 ODA 环境，skip 拦截矛盾=wave6 批6j 工单
> 明示的手动工具+清单形态）。
> 真源指针：转换原语=`server/waterprint_server/jobs/dwg.py::dwg_convert`
> （WP0 ODA-A CLI 契约单源，批6j 增 `output_type` 往返向）；转换开关=
> server settings `dwg_converter_path`/`dwg_converter_timeout_s`（生产面
> 挂点 `services/exports_io.py::_post_export_dwg`）。

## 一、前置

1. 安装 ODA File Converter（Open Design Alliance 免费件，需自行下载
   安装并接受其许可）：默认安装位 `C:\Program Files\ODA\ODAFileConverter
   <版本>\ODAFileConverter.exe`。脚本定位序=`--converter` 显式参 >
   环境变量 `ODA_FILE_CONVERTER` > 常见安装位扫描 > PATH。
2. 仓根执行（server venv 同时含 core/server 依赖）：
   `uv run --project server python tools/oda_smoke.py`

## 二、脚本覆盖面与预期

| 步骤 | 预期 |
|---|---|
| 夹具导出（缺省模式） | 两份纵断 DXF：相对基准+绝对标高（`water_level=1053.2/ground_elev=1051.0`——顺带实跑批6j UF-50 通道） |
| DXF→DWG 正向 | `dwg_convert` 返回非 None；DWG 非空字节 |
| DWG→DXF 反向往返 | 同上；往返件 `ezdxf.readfile` 可读 |
| 读回断言 | modelspace 实体数 >0 |
| 汇总 | `N/N passed` → exit 0；任一失败 exit 1 |

- 转换器缺席：默认诚实失败 exit 1（`--allow-missing`=软跳过 exit 0）。
- `--mock`：内置测试替身（CLI 契约复刻的复制件）验证**编排逻辑**——
  无 ODA 机器可跑；mock 通过 ≠ ODA 兼容性通过（产物真实性须真机复验）。
- 指定既有产物：`--dxf <server exports 目录某件.dxf>`（可重复）。

## 三、人工目检项（脚本外——真机 ODA 在场时）

1. DWG 件在 CAD 软件（AutoCAD/中望/浩辰等）可打开、四线/标注/图脚
   注记齐全、无乱码（中文图层名/文本）。
2. 往返 DXF 与原件实体面量级一致（ODA 重写非逐字节——量级对拍）。
3. 绝对标高件：标高标注为绝对值（如 `1053.200`）、图脚含
   「高程基准：绝对标高」行、几何仍锚基准近原点。

## 四、结果记录

- 通过：在批次日志/工单记「ODA 冒烟 N/N passed（converter=<版本>）」。
- 失败：贴 `[summary]` 前的全部输出行+`dwg_convert_skipped` 日志因，
  挂账登记（挂账池「ODA E2E」行）。
- 本机状态（2026-09-29 批6j 实录）：ODA File Converter **未安装**——
  真机冒烟未跑（脚本以 `--mock` 验证编排逻辑通过；真机通过=待装机后
  人工补跑，欠账在册）。
