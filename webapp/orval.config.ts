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
      },
    },
  },
});
