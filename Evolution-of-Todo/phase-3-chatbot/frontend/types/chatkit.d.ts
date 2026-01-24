/**
 * Type declarations for @openai/chatkit Web Component.
 * Re-exports types from the package for local usage.
 */

export type {
  OpenAIChatKit,
  ChatKitOptions,
  ChatKitEvents,
  HeaderOption,
  HistoryOption,
  StartScreenOption,
  StartScreenPrompt,
  ComposerOption,
  ThreadItemActionsOption,
  CustomApiConfig,
  HostedApiConfig,
  ColorScheme,
  ThemeOption,
  ChatKitIcon,
  LucideIcon,
} from "@openai/chatkit"

// Augment global namespace for the custom element
declare global {
  interface HTMLElementTagNameMap {
    "openai-chatkit": import("@openai/chatkit").OpenAIChatKit
  }
}
