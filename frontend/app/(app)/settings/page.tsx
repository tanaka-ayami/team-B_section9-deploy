"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { groupApi, userApi, billingApi, Group, UserMe } from "@/lib/api";

// プランの上限（30枚）はAPIから取得できないため引き続きフロント側の固定値とする
const PLAN_LIMIT = 30;

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserMe | null>(null);
  const [remindDays, setRemindDays] = useState(3);
  const [emailNotifyEnabled, setEmailNotifyEnabled] = useState(true);
  const [isSavingRemind, setIsSavingRemind] = useState(false);
  const [groups, setGroups] = useState<Group[]>([]);

  useEffect(() => {
    Promise.all([groupApi.list(), userApi.getMe()])
      .then(([gs, me]) => {
        setGroups(gs);
        setUser(me);
        setRemindDays(me.remind_days_before);
        setEmailNotifyEnabled(me.email_notify_enabled);
      })
      .catch(() => setGroups([]));
  }, []);

  const scanRemaining = user
    ? PLAN_LIMIT - user.monthly_scan_count
    : PLAN_LIMIT;
  const scanProgress = user ? (user.monthly_scan_count / PLAN_LIMIT) * 100 : 0;

  const handleRemindSave = async () => {
    setIsSavingRemind(true);
    try {
      const updated = await userApi.updateMe({
        remind_days_before: remindDays,
        email_notify_enabled: emailNotifyEnabled,
      });
      setUser(updated);
    } finally {
      setIsSavingRemind(false);
    }
  };

  const handleLogout = async () => {
    const confirmed = window.confirm("ログアウトしますか？");
    if (!confirmed) return;
    await signOut(auth);
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      {/* ページヘッダー */}
      <div className="px-4 pt-6 pb-4">
        <h1 className="text-2xl font-bold text-[#1F2D24]">設定</h1>
        <p className="text-sm text-[#8fa09e] mt-0.5">
          {user?.display_name ?? ""}
        </p>
      </div>

      <div className="px-4 space-y-4 pb-8">
        {/* プランカード */}
        <div className="bg-white rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-[#1F2D24]">
              無料プラン
            </span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[#EEF1EC] text-[#557C79]">
              Free
            </span>
          </div>

          {/* プログレスバー */}
          <div>
            <div className="h-2 rounded-full bg-[#f2f1ec] overflow-hidden">
              <div
                className="h-full rounded-full bg-[#557C79] transition-all"
                style={{ width: `${scanProgress}%` }}
              />
            </div>
            <p className="text-xs text-[#8fa09e] mt-1.5">
              今月のスキャン残り：{scanRemaining}枚/{PLAN_LIMIT}枚
            </p>
            <p className="text-xs text-[#8fa09e]">
              （毎月1日AM0:00 JSTにリセット）
            </p>
          </div>

          {/* Stripeボタン */}
          <button
            type="button"
            onClick={async () => {
              try {
                const { checkout_url } =
                  await billingApi.createCheckoutSession();
                window.location.href = checkout_url;
              } catch (e) {
                alert("決済ページの取得に失敗しました。再度お試しください。");
              }
            }}
            className="w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2"
            style={{ backgroundColor: "#D45D1E" }}
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"
              />
            </svg>
            有料プランにアップグレード（Stripe）
          </button>
        </div>

        {/* リマインド設定 */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">リマインド設定</p>
          <div className="bg-white rounded-2xl p-4 space-y-4">
            {/* 通知方法（issue #73追加） */}
            <div className="space-y-2">
              <p className="text-sm text-[#1F2D24] font-medium">通知方法</p>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="radio"
                  name="notifyMethod"
                  checked={emailNotifyEnabled === true}
                  onChange={() => setEmailNotifyEnabled(true)}
                  className="w-4 h-4 accent-[#557C79]"
                />
                <span className="text-sm text-[#1F2D24]">
                  メール＋アプリ内通知
                </span>
              </label>

              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="radio"
                  name="notifyMethod"
                  checked={emailNotifyEnabled === false}
                  onChange={() => setEmailNotifyEnabled(false)}
                  className="w-4 h-4 accent-[#557C79]"
                />
                <span className="text-sm text-[#1F2D24]">アプリ内通知のみ</span>
              </label>
            </div>

            <div className="h-px bg-[#f2f1ec]" />

            {/* 日数設定 */}
            <div className="flex items-center gap-3">
              <svg
                className="w-5 h-5 text-[#557C79] flex-shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"
                />
              </svg>
              <span className="text-sm text-[#1F2D24]">期限の</span>
              <input
                type="number"
                min={1}
                max={30}
                value={remindDays}
                onChange={(e) => setRemindDays(Number(e.target.value))}
                className="w-14 text-center text-sm font-semibold rounded-lg border border-[#D2D4BC] py-1.5 bg-[#F5F6F2] text-[#1F2D24]"
              />
              <span className="text-sm text-[#1F2D24]">日前にメール送信</span>
              <button
                type="button"
                onClick={handleRemindSave}
                disabled={isSavingRemind}
                className="ml-auto text-xs font-medium px-3 py-1.5 rounded-lg text-white"
                style={{ backgroundColor: "#557C79" }}
              >
                {isSavingRemind ? "保存中..." : "保存"}
              </button>
            </div>
          </div>
        </div>

        {/* グループ */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">グループ</p>
          <div className="bg-white rounded-2xl overflow-hidden">
            {groups.map((group, index) => (
              <div key={group.id}>
                {index > 0 && <div className="h-px bg-[#f2f1ec] mx-4" />}
                <button
                  type="button"
                  onClick={() => router.push(`/settings/groups/${group.id}`)}
                  className="w-full flex items-center gap-3 px-4 py-4 hover:bg-[#f2f1ec] transition-colors"
                >
                  <span
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ backgroundColor: "#EEF1EC" }}
                  >
                    <svg
                      className="w-4 h-4 text-[#557C79]"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"
                      />
                    </svg>
                  </span>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-[#1F2D24]">
                      {group.name}
                    </p>
                  </div>
                  <svg
                    className="w-4 h-4 text-[#8fa09e]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8.25 4.5l7.5 7.5-7.5 7.5"
                    />
                  </svg>
                </button>
              </div>
            ))}

            {/* 新しいグループを作成 */}
            <div className="h-px bg-[#f2f1ec] mx-4" />
            <button
              type="button"
              onClick={() => router.push("/settings/groups/new")}
              className="w-full flex items-center gap-3 px-4 py-4 hover:bg-[#f2f1ec] transition-colors"
            >
              <span
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: "#FFF0E8" }}
              >
                <svg
                  className="w-4 h-4 text-[#D45D1E]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4.5v15m7.5-7.5h-15"
                  />
                </svg>
              </span>
              <p className="text-sm font-medium text-[#D45D1E]">
                新しいグループを作成
              </p>
              <svg
                className="w-4 h-4 text-[#8fa09e] ml-auto"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.25 4.5l7.5 7.5-7.5 7.5"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* 通知（固定） */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">通知</p>
          <div className="bg-white rounded-2xl p-4 flex items-center gap-3">
            <span
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: "#EEF1EC" }}
            >
              <svg
                className="w-4 h-4 text-[#557C79]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"
                />
              </svg>
            </span>
            <div className="flex-1">
              <p className="text-sm font-medium text-[#1F2D24]">
                アプリ内お知らせ
              </p>
              <p className="text-xs text-[#8fa09e]">
                他メンバーの登録時・個別タップで既読
              </p>
            </div>
          </div>
        </div>

        {/* アカウント */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">アカウント</p>
          <div className="bg-white rounded-2xl overflow-hidden">
            <button
              type="button"
              onClick={() => router.push("/settings/profile")}
              className="w-full flex items-center gap-3 px-4 py-4 hover:bg-[#f2f1ec] transition-colors"
            >
              <svg
                className="w-5 h-5 text-[#557C79]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
                />
              </svg>
              <p className="text-sm font-medium text-[#1F2D24]">
                プロフィール編集
              </p>
              <svg
                className="w-4 h-4 text-[#8fa09e] ml-auto"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.25 4.5l7.5 7.5-7.5 7.5"
                />
              </svg>
            </button>

            <div className="h-px bg-[#f2f1ec] mx-4" />

            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-4 hover:bg-[#f2f1ec] transition-colors"
            >
              <svg
                className="w-5 h-5 text-[#D45D1E]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75"
                />
              </svg>
              <p className="text-sm font-medium text-[#D45D1E]">ログアウト</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
