# templates —— Excel 模板

模板与数据分离的落点（§2：模板驱动，写死逻辑为零；模板**禁用 Excel 公式**）。

## 文件规划（M1 起创建）

```
templates/
├─ manifest.yaml             # 模板版本 + 占位符语法说明
├─ calcbook_unit.xlsx        # 单单元计算书模板（M1）
├─ calcbook_plant.xlsx       # 全厂计算书模板（M2）
├─ network_io.xlsx           # 管网进出模板（M3）
└─ estimate_sheet.xlsx       # 概算表模板（M3）
```

## 模板规则

1. **禁公式**：加载时静态检查无公式单元格，含公式模板 = 加载失败
   （core trace/calcbook.py R2——计算单一事实源在 Python，§11 R12）；
2. 占位符语法 `{{field_id}}`（字段 ID 制，中文列名由模板版式提供）；
3. 模板变更走版本化：改版式不改占位符键；渲染代码不随版式变化；
4. 构建校验：模板清单与 manifest.yaml 一致（防孤儿模板）。
