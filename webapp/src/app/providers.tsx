/**
 * Provider 组合：AntD ConfigProvider（深色默认）+ QueryClient（唯一实例）。
 *
 * 输入:  子组件树
 * 输出:  包裹 Provider 的子组件树
 *
 * 规格说明（骨架冻结）：
 *   - 深色主题默认（§19.3），亮色切换经 zustand UI slice 控制算法切换；
 *   - QueryClient 默认项：staleTime 0、retry 1（4xx 不重试）、
 *     refetchOnWindowFocus false（工程工具不闪数据）；
 *   - queryKey 约定：["<资源>", 三元组/分页参数…]（§17.2 前端缓存规则：
 *     输入变自动失效，杜绝旧数据上屏）；
 *   - StrictMode 双挂载安全：QueryClient 在本组件外创建（模块级或
 *     useRef 工厂），不在渲染体内 new。
 */
export function Providers(_props: { children: React.ReactNode }) {
  throw new Error("骨架未接线：Providers 待 M0 接线期实现");
}
