"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { synthesizeVoice, getWelcomeVoice } from "@/lib/api";

interface VoiceModeProps {
  text?: string;
  autoPlay?: boolean;
  title?: string;
  variant?: "floating" | "inline";
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function resolveAudioUrl(url: string) {
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/")) return `${API_BASE}${url}`;
  return url;
}

export default function VoiceMode({
  text,
  autoPlay = false,
  title = "MIRA",
  variant = "floating",
}: VoiceModeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastAutoPlayedTextRef = useRef("");

  useEffect(() => {
    if (autoPlay && text && text !== lastAutoPlayedTextRef.current) {
      lastAutoPlayedTextRef.current = text;
      handleSpeak(text);
    }
  }, [autoPlay, text]);

  async function handleSpeak(content?: string) {
    const speakText = content || text;
    if (!speakText) return;

    setIsLoading(true);
    setIsOpen(true);

    const res = await synthesizeVoice(speakText, "warm");
    if (res.success && res.data?.audio_url) {
      audioRef.current?.pause();
      const audio = new Audio(resolveAudioUrl(res.data.audio_url));
      audioRef.current = audio;
      audio.onplay = () => { setIsPlaying(true); setIsLoading(false); };
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => { setIsPlaying(false); setIsLoading(false); };
      audio.play().catch(() => { setIsPlaying(false); setIsLoading(false); });
    } else {
      setIsLoading(false);
    }
  }

  async function handleWelcome() {
    setIsLoading(true);
    setIsOpen(true);
    const userName = typeof window !== "undefined" ? localStorage.getItem("mira_user_name") || undefined : undefined;
    const res = await getWelcomeVoice(userName);
    if (res.success && res.data?.audio_url) {
      const audio = new Audio(resolveAudioUrl(res.data.audio_url));
      audioRef.current = audio;
      audio.onplay = () => { setIsPlaying(true); setIsLoading(false); };
      audio.onended = () => setIsPlaying(false);
      audio.play().catch(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }

  function handleStop() {
    audioRef.current?.pause();
    if (audioRef.current) audioRef.current.currentTime = 0;
    setIsPlaying(false);
    setIsOpen(false);
  }

  function handleToggle() {
    if (isPlaying || isLoading) {
      handleStop();
    } else if (isOpen) {
      setIsOpen(false);
    } else {
      text ? handleSpeak() : handleWelcome();
    }
  }

  // ── Inline variant ──────────────────────────────────────────────────────
  if (variant === "inline") {
    return (
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-[2px]">
          {[0, 0.1, 0.2].map((delay, i) => (
            <motion.div
              key={i}
              className="w-[2px] rounded-full bg-mira-gold"
              animate={
                isPlaying
                  ? { height: [3, 10, 3], opacity: [0.5, 1, 0.5] }
                  : { height: 3, opacity: 0.3 }
              }
              transition={
                isPlaying
                  ? { duration: 0.7, delay, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0.2 }
              }
            />
          ))}
        </div>
        <button
          onClick={handleToggle}
          className="text-caption text-mira-slate hover:text-mira-gold transition-colors"
        >
          {isLoading ? "Composing…" : isPlaying ? "Pause" : "Hear MIRA"}
        </button>
        {!isLoading && !isPlaying && isOpen && text && (
          <button
            onClick={() => handleSpeak()}
            className="text-caption text-mira-gold/70 hover:text-mira-gold transition-colors"
          >
            · Replay
          </button>
        )}
      </div>
    );
  }

  // ── Floating variant (default) ──────────────────────────────────────────
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-3">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="flex items-center gap-4 bg-mira-charcoal/95 backdrop-blur-md text-white rounded-full px-6 py-3 shadow-2xl"
          >
            <div className="flex items-center gap-[3px]">
              {[0, 0.1, 0.2, 0.1, 0].map((delay, i) => (
                <motion.div
                  key={i}
                  className="w-[3px] rounded-full bg-mira-gold"
                  animate={
                    isPlaying
                      ? { height: [4, 14, 4], opacity: [0.6, 1, 0.6] }
                      : { height: 4, opacity: 0.3 }
                  }
                  transition={
                    isPlaying
                      ? { duration: 0.7, delay, repeat: Infinity, ease: "easeInOut" }
                      : { duration: 0.2 }
                  }
                />
              ))}
            </div>

            <span className="text-[13px] font-medium tracking-wide text-white/90">
              {isLoading ? "Composing…" : isPlaying ? "MIRA speaking" : "MIRA"}
            </span>

            {!isLoading && !isPlaying && text && (
              <button
                onClick={() => handleSpeak()}
                className="text-[12px] text-mira-gold/80 hover:text-mira-gold transition-colors"
              >
                Replay
              </button>
            )}

            <div className="w-px h-4 bg-white/20" />

            <button
              onClick={handleStop}
              className="text-white/50 hover:text-white transition-colors"
              aria-label="Stop"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {!isOpen && (
        <motion.button
          onClick={handleToggle}
          className="flex items-center gap-2.5 bg-mira-charcoal text-white rounded-full pl-4 pr-5 py-2.5 shadow-xl hover:bg-mira-graphite transition-colors duration-200"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-mira-gold" />
          <span className="text-[13px] font-medium tracking-wide">
            {text ? "Hear MIRA's take" : "MIRA Voice"}
          </span>
        </motion.button>
      )}
    </div>
  );
}
