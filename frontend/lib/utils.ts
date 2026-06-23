import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function firebaseErrorToJa(code: string): string {
  const map: Record<string, string> = {
    "auth/invalid-email":        "メールアドレスの形式が正しくありません",
    "auth/user-not-found":       "メールアドレスまたはパスワードが間違っています",
    "auth/wrong-password":       "メールアドレスまたはパスワードが間違っています",
    "auth/invalid-credential":   "メールアドレスまたはパスワードが間違っています",
    "auth/email-already-in-use": "このメールアドレスはすでに登録されています",
    "auth/weak-password":        "パスワードは6文字以上にしてください",
    "auth/too-many-requests":    "ログイン試行が多すぎます。しばらく時間をおいてください",
  };
  return map[code] ?? `エラーが発生しました（${code}）`;
}