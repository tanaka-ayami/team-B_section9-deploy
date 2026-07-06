"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { documentApi, ApiError, billingApi } from "@/lib/api";

export default function ScanPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [isCheckingOut, setIsCheckingOut] = useState(false);

  const handleFile = async (file: File) => {
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const data = await documentApi.scan(formData);

      sessionStorage.setItem("scanResult", JSON.stringify(data));
      router.push("/scan-confirm");
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        // スキャン上限超過：解析失敗画面には遷移せず、課金モーダルを表示する
        setShowLimitModal(true);
        return;
      }

      sessionStorage.setItem(
        "scanResult",
        JSON.stringify({
          title: null,
          category: null,
          deadline: null,
          has_deadline: false,
          image_url: null,
        }),
      );
      router.push("/scan-confirm");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleUpgrade = async () => {
    setIsCheckingOut(true);
    try {
      const { checkout_url } = await billingApi.createCheckoutSession();
      window.location.href = checkout_url;
    } catch (e) {
      setIsCheckingOut(false);
    }
  };

  return (
    <div
      className="h-dvh flex flex-col overflow-hidden"
      style={{ backgroundColor: "#1a1a1a" }}
    >
      {/* ローディングオーバーレイ */}
      {isAnalyzing && (
        <div
          className="fixed inset-0 z-50 flex flex-col items-center justify-center"
          style={{ backgroundColor: "rgba(0,0,0,0.8)" }}
        >
          <svg
            className="w-10 h-10 animate-spin text-white mb-4"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z"
            />
          </svg>
          <p className="text-white text-sm">解析中...</p>
        </div>
      )}

      {/* ヘッダー */}
      <div className="flex items-center px-4 pt-12 pb-4">
        <button
          type="button"
          onClick={() => router.back()}
          className="w-9 h-9 rounded-full flex items-center justify-center mr-3"
          style={{ background: "rgba(255,255,255,0.15)" }}
        >
          <svg
            className="w-5 h-5 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 19.5 8.25 12l7.5-7.5"
            />
          </svg>
        </button>
        <h1 className="text-white text-base font-medium">書類をスキャン</h1>
      </div>

      {/* カメラプレビューエリア */}
      <div
        className="flex-1 flex items-center justify-center mx-4 rounded-2xl overflow-hidden"
        style={{ backgroundColor: "#2a2a2a" }}
      >
        <div className="text-center">
          <div className="relative w-48 h-64 mx-auto">
            <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-white rounded-tl" />
            <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-white rounded-tr" />
            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-white rounded-bl" />
            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-white rounded-br" />
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-white text-xs text-center opacity-60">
                書類を枠内に
                <br />
                合わせてください
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ボタンエリア */}
      <div className="flex items-center justify-center gap-6 px-4 py-4">
        {/* ライブラリ */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-14 h-14 rounded-2xl flex items-center justify-center"
          style={{ background: "rgba(255,255,255,0.15)" }}
        >
          <svg
            className="w-6 h-6 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
            />
          </svg>
        </button>

        {/* シャッター */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-20 h-20 rounded-full border-4 border-white flex items-center justify-center"
          style={{ background: "rgba(255,255,255,0.3)" }}
        >
          <div className="w-14 h-14 rounded-full bg-white" />
        </button>

        <div className="w-14 h-14" />
      </div>

      <p className="text-center text-xs pb-4 opacity-50 text-white">
        ライブラリから書類を選択できます
      </p>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      {showLimitModal && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center"
          style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
        >
          <div className="w-full max-w-sm bg-white rounded-t-2xl px-5 pt-6 pb-8">
            <div className="w-9 h-1 bg-gray-300 rounded-full mx-auto mb-5" />

            <div className="flex justify-center mb-4">
              <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-amber-600"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m0 3.75h.008v.008H12v-.008ZM21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                  />
                </svg>
              </div>
            </div>

            <p className="text-center text-lg font-medium mb-2">
              今月のスキャン上限に達しました
            </p>
            <p className="text-center text-sm text-gray-500 mb-5 leading-relaxed">
              無料プランは月30枚までです。
              <br />
              プレミアムプランなら上限なくスキャンできます。
            </p>

            <div className="bg-gray-50 rounded-lg px-4 py-3 mb-5">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs text-gray-500">今月のスキャン</span>
                <span className="text-xs font-medium">30 / 30枚</span>
              </div>
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full w-full bg-amber-500" />
              </div>
            </div>

            <div className="flex flex-col gap-2.5 mb-4">
              <div className="flex items-center gap-2.5">
                <svg
                  className="w-4 h-4 text-green-600 shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m4.5 12.75 6 6 9-13.5"
                  />
                </svg>
                <span className="text-sm">スキャン枚数無制限</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleUpgrade}
              disabled={isCheckingOut}
              className="w-full h-12 rounded-lg bg-gray-900 text-white text-sm font-medium mb-2.5 disabled:opacity-50"
            >
              {isCheckingOut
                ? "手続き中..."
                : "プレミアムプランにアップグレード"}
            </button>
            <button
              type="button"
              onClick={() => setShowLimitModal(false)}
              className="w-full h-11 text-sm text-gray-500"
            >
              あとで
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
