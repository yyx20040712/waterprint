/**
 * Provider 组合：AntD ConfigProvider（深色默认）+ QueryClient（唯一实例）。
 *
 * 输入:  子组件树
 * 输出:  QueryClientProvider+ConfigProvider 包裹的子组件树
 *
 * 规格说明（FE3 批 6b 段一，D2 实装——去骨架 throw 占位）：
 *   - 深色主题默认（§19.3）：ConfigProvider theme.darkAlgorithm；亮色切换
 *     经 zustand UI slice 控制算法切换（挂账 UX 批）；
 *   - QueryClient 默认项在 ./queryClient（D3 领域错误 retry 口径+staleTime
 *     0+refetchOnWindowFocus false——口径差异记档于该文件头）；
 *   - queryKey 约定：["<资源>", 三元组/分页参数…]（§17.2 前端缓存规则：
 *     输入变自动失效，杜绝旧数据上屏）——orval 生成器按 [url, params]
 *     组装即此形，本层不重写；
 *   - StrictMode 双挂载安全：QueryClient 模块级单例（组件外创建——工厂
 *     与策略在 ./queryClient，纯函数可测），不在渲染体内 new。
 */
import { QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, theme } from "antd";

import { createQueryClient } from "./queryClient";

// 模块级唯一实例（D2「组件外创建」——StrictMode 双挂载共享同一 client）
const queryClient = createQueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={{ algorithm: theme.darkAlgorithm }}>
        {children}
      </ConfigProvider>
    </QueryClientProvider>
  );
}
