/**
 * 批量任务恢复存储层测试：sessionStorage 读写清除三函数+异常降级
 * （SVRB2 D8——storage 注入 mock，node 直测零环境依赖）。
 *
 * 输入:  内存 Storage 替身（含抛异常形态）+project×kind 键维度用例载荷
 * 输出:  往返/隔离/畸形归 null/清除/异常静默五面断言（先红后绿：
 *        module 未就绪=import 解析红）
 */
import { describe, expect, it } from "vitest";

import {
  batchTaskKey,
  clearBatchTask,
  readBatchTask,
  writeBatchTask,
} from "./batchTaskStore";

/** 内存 Storage 替身（Storage 合同子集全实现——getItem/setItem/removeItem）。 */
function makeStorage(store = new Map<string, string>()): Storage {
  return {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };
}

/** 全方法抛异常替身（隐私模式/配额满面——异常静默降级分支）。 */
function makeThrowingStorage(): Storage {
  const boom = () => {
    throw new Error("storage unavailable");
  };
  return {
    length: 0,
    clear: boom,
    getItem: boom,
    key: boom,
    removeItem: boom,
    setItem: boom,
  } as unknown as Storage;
}

describe("batchTaskStore 键维度", () => {
  it("键名=前缀+project+kind 双维度（同项目多 kind 互不串台）", () => {
    expect(batchTaskKey("p1", "dxf")).toBe("waterprint:exportBatch:p1:dxf");
    expect(batchTaskKey("p1", "ifc")).not.toBe(batchTaskKey("p1", "dxf"));
    expect(batchTaskKey("p2", "dxf")).not.toBe(batchTaskKey("p1", "dxf"));
  });
});

describe("batchTaskStore 读写往返", () => {
  it("write→read 往返恒等（{taskId,total} 最小载荷）", () => {
    const storage = makeStorage();
    writeBatchTask(storage, "p1", "dxf", { taskId: "t-1", total: 3 });
    expect(readBatchTask(storage, "p1", "dxf")).toEqual({ taskId: "t-1", total: 3 });
  });

  it("clear 后 read 归 null", () => {
    const storage = makeStorage();
    writeBatchTask(storage, "p1", "dxf", { taskId: "t-1", total: 3 });
    clearBatchTask(storage, "p1", "dxf");
    expect(readBatchTask(storage, "p1", "dxf")).toBeNull();
  });

  it("kind 维度隔离（dxf 写入不污染 ifc 键）", () => {
    const storage = makeStorage();
    writeBatchTask(storage, "p1", "dxf", { taskId: "t-dxf", total: 2 });
    expect(readBatchTask(storage, "p1", "ifc")).toBeNull();
  });
});

describe("batchTaskStore 畸形归一（read 单一空态 null）", () => {
  it("未写键→null", () => {
    expect(readBatchTask(makeStorage(), "p1", "dxf")).toBeNull();
  });

  it("非 JSON 串→null", () => {
    const storage = makeStorage();
    storage.setItem(batchTaskKey("p1", "dxf"), "{not-json");
    expect(readBatchTask(storage, "p1", "dxf")).toBeNull();
  });

  it("taskId 空串→null（task_id 唯一消费字段不可空）", () => {
    const storage = makeStorage();
    storage.setItem(batchTaskKey("p1", "dxf"), JSON.stringify({ taskId: "", total: 3 }));
    expect(readBatchTask(storage, "p1", "dxf")).toBeNull();
  });

  it("total 非正整数（0/负数/小数/非数）→null", () => {
    const storage = makeStorage();
    for (const total of [0, -1, 1.5, "3", null]) {
      storage.setItem(batchTaskKey("p1", "dxf"), JSON.stringify({ taskId: "t-1", total }));
      expect(readBatchTask(storage, "p1", "dxf")).toBeNull();
    }
  });
});

describe("batchTaskStore 异常静默降级（token.ts 保守先例）", () => {
  it("storage 抛异常：read→null / write·clear 不抛（提交主流程不受损）", () => {
    const storage = makeThrowingStorage();
    expect(readBatchTask(storage, "p1", "dxf")).toBeNull();
    expect(() => writeBatchTask(storage, "p1", "dxf", { taskId: "t-1", total: 1 })).not.toThrow();
    expect(() => clearBatchTask(storage, "p1", "dxf")).not.toThrow();
  });

  it("storage=null（无 window 面）：三函数全静默（read 恒 null）", () => {
    expect(readBatchTask(null, "p1", "dxf")).toBeNull();
    expect(() => writeBatchTask(null, "p1", "dxf", { taskId: "t-1", total: 1 })).not.toThrow();
    expect(() => clearBatchTask(null, "p1", "dxf")).not.toThrow();
  });
});
