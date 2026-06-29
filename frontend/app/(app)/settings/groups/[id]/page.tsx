"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { groupApi, userApi, Group, GroupMember, Invitation } from "@/lib/api";

// アバター背景色
const AVATAR_COLORS = ["#ADCFBA", "#D2D4BC", "#FFF0E8", "#EEF1EC", "#f2f1ec"];
const getAvatarColor = (index: number) => AVATAR_COLORS[index % AVATAR_COLORS.length];

// 招待・グループ名変更で共通のBottomSheetモーダル
function BottomModal({
  title,
  onClose,
  onSubmit,
  submitLabel,
  submitting,
  children,
}: {
  title: string;
  onClose: () => void;
  onSubmit: () => void;
  submitLabel: string;
  submitting?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full bg-white rounded-t-3xl p-6 space-y-4">
        <h3 className="text-base font-semibold text-[#1F2D24]">{title}</h3>
        {children}
        <button
          type="button"
          onClick={onSubmit}
          disabled={submitting}
          className="w-full py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
          style={{ backgroundColor: "#557C79" }}
        >
          {submitting ? "処理中..." : submitLabel}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="w-full py-3 rounded-xl text-sm font-medium text-[#8fa09e]"
        >
          キャンセル
        </button>
      </div>
    </div>
  );
}

export default function GroupDetailPage() {
  const router = useRouter();
  const params = useParams();
  const groupId = params.id as string;

  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [newGroupName, setNewGroupName] = useState("");
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const isAdmin = group?.created_by === currentUserId;

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [groups, memberList, invitationList, me] = await Promise.all([
        groupApi.list(),
        groupApi.getMembers(groupId),
        groupApi.getInvitations(groupId),
        userApi.getMe(),
      ]);
      const matched = groups.find((g) => g.id === groupId) ?? null;
      setGroup(matched);
      setMembers(memberList);
      setInvitations(invitationList);
      setCurrentUserId(me.id);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId]);

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setModalSubmitting(true);
    setModalError(null);
    try {
      await groupApi.invite(groupId, inviteEmail.trim());
      const invitationList = await groupApi.getInvitations(groupId);
      setInvitations(invitationList);
      setInviteEmail("");
      setShowInviteModal(false);
    } catch (e) {
      setModalError(e instanceof Error ? e.message : "招待の送信に失敗しました");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleRename = async () => {
    if (!newGroupName.trim() || !group) return;
    setModalSubmitting(true);
    setModalError(null);
    try {
      const updated = await groupApi.update(groupId, newGroupName.trim());
      setGroup(updated);
      setShowRenameModal(false);
    } catch (e) {
      setModalError(e instanceof Error ? e.message : "グループ名の変更に失敗しました");
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!group) return;
    const confirmed = window.confirm(
      "「" + group.name + "」を削除しますか？\nグループ内の書類も削除されます。"
    );
    if (!confirmed) return;
    try {
      await groupApi.delete(groupId);
      router.replace("/settings");
    } catch (e) {
      alert(e instanceof Error ? e.message : "削除に失敗しました");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec]">
        <p className="text-sm text-[#8fa09e]">読み込み中...</p>
      </div>
    );
  }

  if (loadError || !group) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f2f1ec] px-4">
        <p className="text-sm text-[#E24B4A] text-center">
          {loadError ?? "グループが見つかりません"}
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f2f1ec]">
      {/* ヘッダー */}
      <div className="bg-[#557C79] px-4 pt-12 pb-4 flex items-center gap-3">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-8 h-8 flex items-center justify-center rounded-full"
          style={{ background: "rgba(255,255,255,0.2)" }}
          aria-label="戻る"
        >
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-white">グループ管理</h1>
      </div>

      <div className="px-4 py-4 space-y-4 pb-8">
        {/* メンバー一覧 */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">
            {"メンバー（" + members.length + "人）"}
          </p>
          <div className="bg-white rounded-2xl overflow-hidden">
            {members.map((member, index) => (
              <div key={member.id}>
                {index > 0 && <div className="h-px bg-[#f2f1ec] mx-4" />}
                <div className="flex items-center gap-3 px-4 py-3">
                  <span
                    className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold text-[#557C79] flex-shrink-0"
                    style={{ backgroundColor: getAvatarColor(index) }}
                  >
                    {member.display_name.charAt(0)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-[#1F2D24]">{member.display_name}</p>
                    <p className="text-xs text-[#8fa09e]">{member.email}</p>
                  </div>
                </div>
              </div>
            ))}
            {/* 招待ボタン */}
            <div className="h-px bg-[#f2f1ec] mx-4" />
            <button
              type="button"
              onClick={() => { setModalError(null); setShowInviteModal(true); }}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#f2f1ec] transition-colors"
            >
              <span className="w-9 h-9 rounded-full border-2 border-dashed border-[#D45D1E] flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-[#D45D1E]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </span>
              <p className="text-sm font-medium text-[#D45D1E]">メールアドレスで招待する</p>
            </button>
          </div>
        </div>

        {/* 招待中 */}
        {invitations.length > 0 && (
          <div>
            <p className="text-xs text-[#8fa09e] mb-2 px-1">招待中</p>
            <div className="bg-white rounded-2xl overflow-hidden">
              {invitations.map((inv, index) => (
                <div key={inv.id}>
                  {index > 0 && <div className="h-px bg-[#f2f1ec] mx-4" />}
                  <div className="flex items-center gap-3 px-4 py-3">
                    <svg className="w-5 h-5 text-[#8fa09e] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
                    </svg>
                    <p className="text-sm text-[#1F2D24] flex-1">{inv.invitee_email}</p>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[#FFF0E8] text-[#D45D1E]">
                      pending
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 権限説明バナー */}
        <div className="bg-[#EEF1EC] rounded-2xl p-4 flex gap-3">
          <svg className="w-4 h-4 text-[#557C79] flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
          </svg>
          <p className="text-xs text-[#557C79] leading-relaxed">
            グループ内の全メンバーが書類の登録・編集・削除を行えます。グループの削除は作成者のみ可能です。
          </p>
        </div>

        {/* グループ操作 */}
        <div>
          <p className="text-xs text-[#8fa09e] mb-2 px-1">グループ操作</p>
          <div className="bg-white rounded-2xl overflow-hidden">
            <button
              type="button"
              onClick={() => { setModalError(null); setNewGroupName(group.name); setShowRenameModal(true); }}
              className="w-full flex items-center gap-3 px-4 py-4 hover:bg-[#f2f1ec] transition-colors"
            >
              <svg className="w-5 h-5 text-[#557C79]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
              </svg>
              <p className="text-sm font-medium text-[#1F2D24]">グループ名を変更</p>
              <svg className="w-4 h-4 text-[#8fa09e] ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
            <div className="h-px bg-[#f2f1ec] mx-4" />
            {/* グループ削除（created_byのみ操作可能） */}
            <button
              type="button"
              onClick={isAdmin ? handleDelete : undefined}
              disabled={!isAdmin}
              className="w-full flex items-center gap-3 px-4 py-4 transition-colors"
              style={{ opacity: isAdmin ? 1 : 0.4, cursor: isAdmin ? "pointer" : "not-allowed" }}
            >
              <svg className="w-5 h-5 text-[#D45D1E]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
              <div className="text-left">
                <p className="text-sm font-medium text-[#D45D1E]">グループを削除</p>
                {!isAdmin && <p className="text-xs text-[#8fa09e]">作成者のみ操作可能</p>}
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* 招待モーダル */}
      {showInviteModal && (
        <BottomModal
          title="メンバーを招待"
          onClose={() => setShowInviteModal(false)}
          onSubmit={handleInvite}
          submitLabel="招待を送る"
          submitting={modalSubmitting}
        >
          {modalError && (
            <p className="text-xs text-[#E24B4A]">{modalError}</p>
          )}
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="招待するメールアドレス"
            className="w-full px-4 py-3 rounded-xl border border-[#D2D4BC] bg-[#F5F6F2] text-sm text-[#1F2D24] placeholder-[#8fa09e] outline-none"
          />
        </BottomModal>
      )}

      {/* グループ名変更モーダル */}
      {showRenameModal && (
        <BottomModal
          title="グループ名を変更"
          onClose={() => setShowRenameModal(false)}
          onSubmit={handleRename}
          submitLabel="変更する"
          submitting={modalSubmitting}
        >
          {modalError && (
            <p className="text-xs text-[#E24B4A]">{modalError}</p>
          )}
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="グループ名"
            className="w-full px-4 py-3 rounded-xl border border-[#D2D4BC] bg-[#F5F6F2] text-sm text-[#1F2D24] placeholder-[#8fa09e] outline-none"
          />
        </BottomModal>
      )}
    </div>
  );
}