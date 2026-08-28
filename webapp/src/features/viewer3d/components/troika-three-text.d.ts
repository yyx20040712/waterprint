/**
 * troika-three-text 类型声明（包未携带 types 字段——仅声明消费面字段）。
 *
 * 输入:  troika-three-text 运行时模块（dist ESM）
 * 输出:  Text 类类型面（注记组件消费的最小字段集）
 *
 * 规格说明（FE1）：第三方库类型补全，非服务端契约（orval 面不受触）；
 *   字段集=Annotations.tsx 实际消费面，完整 API 见库文档。
 */
declare module "troika-three-text" {
  import type { Mesh } from "three";

  export class Text extends Mesh {
    text: string;
    fontSize: number;
    color: string;
    anchorX: "left" | "center" | "right";
    anchorY: "top" | "middle" | "bottom";
    maxWidth: number;
    letterSpacing: number;
    sync(): void;
    dispose(): void;
  }
}
