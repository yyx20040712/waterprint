/**
 * orval 配置：OpenAPI 契约（单一事实源）→ TS 类型 + TanStack Query hooks。
 *
 * 输入: ../../api-contracts/openapi.json（由 server 导出，见 api-contracts/README）
 * 输出: src/shared/api/generated/（生成物，禁手改，不入库）
 */
import { defineConfig } from "orval";

export default defineConfig({
  waterprint: {
    input: {
      target: "../api-contracts/openapi.json",
    },
    output: {
      target: "./src/shared/api/generated/client.ts",
      schemas: "./src/shared/api/generated/model",
      client: "react-query",
      mode: "tags-split",
      clean: true,
      override: {
        mutator: {
          path: "./src/shared/api/http.ts",
          name: "customInstance",
        },
        // GOV5-1（orval 8 迁移）：fetch client 默认把 status/headers 包进
        // 返回类型（{data,status,headers} 成功/错误联合）——关掉后直接
        // 返回 data 本体，保持 orval 7 时代的消费面契约（配置解优于
        // 全量消费面解包改造）。
        fetch: {
          includeHttpResponseReturnType: false,
        },
      },
    },
  },
});
