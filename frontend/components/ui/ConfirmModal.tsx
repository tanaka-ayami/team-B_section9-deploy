"use client";

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}

export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "はい",
  cancelLabel = "キャンセル",
  onConfirm,
  onCancel,
  danger = false,
}: ConfirmModalProps) {
  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30" onClick={onCancel} />
      <div className="fixed inset-0 z-50 flex items-center justify-center px-6">
        <div className="w-full max-w-xs bg-white rounded-2xl p-5 space-y-4 shadow-xl">
          <div>
            <h3 className="text-sm font-semibold text-[#1F2D24]">{title}</h3>
            <p className="text-sm text-[#557C79] mt-1.5">{message}</p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2.5 rounded-xl text-sm font-medium bg-[#F5F6F2] text-[#557C79]"
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              onClick={onConfirm}
              className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white"
              style={{ backgroundColor: danger ? "#D45D1E" : "#557C79" }}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}