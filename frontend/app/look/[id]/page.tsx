"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Heart } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Navigation from "@/components/Navigation";
import LoadingState from "@/components/LoadingState";
import AskMiraPanel from "@/components/AskMiraPanel";
import VoiceMode from "@/components/VoiceMode";
import {
  explainSize,
  generateCommentary,
  generateMotion,
  getLook,
  toggleFavorite,
} from "@/lib/api";

interface Look {
  look_id: string;
  try_on_image_url: string;
  source_garment_url: string;
  stylist_commentary: string;
  commentary_payload?: any;
  recommended_size: any;
  fit_notes: string;
  garment_brand?: string;
  garment_fit?: string;
  vibe_tags: string[];
  occasion_tags: string[];
  is_favorite: boolean;
  animated_clip_url: string | null;
  created_at: string;
}

const COMMENTARY_MODES = [
  { key: "concise_luxury", label: "Concise" },
  { key: "editorial_breakdown", label: "Editorial" },
  { key: "fit_focused", label: "Fit" },
  { key: "occasion_stylist", label: "Occasion" },
];

const MOTION_PRESETS = [
  { key: "editorial_turn", label: "Editorial Turn" },
  { key: "subtle_idle", label: "Subtle Idle" },
  { key: "runway_step", label: "Runway Step" },
];

const ACCORDION_SECTIONS = [
  { key: "fit_assessment", label: "Fit Assessment" },
  { key: "silhouette_line", label: "Silhouette & Line" },
  { key: "proportion", label: "Proportion" },
  { key: "occasion_read", label: "Occasion Read" },
  { key: "colour_surface", label: "Colour & Surface" },
  { key: "to_elevate_it", label: "To Elevate It" },
  { key: "tailoring_note", label: "Tailoring Note" },
];

function firstSentence(value?: string, maxWords = 24) {
  if (!value) return "";
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) return "";
  const match = normalized.match(/.+?[.!?](?:\s|$)/);
  const sentence = (match ? match[0] : normalized).trim();
  const words = sentence.split(" ");
  return words.length > maxWords ? `${words.slice(0, maxWords).join(" ")}...` : sentence;
}

function clampWords(value: string, maxWords = 48) {
  const words = value.replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
  return words.length > maxWords ? `${words.slice(0, maxWords).join(" ")}...` : words.join(" ");
}

function buildConversationalVoiceScript(commentary: string, commentaryPayload: any) {
  const lead =
    firstSentence(commentaryPayload?.text || commentary, 26) ||
    firstSentence(commentary, 26);
  const refinement =
    firstSentence(commentaryPayload?.to_elevate_it, 18) ||
    (Array.isArray(commentaryPayload?.complete_the_look) && commentaryPayload.complete_the_look.length > 0
      ? `I would complete the look with ${commentaryPayload.complete_the_look[0]}.`
      : "");
  const occasionBeat = firstSentence(commentaryPayload?.occasion_read, 16);

  return clampWords(["Here is my take.", lead, refinement, occasionBeat].filter(Boolean).join(" "), 48);
}

export default function LookDetailPage() {
  const params = useParams();
  const lookId = params.id as string;

  const [look, setLook] = useState<Look | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCommentaryMode, setActiveCommentaryMode] = useState("concise_luxury");
  const [commentary, setCommentary] = useState("");
  const [commentaryPayload, setCommentaryPayload] = useState<any>(null);
  const [isLoadingCommentary, setIsLoadingCommentary] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [motionError, setMotionError] = useState("");
  const [selectedPreset, setSelectedPreset] = useState("editorial_turn");
  const [sizeExplanation, setSizeExplanation] = useState<any>(null);
  const [openSection, setOpenSection] = useState<string | null>(null);

  const vibeTags =
    Array.isArray(commentaryPayload?.vibe_tags) && commentaryPayload.vibe_tags.length > 0
      ? (commentaryPayload.vibe_tags as string[]).filter(Boolean).slice(0, 5)
      : look?.vibe_tags || [];

  const occasionTags =
    Array.isArray(commentaryPayload?.occasion_tags) && commentaryPayload.occasion_tags.length > 0
      ? (commentaryPayload.occasion_tags as string[]).filter(Boolean).slice(0, 4)
      : look?.occasion_tags || [];

  const voiceScript = commentary ? buildConversationalVoiceScript(commentary, commentaryPayload) : "";

  useEffect(() => {
    loadLook();
  }, [lookId]);

  useEffect(() => {
    if (commentaryPayload && openSection === null) {
      const first = ACCORDION_SECTIONS.find((section) => Boolean(commentaryPayload?.[section.key]));
      if (first) setOpenSection(first.key);
    }
  }, [commentaryPayload, openSection]);

  async function loadLook() {
    const res = await getLook(lookId);
    if (res.success && res.data) {
      setLook(res.data);
      setCommentary(res.data.stylist_commentary || "");
      setCommentaryPayload(res.data.commentary_payload || null);
    }
    setIsLoading(false);
  }

  async function handleToggleFavorite() {
    const res = await toggleFavorite(lookId);
    if (res.success && res.data) {
      setLook(res.data);
    }
  }

  async function handleRegenerateCommentary(mode: string) {
    if (!look) return;
    setActiveCommentaryMode(mode);
    setIsLoadingCommentary(true);
    const res = await generateCommentary({
      look_image_url: look.try_on_image_url,
      mode,
      user_profile_id: localStorage.getItem("mira_profile_id") || undefined,
    });
    if (res.success && res.data) {
      setCommentary(res.data.text || "");
      setCommentaryPayload(res.data);
    }
    setIsLoadingCommentary(false);
  }

  async function handleAnimate() {
    if (!look) return;
    setIsAnimating(true);
    setMotionError("");
    const res = await generateMotion({
      look_id: look.look_id,
      source_image_url: look.try_on_image_url,
      motion_preset: selectedPreset,
    });
    if (res.success && res.data) {
      setLook({ ...look, animated_clip_url: res.data.video_url });
    } else {
      setMotionError(res.message || "The motion didn't come together this time.");
    }
    setIsAnimating(false);
  }

  async function handleExplainSize() {
    const profileId = localStorage.getItem("mira_profile_id");
    if (!profileId) return;
    const res = await explainSize({
      user_profile_id: profileId,
      garment_category: "tops",
      brand: look?.garment_brand,
    });
    if (res.success && res.data) {
      setSizeExplanation(res.data);
    }
  }

  if (isLoading) {
    return (
      <>
        <Navigation />
        <main className="flex min-h-screen items-center justify-center px-5 pt-20">
          <LoadingState caption="Opening the look" message="Gathering the image, notes, and saved styling context." />
        </main>
      </>
    );
  }

  if (!look) {
    return (
      <>
        <Navigation />
        <main className="flex min-h-screen items-center justify-center px-5 pt-20">
          <div className="mira-section max-w-md px-6 py-8 text-center">
            <h2 className="text-heading text-mira-charcoal">Look not found</h2>
            <p className="mt-3 text-body text-mira-slate">This saved look is no longer available.</p>
            <Link href="/wardrobe" className="mira-btn-primary mt-8 inline-flex">
              Back to Wardrobe
            </Link>
          </div>
        </main>
      </>
    );
  }

  const completeTheLook = Array.isArray(commentaryPayload?.complete_the_look)
    ? (commentaryPayload.complete_the_look as string[]).filter(Boolean).slice(0, 4)
    : [];

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-20 pb-14">
        <div className="mira-container">
          <div className="mb-6">
            <Link href="/wardrobe" className="text-[0.8rem] text-mira-slate transition-colors hover:text-mira-charcoal">
              &larr; Back to Wardrobe
            </Link>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
            <div className="space-y-5">
              <motion.div className="mira-card-elevated overflow-hidden p-4 sm:p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                <div className="relative overflow-hidden rounded-[1.8rem] bg-[#eee3d4]">
                  <img src={look.try_on_image_url} alt="Styled look" className="aspect-[4/5] w-full object-cover object-top" />
                </div>

                {look.animated_clip_url && (
                  <div className="mt-4 overflow-hidden rounded-[1.6rem] bg-[#eee3d4]">
                    <video
                      src={look.animated_clip_url}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="aspect-[4/5] w-full object-cover object-top"
                    />
                  </div>
                )}
              </motion.div>

              {!look.animated_clip_url && (
                <div className="mira-card p-5 sm:p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="mira-overline">Motion</p>
                      <h2 className="mt-2 text-heading text-mira-charcoal">Bring this look to life</h2>
                    </div>
                  </div>
                  {motionError && (
                    <div className="mt-4 rounded-[1.2rem] border border-mira-rose/20 bg-mira-rose/5 px-4 py-3 text-body text-mira-rose-muted">
                      {motionError}
                    </div>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {MOTION_PRESETS.map((preset) => (
                      <button
                        key={preset.key}
                        onClick={() => setSelectedPreset(preset.key)}
                        className={`rounded-full px-4 py-2.5 text-[0.82rem] transition-all ${
                          selectedPreset === preset.key ? "bg-mira-charcoal text-white" : "bg-[#f7f1e8] text-mira-slate"
                        }`}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                  <button onClick={handleAnimate} disabled={isAnimating} className="mira-btn-primary mt-5">
                    {isAnimating ? "Creating motion..." : "Generate Motion"}
                  </button>
                </div>
              )}
            </div>

            <div className="space-y-5">
              <div className="mira-section px-6 py-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="mira-overline">Saved Look</p>
                    <h1 className="mt-2 text-[2rem] leading-[1] tracking-[-0.04em] text-mira-charcoal sm:text-[2.4rem]">
                      Kept for later.
                    </h1>
                  </div>
                  <button onClick={handleToggleFavorite} className="inline-flex items-center gap-2 text-body text-mira-slate">
                    <Heart className={`h-4 w-4 ${look.is_favorite ? "fill-current text-mira-rose" : ""}`} />
                    {look.is_favorite ? "Favorited" : "Add to favorites"}
                  </button>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {occasionTags.map((tag) => (
                    <span key={tag} className="mira-tag">
                      {tag}
                    </span>
                  ))}
                  {vibeTags.map((tag) => (
                    <span key={tag} className="mira-tag mira-tag-gold">
                      {tag}
                    </span>
                  ))}
                </div>
                <p className="mt-4 text-[0.8rem] uppercase tracking-[0.16em] text-mira-slate">
                  Saved {new Date(look.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
                </p>
              </div>

              <div className="mira-card-elevated p-6">
                <div className="flex items-center justify-between gap-3">
                  <p className="mira-overline">MIRA&apos;s Perspective</p>
                  {voiceScript && <VoiceMode text={voiceScript} title="MIRA Speaking" variant="inline" />}
                </div>

                {isLoadingCommentary ? (
                  <div className="mt-4 space-y-3">
                    <div className="h-6 animate-pulse rounded-full bg-[#eadfd1]" />
                    <div className="h-6 w-[88%] animate-pulse rounded-full bg-[#eadfd1]" />
                    <div className="h-6 w-[72%] animate-pulse rounded-full bg-[#eadfd1]" />
                  </div>
                ) : (
                  <p className="mt-4 font-display text-[1.5rem] leading-[1.35] tracking-[-0.02em] text-mira-charcoal">
                    &ldquo;{commentary}&rdquo;
                  </p>
                )}

                <div className="mt-5 flex flex-wrap gap-2">
                  {COMMENTARY_MODES.map((mode) => (
                    <button
                      key={mode.key}
                      onClick={() => handleRegenerateCommentary(mode.key)}
                      className={`rounded-full px-4 py-2 text-[0.78rem] transition-all ${
                        activeCommentaryMode === mode.key ? "bg-mira-charcoal text-white" : "bg-[#f7f1e8] text-mira-slate"
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>

              {completeTheLook.length > 0 && (
                <div className="mira-card p-5">
                  <p className="mira-overline">Complete the look</p>
                  <div className="mt-4 space-y-2.5">
                    {completeTheLook.map((item) => (
                      <div key={item} className="rounded-[1.2rem] bg-[#f7f1e8] px-4 py-3 text-[0.9rem] text-mira-graphite">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {look.recommended_size && (
                <div className="mira-card p-5">
                  <p className="mira-overline">Suggested fit</p>
                  <div className="mt-4 flex items-start gap-4">
                    <span className="font-display text-[2.1rem] leading-none tracking-[-0.05em] text-mira-charcoal">
                      {look.recommended_size.recommended_size || look.recommended_size}
                    </span>
                    <div>
                      <p className="text-[0.9rem] leading-[1.6] text-mira-graphite">
                        {look.recommended_size.reason_summary || "Saved with this look."}
                      </p>
                      <button onClick={handleExplainSize} className="mt-3 text-[0.82rem] text-mira-gold">
                        Why this size?
                      </button>
                    </div>
                  </div>
                  {sizeExplanation && (
                    <div className="mt-4 rounded-[1.2rem] bg-[#f7f1e8] px-4 py-4 text-[0.88rem] leading-[1.65] text-mira-graphite">
                      {sizeExplanation.reason}
                    </div>
                  )}
                </div>
              )}

              {ACCORDION_SECTIONS.filter((section) => Boolean(commentaryPayload?.[section.key])).length > 0 && (
                <div className="mira-card-elevated overflow-hidden">
                  {ACCORDION_SECTIONS.filter((section) => Boolean(commentaryPayload?.[section.key])).map((section, index) => (
                    <div key={section.key} className={index > 0 ? "border-t border-black/5" : ""}>
                      <button
                        onClick={() => setOpenSection(openSection === section.key ? null : section.key)}
                        className="flex w-full items-center justify-between px-5 py-4 text-left"
                      >
                        <span className="text-[0.78rem] uppercase tracking-[0.16em] text-mira-slate">
                          {section.label}
                        </span>
                        <motion.span animate={{ rotate: openSection === section.key ? 180 : 0 }}>
                          <ChevronDown className="h-4 w-4 text-mira-slate" />
                        </motion.span>
                      </button>
                      <AnimatePresence initial={false}>
                        {openSection === section.key && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.22 }}
                            className="overflow-hidden"
                          >
                            <p className="px-5 pb-5 text-[0.94rem] leading-[1.7] text-mira-graphite">
                              {commentaryPayload?.[section.key]}
                            </p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              )}

              <AskMiraPanel
                lookImageUrl={look.try_on_image_url}
                commentaryPayload={commentaryPayload}
                occasion={occasionTags[0]}
                garmentBrand={look.garment_brand}
                garmentFit={look.garment_fit}
              />
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
