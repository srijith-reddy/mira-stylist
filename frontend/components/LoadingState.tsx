"use client";

import { motion } from "framer-motion";

interface LoadingStateProps {
  caption?: string;
  message?: string;
  detail?: string;
  steps?: string[];
  activeStep?: number;
}

export default function LoadingState({
  caption = "MIRA is at work",
  message = "Preparing something beautiful...",
  detail,
  steps,
  activeStep = 0,
}: LoadingStateProps) {
  return (
    <motion.div
      className="mx-auto flex w-full max-w-md flex-col items-center justify-center gap-6 rounded-[2rem] border border-black/5 bg-white/70 px-6 py-10 text-center shadow-[0_18px_50px_rgba(40,28,18,0.07)]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="relative h-14 w-14">
        <motion.div
          className="absolute inset-0 rounded-full border border-mira-sand/80"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute inset-[5px] rounded-full border border-mira-gold/35"
          animate={{ rotate: -360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
        <div className="absolute inset-[14px] rounded-full bg-mira-gold/18 animate-shimmer" />
      </div>

      <div className="space-y-3">
        <p className="mira-overline">{caption}</p>
        <p className="font-display text-[1.5rem] leading-[1.18] tracking-[-0.03em] text-mira-charcoal">
          {message}
        </p>
        {detail && (
          <p className="text-body text-mira-slate">{detail}</p>
        )}
      </div>

      {steps && steps.length > 0 && (
        <div className="w-full space-y-3 pt-2 text-left">
          {steps.map((step, index) => {
            const isDone = index < activeStep;
            const isActive = index === activeStep;
            return (
              <div
                key={step}
                className="flex items-center gap-3 rounded-full bg-[#f6f0e7] px-4 py-3"
              >
                <div
                  className={`h-2.5 w-2.5 rounded-full ${
                    isDone
                      ? "bg-mira-charcoal"
                      : isActive
                      ? "bg-mira-gold animate-pulse"
                      : "bg-mira-sand"
                  }`}
                />
                <span
                  className={`text-[0.86rem] ${
                    isActive || isDone ? "text-mira-charcoal" : "text-mira-slate"
                  }`}
                >
                  {step}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
