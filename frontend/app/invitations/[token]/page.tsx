"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { invitationApi, InvitationPublic } from "@/lib/api";

export default function InvitationPage() {
  const params = useParams();
  const token = params.token as string;
  const router = useRouter();
  const { user, loading } = useAuth();

  const [invitation, setInvitation] = useState<InvitationPublic | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [done, setDone] = useState<"accepted" | "rejected" | null>(null);

  useEffect(() => {
    invitationApi
      .get(token)
      .then(setInvitation)
      .catch((e) => setLoadError(e instanceof Error ? e.message : "招待の取得に失敗しました"))
      .finally(() => setIsLoading(false));
  }, [token]);

  const handleAccept = async () => {
    setIsSubmitting(true);
    setActionError(null);
    try {
      await invitationApi.accept(token);
      setDone("accepted");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "承諾に失敗しました");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setActionError(null);
    try {
      await invitationApi.reject(token);
      setDone("rejected");
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "辞退に失敗しました");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec]">
        <p className="text-sm text-[#8fa09e]">読み込み中...</p>
      </div>
    );
  }

  if (loadError || !invitation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec] px-4">
        <p className="text-sm text-[#E24B4A] text-center">
          {loadError ?? "招待が見つかりません"}
        </p>
      </div>
    );
  }

  if (done) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#f2f1ec] px-4 gap-4">
        <p className="text-sm text-[#1F2D24] text-center">
          {done === "accepted"
            ? `「${invitation.group_name}」に参加しました！`
            : "招待を辞退しました"}
        </p>
        <button
          type="button"
          onClick={() => router.replace("/calendar")}
          className="px-6 py-3 rounded-xl text-sm font-semibold text-white"
          style={{ backgroundColor: "#557C79" }}
        >
          トップへ進む
        </button>
      </div>
    );
  }

  if (invitation.status !== "pending") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec] px-4">
        <p className="text-sm text-[#8fa09e] text-center">
          この招待は既に処理済みです（{invitation.status}）
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec] px-4">
      <div className="bg-white rounded-2xl p-6 max-w-sm w-full space-y-4">
        <h1 className="text-lg font-semibold text-[#1F2D24]">グループへの招待</h1>
        <p className="text-sm text-[#1F2D24]">
          <span className="font-medium">{invitation.invited_by_email}</span> さんから
          <br />
          <span className="font-medium">「{invitation.group_name}」</span>への招待が届いています。
        </p>

        {!user ? (
          <div className="space-y-3">
            <p className="text-xs text-[#8fa09e]">
              参加するには、ログインまたは新規登録が必要です。ログイン後、自動でこのページに戻ります。
            </p>
            <button
              type="button"
              onClick={() =>
                router.push(`/login?redirect=${encodeURIComponent(`/invitations/${token}`)}`)
              }
              className="w-full py-3 rounded-xl text-sm font-semibold text-white"
              style={{ backgroundColor: "#557C79" }}
            >
              ログイン / 新規登録へ
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {actionError && <p className="text-xs text-[#E24B4A]">{actionError}</p>}
            <button
              type="button"
              onClick={handleAccept}
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
              style={{ backgroundColor: "#557C79" }}
            >
              {isSubmitting ? "処理中..." : "参加する"}
            </button>
            <button
              type="button"
              onClick={handleReject}
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl text-sm font-medium text-[#8fa09e] disabled:opacity-60"
            >
              辞退する
            </button>
          </div>
        )}
      </div>
    </div>
  );
}