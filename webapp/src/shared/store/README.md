# shared/store —— zustand slices

每 feature 一个 slice 文件（features/*/store/*.ts）。共享件准入=「同层晋升
准入五条」（复杂度治理方案二）；b1 主题地基批（2026-11-19）首件晋升：
主题模式为全应用横切 UI 态（app 壳+providers+后续 features 消费面），
落位本目录。

## 文件清单

| 文件 | 职责 |
|------|------|
| `themeStore.ts` | 三主题模式真源（b1 主题地基批——值域 light/warm/dark 源自已批准设计稿三主题体系）：ThemeMode 类型+THEME_MODES/THEME_MODE_LABELS+isThemeMode；readStoredThemeMode（localStorage `waterprint.theme` 读+值域校验+缺席/非法回退 light——api token 键同款 try/catch 守卫）；applyThemeMode（documentElement data-theme 属性+域色四轴按模重注入——semanticColors installDomainColorAxis(mode)）；useThemeStore（zustand——init 同步读存储零闪烁，setMode=set 状态+写 localStorage+applyThemeMode 三面联动） | b1 主题地基批实装（消费面=app/providers+shellV4/themeSwitch） |
| `themeStore.test.ts` | 主题 store vitest（jsdom——读存储三态〔缺席 light/合法值/非法回退〕+setMode 三面联动〔状态/localStorage/data-theme+域色轴〕+持久化键冻结） | b1 主题地基批实装（以 vitest 实跑为准） |

## 规则

- UI 态走 zustand；服务态走 TanStack Query（§2 选型）；
  界限：**一切来自服务端的数据不进 zustand**（queryKey 含三元组
  自动失效，§17.2）；
- 画布/3D 状态全经 store 持有，不依赖组件重挂载（§11 R14）。
