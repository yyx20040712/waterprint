/**
 * 客户端协议期望值 vitest（联机架构第六批 2026-11-19——node 直测：常量
 * 与仓库数据包三 manifest 重算聚合串对拍=漂移防线）。
 *
 * 输入:  clientProtocol（EXPECTED_API_VERSION/EXPECTED_DATA_VERSION）+
 *        仓库根 data/ 三 manifest 版本槽（fs 实读）
 * 输出:  断言两组：①数据期望值=三包重算聚合（assumptions@..+
 *        coefficients@..+unit_prices@..——core load_run_env 同形态：
 *        包名排序拼接；数据包抬版未同步常量即红）②API 期望值形态
 *        （点分两位——server API_SEMANTIC_VERSION 制式）
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { EXPECTED_API_VERSION, EXPECTED_DATA_VERSION } from "./clientProtocol";

/** 仓库根 data/（webapp/src/shared/api → 上溯四级到仓库根）。 */
const DATA_DIR = fileURLToPath(new URL("../../../../data/", import.meta.url));

/** manifest 头部版本槽实读（键行正则——quoted 值形态）。 */
function manifestVersion(packageDir: string, key: string): string {
  const text = readFileSync(`${DATA_DIR}${packageDir}/manifest.yaml`, "utf-8");
  const match = new RegExp(`^${key}:\\s*"([^"]+)"`, "m").exec(text);
  if (match === null || match[1] === undefined) {
    throw new Error(`manifest 版本槽缺失：${packageDir}/${key}`);
  }
  return match[1];
}

describe("clientProtocol（客户端协议期望值——联机第六批）", () => {
  it("数据期望值=仓库三包重算聚合（core load_run_env 同形态——漂移防线）", () => {
    const versions: Record<string, string> = {
      assumptions: manifestVersion("assumptions", "data_version"),
      coefficients: manifestVersion("coefficients", "data_version"),
      unit_prices: manifestVersion("unit_prices", "price_data_version"),
    };
    const recomputed = Object.keys(versions)
      .sort()
      .map((name) => `${name}@${versions[name]}`)
      .join("+");
    expect(EXPECTED_DATA_VERSION).toBe(recomputed);
  });

  it("API 期望值形态=点分版本串（server API_SEMANTIC_VERSION 镜像制式）", () => {
    expect(EXPECTED_API_VERSION).toMatch(/^\d+\.\d+$/);
  });
});
