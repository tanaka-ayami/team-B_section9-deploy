"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

export default function ScanPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleFile = async (file: File) => {
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/v1/documents/scan", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("scan failed");

      const data = await res.json();
      sessionStorage.setItem("scanResult", JSON.stringify(data));
      router.push("/scan-confirm");
    } catch (e) {
      sessionStorage.setItem("scanResult", JSON.stringify({
        image_url: null,
        ai_analysis: null,
      }));
      router.push("/scan-confirm");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#1a1a1a" }}>
      {/* ローディングオーバーレイ */}
      {isAnalyzing && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center"
          style={{ backgroundColor: "rgba(0,0,0,0.8)" }}>
          <svg className="w-10 h-10 animate-spin text-white mb-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4Z"/>
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
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5"/>
          </svg>
        </button>
        <h1 className="text-white text-base font-medium">書類をスキャン</h1>
      </div>

      {/* カメラプレビューエリア */}
      <div className="flex-1 flex items-center justify-center mx-4 rounded-2xl overflow-hidden"
        style={{ backgroundColor: "#2a2a2a", minHeight: "50vh" }}>
        <div className="text-center">
          <div className="relative w-48 h-64 mx-auto">
            <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-white rounded-tl"/>
            <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-white rounded-tr"/>
            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-white rounded-bl"/>
            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-white rounded-br"/>
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-white text-xs text-center opacity-60">
                書類を枠内に<br/>合わせてください
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ボタンエリア */}
      <div className="flex items-center justify-center gap-8 px-4 py-8">
        {/* ライブラリ */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-14 h-14 rounded-2xl flex items-center justify-center"
          style={{ background: "rgba(255,255,255,0.15)" }}
        >
          <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"/>
          </svg>
        </button>

        {/* シャッター */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-20 h-20 rounded-full border-4 border-white flex items-center justify-center"
          style={{ background: "rgba(255,255,255,0.3)" }}
        >
          <div className="w-14 h-14 rounded-full bg-white"/>
        </button>

        <div className="w-14 h-14"/>
      </div>

      <p className="text-center text-xs pb-8 opacity-50 text-white">
        ライブラリから書類を選択できます
      </p>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}