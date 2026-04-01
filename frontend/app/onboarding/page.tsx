"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import MiraLogo from "@/components/MiraLogo";
import LoadingState from "@/components/LoadingState";
import { getOnboardingQuestions, getProfile, submitOnboarding } from "@/lib/api";

interface Question {
  question_id: string;
  question_text: string;
  options: string[];
  question_type: "single_select" | "multi_select" | "free_text" | "scale";
}

const INTRO_POINTS = [
  "A few preferences now make every future look feel more personal.",
  "This takes about two quiet minutes.",
  "You can refine your profile later from inside MIRA.",
];

export default function OnboardingPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [freeTextInput, setFreeTextInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isWaitingForNarrative, setIsWaitingForNarrative] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [narrative, setNarrative] = useState("");
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    loadQuestions();
  }, []);

  async function loadQuestions() {
    try {
      const res = await getOnboardingQuestions();
      setQuestions(res.success && res.data ? res.data : FALLBACK_QUESTIONS);
    } catch {
      setQuestions(FALLBACK_QUESTIONS);
    } finally {
      setIsLoading(false);
    }
  }

  const current = questions[currentIndex];
  const progress = questions.length > 0 ? ((currentIndex + 1) / questions.length) * 100 : 0;
  const currentAnswer = current ? answers[current.question_id] : null;

  useEffect(() => {
    if (!current || current.question_type !== "free_text") {
      return;
    }
    const existing = answers[current.question_id];
    setFreeTextInput(typeof existing === "string" ? existing : "");
  }, [current, answers]);

  const canContinue = useMemo(() => {
    if (!current) return false;
    if (current.question_type === "multi_select") {
      return Array.isArray(currentAnswer) && currentAnswer.length > 0;
    }
    if (current.question_type === "free_text") {
      return freeTextInput.trim().length > 0;
    }
    return Boolean(currentAnswer);
  }, [current, currentAnswer, freeTextInput]);

  function selectOption(option: string) {
    if (!current) return;

    if (current.question_type === "multi_select") {
      const existing = answers[current.question_id] || [];
      const updated = existing.includes(option)
        ? existing.filter((item: string) => item !== option)
        : [...existing, option];
      setAnswers((state) => ({ ...state, [current.question_id]: updated }));
      return;
    }

    setAnswers((state) => ({ ...state, [current.question_id]: option }));
    setTimeout(() => advance(), 240);
  }

  function submitFreeText() {
    if (!current || !freeTextInput.trim()) return;
    setAnswers((state) => ({ ...state, [current.question_id]: freeTextInput.trim() }));
    setFreeTextInput("");
    advance();
  }

  function advance() {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((index) => index + 1);
    } else {
      handleSubmit();
    }
  }

  function goBack() {
    if (currentIndex > 0) {
      setCurrentIndex((index) => index - 1);
    }
  }

  async function handleSubmit() {
    setIsSubmitting(true);
    setSubmitError("");
    try {
      const responses = Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      }));

      const res = await submitOnboarding(responses);
      if (res.success && res.data) {
        const profileId = res.data.id;
        if (profileId) {
          localStorage.setItem("mira_profile_id", profileId);
        }
        const initialNarrative = res.data.narrative_summary?.trim();
        if (initialNarrative) {
          setNarrative(initialNarrative);
        } else if (profileId) {
          setIsWaitingForNarrative(true);
          const resolvedNarrative = await waitForNarrative(profileId);
          setNarrative(
            resolvedNarrative || "Your written profile is still being refined and will appear shortly in MIRA."
          );
        } else {
          setNarrative("Your written profile is still being refined and will appear shortly in MIRA.");
        }
        setIsComplete(true);
      } else {
        setSubmitError(res.message || "We couldn't save your profile just yet. Please try again.");
      }
    } catch {
      setSubmitError("We couldn't save your profile just yet. Please try again.");
    } finally {
      setIsWaitingForNarrative(false);
      setIsSubmitting(false);
    }
  }

  async function waitForNarrative(profileId: string) {
    for (let attempt = 0; attempt < 8; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const res = await getProfile(profileId);
      const resolvedNarrative = res.success ? res.data?.narrative_summary?.trim() : "";
      if (resolvedNarrative) {
        return resolvedNarrative;
      }
    }
    return "";
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center px-5">
        <LoadingState
          caption="Preparing your consultation"
          message="Setting the tone for a more personal MIRA."
          detail="We are getting a few style prompts ready."
        />
      </main>
    );
  }

  if (isSubmitting || isWaitingForNarrative) {
    return (
      <main className="flex min-h-screen items-center justify-center px-5">
        <LoadingState
          caption={isWaitingForNarrative ? "Finishing your profile note" : "Building your profile"}
          message={
            isWaitingForNarrative
              ? "Your preferences are saved. MIRA is finishing the written profile."
              : "MIRA is shaping your style identity."
          }
          detail={
            isWaitingForNarrative
              ? "This usually settles in within a few more seconds."
              : "This usually takes a brief moment."
          }
          steps={
            isWaitingForNarrative
              ? ["Saving your preferences", "Writing your style narrative", "Preparing your profile"]
              : ["Reviewing your preferences", "Writing your style narrative", "Preparing your profile"]
          }
          activeStep={1}
        />
      </main>
    );
  }

  if (isComplete) {
    return (
      <main className="flex min-h-screen items-center justify-center px-5 py-10">
        <motion.div
          className="mira-section w-full max-w-xl px-6 py-8 text-center sm:px-8"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <MiraLogo size="md" showTagline={false} />
          <p className="mira-overline mt-8">Your Style Identity</p>
          {narrative.startsWith("Your written profile is still being refined") ? (
            <div className="mt-5 rounded-[1.6rem] bg-white/72 px-5 py-5 text-left text-[0.98rem] leading-[1.7] text-mira-slate">
              {narrative}
            </div>
          ) : (
            <p className="mt-4 font-display text-[1.55rem] leading-[1.35] tracking-[-0.02em] text-mira-graphite sm:text-[1.9rem]">
              &ldquo;{narrative}&rdquo;
            </p>
          )}
          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            <button onClick={() => router.push("/try-on")} className="mira-btn-primary w-full">
              Visualize Your First Look
            </button>
            <button onClick={() => router.push("/profile")} className="mira-btn-secondary w-full">
              Review Profile
            </button>
          </div>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-5 pb-28 pt-6">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between gap-4">
          <Link href="/" className="inline-flex items-center gap-2 text-[0.82rem] text-mira-slate transition-colors hover:text-mira-charcoal">
            <ArrowLeft className="h-4 w-4" />
            Home
          </Link>
          <span className="text-[0.78rem] uppercase tracking-[0.18em] text-mira-slate">
            {currentIndex + 1} of {questions.length}
          </span>
        </div>

        <div className="overflow-hidden rounded-full bg-[#ece3d7]">
          <motion.div
            className="h-1.5 rounded-full bg-mira-gold"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          />
        </div>

        <section className="mira-section mt-5 overflow-hidden">
          <div className="border-b border-black/5 px-6 py-6 sm:px-8">
            <MiraLogo size="sm" showTagline={false} />
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {INTRO_POINTS.map((item) => (
                <div key={item} className="rounded-[1.3rem] bg-white/58 px-4 py-4 text-[0.84rem] leading-[1.6] text-mira-slate">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="px-6 py-8 sm:px-8 sm:py-9">
            <AnimatePresence mode="wait">
              {current && (
                <motion.div
                  key={current.question_id}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                >
                  <p className="mira-overline">A little style context</p>
                  <h1 className="mt-3 text-[2rem] leading-[1.02] tracking-[-0.04em] text-mira-charcoal sm:text-[2.45rem]">
                    {current.question_text}
                  </h1>

                  {(current.question_type === "single_select" || current.question_type === "multi_select") && (
                    <>
                      <p className="mt-4 text-body text-mira-slate">
                        {current.question_type === "multi_select"
                          ? "Choose as many as feel true. You can keep this intuitive."
                          : "Choose the direction that feels most like you."}
                      </p>
                      <div className="mt-7 flex flex-wrap gap-3">
                        {current.options.map((option) => {
                          const selected =
                            current.question_type === "multi_select"
                              ? (answers[current.question_id] || []).includes(option)
                              : answers[current.question_id] === option;

                          return (
                            <motion.button
                              key={option}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => selectOption(option)}
                              className={`rounded-[1.4rem] border px-4 py-3 text-left text-[0.95rem] leading-[1.45] transition-all duration-200 ${
                                selected
                                  ? "border-mira-charcoal bg-mira-charcoal text-white shadow-elevated"
                                  : "border-black/6 bg-white/70 text-mira-graphite"
                              }`}
                            >
                              {option}
                            </motion.button>
                          );
                        })}
                      </div>
                    </>
                  )}

                  {current.question_type === "free_text" && (
                    <div className="mt-7">
                      <p className="mb-3 text-body text-mira-slate">
                        {current.question_id === "name"
                          ? "First name is enough."
                          : "A short note is enough. MIRA only needs the useful signal."}
                      </p>
                      <textarea
                        value={freeTextInput}
                        onChange={(event) => setFreeTextInput(event.target.value)}
                        placeholder={current.question_id === "name" ? "Your name" : "Write a brief note..."}
                        className="mira-input min-h-[160px] resize-none"
                        autoFocus
                      />
                    </div>
                  )}

                  {submitError && currentIndex === questions.length - 1 && (
                    <div className="mt-6 rounded-[1.4rem] border border-mira-rose/25 bg-mira-rose/5 px-4 py-3 text-body text-mira-rose-muted">
                      {submitError}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-black/5 bg-[#fbf8f2]/92 px-5 pb-[calc(env(safe-area-inset-bottom,0px)+0.9rem)] pt-3 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-2xl items-center gap-3">
          <button
            onClick={goBack}
            disabled={currentIndex === 0}
            className="mira-btn-secondary min-w-[6.5rem] disabled:opacity-30"
          >
            Back
          </button>

          {current?.question_type === "free_text" ? (
            <button
              onClick={submitFreeText}
              disabled={!canContinue}
              className="mira-btn-primary flex-1"
            >
              {currentIndex === questions.length - 1 ? "Complete Profile" : "Continue"}
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : current?.question_type === "multi_select" ? (
            <button
              onClick={advance}
              disabled={!canContinue}
              className="mira-btn-primary flex-1"
            >
              {currentIndex === questions.length - 1 ? "Complete Profile" : "Continue"}
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <div className="flex-1 rounded-full bg-[#f2eadf] px-4 py-3 text-center text-[0.82rem] text-mira-slate">
              Tap one answer to continue
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

const FALLBACK_QUESTIONS: Question[] = [
  {
    question_id: "name",
    question_text: "What should MIRA call you?",
    options: [],
    question_type: "free_text",
  },
  {
    question_id: "aesthetic",
    question_text: "Which feels most like you?",
    options: ["Effortless", "Sculpted", "Romantic", "Sharp", "Minimal", "Dramatic"],
    question_type: "single_select",
  },
  {
    question_id: "silhouette",
    question_text: "Do you usually like your clothes to skim the body, define the waist, or fall away more fluidly?",
    options: ["Skim the body", "Define the waist", "Fall away fluidly", "It depends on the occasion"],
    question_type: "single_select",
  },
  {
    question_id: "dressing_for",
    question_text: "Are you dressing more for confidence, elegance, playfulness, power, or ease?",
    options: ["Confidence", "Elegance", "Playfulness", "Power", "Ease"],
    question_type: "multi_select",
  },
  {
    question_id: "colors_love",
    question_text: "What colours make you feel most like yourself?",
    options: ["Rich jewel tones", "Soft neutrals", "Bold brights", "Earth tones", "Pastels", "Monochromes", "Metallics"],
    question_type: "multi_select",
  },
  {
    question_id: "colors_avoid",
    question_text: "Are there any colours you tend to shy away from?",
    options: [],
    question_type: "free_text",
  },
  {
    question_id: "occasions",
    question_text: "What are you most often dressing for?",
    options: ["Work", "Evenings out", "Weddings & celebrations", "Festive occasions", "Everyday elevated", "Travel", "Date nights", "Special events"],
    question_type: "multi_select",
  },
  {
    question_id: "comfort_statement",
    question_text: "On a given day, do you lean more toward comfort or making a statement?",
    options: ["Mostly comfort", "Slightly comfort", "Balance of both", "Slightly statement", "Mostly statement"],
    question_type: "single_select",
  },
  {
    question_id: "modesty",
    question_text: "Do you have any modesty or coverage preferences we should keep in mind?",
    options: ["Full coverage preferred", "Moderate coverage", "No specific preference", "I'll specify per occasion"],
    question_type: "single_select",
  },
  {
    question_id: "luxury_preference",
    question_text: "Where does your wardrobe tend to live?",
    options: ["Luxury / designer", "Contemporary / premium", "High street / accessible", "A thoughtful mix"],
    question_type: "single_select",
  },
  {
    question_id: "style_goal",
    question_text: "If MIRA could help you with one thing, what would it be?",
    options: [],
    question_type: "free_text",
  },
];
