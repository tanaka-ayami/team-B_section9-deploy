"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FirebaseError } from "firebase/app";
import { loginWithEmail, registerWithEmail, resetPassword, getIdToken } from "@/lib/firebase";
import { firebaseErrorToJa } from "@/lib/utils";
import { FormField } from "./FormField";

const MailIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
  </svg>
);

const LockIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
  </svg>
);

type AuthTab = "login" | "register";

function validate(tab: AuthTab, email: string, password: string, passwordConfirm: string): string | null {
  if (!email.trim()) return "メールアドレスを入力してください";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "メールアドレスの形式が正しくありません";
  if (!password) return "パスワードを入力してください";
  if (tab === "register") {
    if (password.length < 6) return "パスワードは6文字以上にしてください";
    if (password !== passwordConfirm) return "パスワードが一致しません。もう一度確認してください";
  }
  return null;
}

export function AuthForm() {
  const router = useRouter();
  const [tab, setTab] = useState<AuthTab>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetSent, setResetSent] = useState(false);

  const switchTab = (next: AuthTab) => {
    setTab(next);
    setError(null);
    setPassword("");
    setPasswordConfirm("");
    setResetSent(false);
  };

  const handleLogin = async () => {
    const err = validate("login", email, password, "");
    if (err) { setError(err); return; }
    setLoading(true);
    setError(null);
    try {
      await loginWithEmail(email, password);
      router.replace("/calendar");
    } catch (e) {
      setError(e instanceof FirebaseError ? firebaseErrorToJa(e.code) : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    const err = validate("register", email, password, passwordConfirm);
    if (err) { setError(err); return; }
    setLoading(true);
    setError(null);
    try {
      await registerWithEmail(email, password);
      const token = await getIdToken();
      const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      await fetch(`${base}/v1/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({}),
      });
      router.replace("/calendar");
    } catch (e) {
      setError(e instanceof FirebaseError ? firebaseErrorToJa(e.code) : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!email.trim()) { setError("パスワードリセット用のメールアドレスを入力してください"); return; }
    setLoading(true);
    setError(null);
    try {
      await resetPassword(email);
      setResetSent(true);
    } catch (e) {
      setError(e instanceof FirebaseError ? firebaseErrorToJa(e.code) : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => tab === "login" ? handleLogin() : handleRegister();
  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter") handleSubmit(); };

  return (
    <div className="bg-white rounded-t-3xl px-6 pt-8 pb-12">
      <div className="flex rounded-full p-1 mb-7" style={{ background: "#EEF1EC" }}>
        <div
            role="button"
            tabIndex={0}
            onPointerDown={() => switchTab("login")}
            className="flex-1 py-2 rounded-full text-xs font-medium text-center cursor-pointer select-none"
            style={tab === "login" ? { background: "#4A7C59", color: "#fff" } : { color: "#6B7C6F" }}
        >
            ログイン
        </div>
        <div
            role="button"
            tabIndex={0}
            onPointerDown={() => switchTab("register")}
            className="flex-1 py-2 rounded-full text-xs font-medium text-center cursor-pointer select-none"
            style={tab === "register" ? { background: "#4A7C59", color: "#fff" } : { color: "#6B7C6F" }}
        >
            新規登録
        </div>
    </div>

      {resetSent && (
        <div className="mb-4 p-3 rounded-xl text-xs" style={{ background: "#EAF3DE", border: "1px solid #86BFAD", color: "#3B6D11" }}>
          リセット用メールを送信しました。メールを確認してください。
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 rounded-xl text-xs" style={{ background: "#FCEBEB", border: "1px solid #f87171", color: "#E24B4A" }}>
          {error}
        </div>
      )}

      <FormField
        label="メールアドレス"
        icon={<MailIcon />}
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="taro@example.com"
        autoComplete="email"
      />

      <FormField
        label="パスワード"
        icon={<LockIcon />}
        type="password"
        isPassword
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="••••••••"
        autoComplete={tab === "login" ? "current-password" : "new-password"}
      />

      {tab === "login" && (
        <div className="flex justify-end -mt-2 mb-4">
          <button type="button" onClick={handleResetPassword} className="text-xs" style={{ color: "#4A7C59" }}>
            パスワードをお忘れの方
          </button>
        </div>
      )}

      {tab === "register" && (
        <FormField
          label="パスワード（確認）"
          icon={<LockIcon />}
          type="password"
          isPassword
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="もう一度入力してください"
          autoComplete="new-password"
        />
      )}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-medium text-sm text-white transition-colors disabled:opacity-60"
        style={{ background: "#4A7C59" }}
      >
        {loading && (
          <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z" />
          </svg>
        )}
        {loading ? "処理中..." : tab === "login" ? "ログイン" : "新規登録"}
      </button>

      <p className="text-center text-xs mt-5" style={{ color: "#9BA89D" }}>
        {tab === "login" ? (
          <>
            アカウントをお持ちでない方は{" "}
            <button type="button" onClick={() => switchTab("register")} className="font-medium" style={{ color: "#4A7C59" }}>
              新規登録
            </button>
          </>
        ) : (
          <>
            すでにアカウントをお持ちの方は{" "}
            <button type="button" onClick={() => switchTab("login")} className="font-medium" style={{ color: "#4A7C59" }}>
              ログイン
            </button>
          </>
        )}
      </p>
    </div>
  );
}