/**
 * API token 存取（R2-A 批2 D1）：localStorage 单键三函数——运行期 token 面唯一真相。
 *
 * 输入:  setApiToken(token) 的令牌串（设置页保存/?token= 首参引导写入）；
 *        getApiToken()/clearApiToken() 零参同步现读
 * 输出:  getApiToken → string|null（null=未配置——请求零注入零行为变化）；
 *        setApiToken/clearApiToken → void（写后即时生效）
 *
 * 规格说明（R2-A 批2 D1）：
 *   - key=`waterprint.api_token`（命名空间防碰撞——同源多应用共存面）；
 *   - 同步现读：无全局缓存无订阅无刷新语义——消费方（http.ts headers 面/
 *     useTaskFeed SSE URL 面）每次现取，设置页保存即时生效；
 *   - node 测试环境守卫：vitest 默认 node 环境无 localStorage——typeof
 *     守卫（undefined 视同未配置），既有 node 形态测试零适配；
 *   - localStorage 抛异常（隐私模式/配额满）：读写均保守视同未配置面
 *     （不向调用方外抛——token 是鉴权增强件非业务依赖）。
 */
const STORAGE_KEY = "waterprint.api_token";

/** 读 token（null=未配置——undefined/localStorage 缺席/空串同归 null 单一空态）。 */
export function getApiToken(): string | null {
  try {
    if (typeof localStorage === "undefined") {
      return null; // node 测试环境守卫（D1）
    }
    const value = localStorage.getItem(STORAGE_KEY);
    return value === null || value === "" ? null : value;
  } catch {
    return null; // 隐私模式等异常面：保守视同未配置
  }
}

/** 写 token（即时生效——下一次请求现取即带；环境缺席/写失败静默）。 */
export function setApiToken(token: string): void {
  try {
    if (typeof localStorage === "undefined") {
      return;
    }
    localStorage.setItem(STORAGE_KEY, token);
  } catch {
    // 配额满/隐私模式：静默失败（后续请求零注入=安全侧缺省）
  }
}

/** 清除 token（下一次请求回落零注入；环境缺席/删失败静默）。 */
export function clearApiToken(): void {
  try {
    if (typeof localStorage === "undefined") {
      return;
    }
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // 同上：清除失败保守视同未配置面
  }
}
