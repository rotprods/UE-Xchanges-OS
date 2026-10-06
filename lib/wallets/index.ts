/**
 * Barrel file — re-exports the Paper Wallet system.
 *
 * Usage:
 *   import { PaperWalletManager, checkGraduation } from "@/lib/wallets";
 */

export {
  PaperWalletManager,
  type PaperWallet,
  type PaperTrade,
  type WalletStats,
  type WalletStatus,
} from "./PaperWalletManager";

export {
  checkGraduation,
  type GraduationCriteria,
  type GraduationResult,
  type CriterionResult,
} from "./GraduationChecker";
