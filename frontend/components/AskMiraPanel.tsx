"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { askStylist, synthesizeVoice } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const QUICK_QUESTIONS = [
  "Would this work for dinner?",
  "What shoes would you pair with this?",
  "How would you make this feel more elevated?",
];

function resolveAudioUrl(url: string) {
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  if (url.startsWith("/")) {
    return `${API_BASE}${url}`;
  }
  return url;
}

export default function AskMiraPanel({
  lookImageUrl,
  commentaryPayload,
  occasion,
  garmentBrand,
  garmentFit,
}: {
  lookImageUrl: string;
  commentaryPayload?: Record<string, any> | null;
  occasion?: string;
  garmentBrand?: string;
  garmentFit?: string;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [suggestedFollowUp, setSuggestedFollowUp] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isVoiceLoading, setIsVoiceLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  async function playAnswer(text: string) {
    if (!text) return;
    setIsVoiceLoading(true);
    const res = await synthesizeVoice(text, "warm");
    if (res.success && res.data?.audio_url) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      const audio = new Audio(resolveAudioUrl(res.data.audio_url));
      audioRef.current = audio;
      audio.onplay = () => {
        setIsSpeaking(true);
        setIsVoiceLoading(false);
      };
      audio.onended = () => {
        setIsSpeaking(false);
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        setIsVoiceLoading(false);
      };
      await audio.play().catch(() => {
        setIsSpeaking(false);
        setIsVoiceLoading(false);
      });
    } else {
      setIsVoiceLoading(false);
    }
  }

  function stopAudio() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsSpeaking(false);
  }

  async function handleAsk(submittedQuestion?: string) {
    const nextQuestion = (submittedQuestion || question).trim();
    if (!nextQuestion || isLoading) return;

    setQuestion(nextQuestion);
    setIsLoading(true);
    setError("");
    setSuggestedFollowUp("");

    const profileId =
      typeof window !== "undefined"
        ? localStorage.getItem("mira_profile_id") || undefined
        : undefined;

    const res = await askStylist({
      question: nextQuestion,
      look_image_url: lookImageUrl,
      user_profile_id: profileId,
      garment_brand: garmentBrand,
      garment_fit: garmentFit,
      occasion,
      commentary_payload: commentaryPayload || undefined,
    });

    if (res.success && res.data?.answer) {
      const nextAnswer = res.data.answer;
      setAnswer(nextAnswer);
      setSuggestedFollowUp(res.data.suggested_follow_up || "");
      await playAnswer(nextAnswer);
    } else {
      setError(res.message || "MIRA couldn't answer that just yet.");
    }

    setIsLoading(false);
  }

  return (
    <div className="mira-card-elevated p-5 space-y-4 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <p className="mira-overline">Ask MIRA</p>
        {(isSpeaking || isVoiceLoading) && (
          <span className="text-caption text-mira-gold">
            {isVoiceLoading ? "Preparing voice" : "Speaking now"}
          </span>
        )}
      </div>

      <p className="text-body text-mira-slate">
        Ask a follow-up about the look and MIRA will answer in a more conversational tone.
      </p>

      <div className="flex flex-wrap gap-2">
        {QUICK_QUESTIONS.map((item) => (
          <button
            key={item}
            onClick={() => handleAsk(item)}
            className="mira-tag cursor-pointer hover:bg-[#f4ece1]"
            disabled={isLoading}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask MIRA about shoes, polish, occasion, or what to change next..."
          rows={3}
          className="mira-input min-h-[110px]"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => handleAsk()}
            disabled={!question.trim() || isLoading}
            className="mira-btn-gold"
          >
            {isLoading ? "Asking MIRA..." : "Ask MIRA"}
          </button>
          {answer && !isSpeaking && (
            <button
              onClick={() => playAnswer(answer)}
              className="mira-btn-secondary"
            >
              Speak Again
            </button>
          )}
          {isSpeaking && (
            <button
              onClick={stopAudio}
              className="mira-btn-secondary"
            >
              Stop Voice
            </button>
          )}
        </div>
      </div>

      {error && (
        <p className="text-body text-mira-rose-muted">{error}</p>
      )}

      {answer && (
        <motion.div
          className="rounded-[1.5rem] border border-black/5 bg-[#f8f3ec] p-4 space-y-3"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-body text-mira-charcoal leading-relaxed">{answer}</p>
          {suggestedFollowUp && (
            <button
              onClick={() => handleAsk(suggestedFollowUp)}
              className="text-caption text-mira-gold hover:underline"
            >
              Next: {suggestedFollowUp}
            </button>
          )}
        </motion.div>
      )}
    </div>
  );
}
