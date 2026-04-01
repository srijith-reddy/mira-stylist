"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, ReactNode, RefObject } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Film,
  ImagePlus,
  Sparkles,
  Wand2,
} from "lucide-react";
import Navigation from "@/components/Navigation";
import LoadingState from "@/components/LoadingState";
import VoiceMode from "@/components/VoiceMode";
import AskMiraPanel from "@/components/AskMiraPanel";
import {
  generateCommentary,
  generateMotion,
  getProfile,
  recommendSize,
  runTryOn,
  saveLook,
} from "@/lib/api";

type Stage = "upload" | "processing" | "result";

type Profile = {
  id: string;
  name: string;
  gender?: string | null;
  height_cm?: number | null;
  brand_size_references?: { category: string; brand: string; size: string }[];
};

const MOTION_PRESETS = [
  {
    key: "editorial_turn",
    label: "Editorial Turn",
    description: "A composed turn with soft fabric response and campaign energy.",
  },
  {
    key: "subtle_idle",
    label: "Subtle Idle",
    description: "A quiet showroom-style movement with almost no drift.",
  },
  {
    key: "runway_step",
    label: "Runway Step",
    description: "One poised forward step with a more directional feel.",
  },
];

const OCCASION_OPTIONS = [
  "Daily wear",
  "Work",
  "Date night",
  "Dinner",
  "Travel",
  "Wedding guest",
  "Festive occasion",
  "Special event",
];

const GARMENT_FIT_OPTIONS = [
  "Not sure",
  "Regular",
  "Slim",
  "Relaxed",
  "Oversized",
  "Tailored",
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

function buildVoiceScript({
  commentary,
  commentaryPayload,
  occasion,
  garmentBrand,
}: {
  commentary: string;
  commentaryPayload: any;
  occasion?: string;
  garmentBrand?: string;
}) {
  const lead =
    firstSentence(commentaryPayload?.text || commentary, 26) ||
    firstSentence(commentary, 26);
  const refinement =
    firstSentence(commentaryPayload?.to_elevate_it, 18) ||
    (Array.isArray(commentaryPayload?.complete_the_look) && commentaryPayload.complete_the_look.length > 0
      ? `I would finish it with ${commentaryPayload.complete_the_look[0]}.`
      : "");
  const context = occasion
    ? `Best for ${occasion.toLowerCase()}.`
    : garmentBrand
    ? `${garmentBrand} is carrying the look nicely here.`
    : "";

  return clampWords(["Here is my quick read.", lead, refinement, context].filter(Boolean).join(" "), 48);
}

export default function TryOnPage() {
  const [stage, setStage] = useState<Stage>("upload");
  const [personImage, setPersonImage] = useState("");
  const [garmentImage, setGarmentImage] = useState("");
  const [personPreview, setPersonPreview] = useState("");
  const [garmentPreview, setGarmentPreview] = useState("");
  const [result, setResult] = useState<any>(null);
  const [commentary, setCommentary] = useState("");
  const [commentaryPayload, setCommentaryPayload] = useState<any>(null);
  const [sizeRec, setSizeRec] = useState<any>(null);
  const [error, setError] = useState("");
  const [isSaved, setIsSaved] = useState(false);
  const [savedLookId, setSavedLookId] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [occasion, setOccasion] = useState("Daily wear");
  const [garmentBrand, setGarmentBrand] = useState("Zara");
  const [garmentFit, setGarmentFit] = useState("Not sure");
  const [motionEnabled, setMotionEnabled] = useState(false);
  const [motionPreset, setMotionPreset] = useState("editorial_turn");
  const [motionUrl, setMotionUrl] = useState("");
  const [isAnimating, setIsAnimating] = useState(false);
  const [openSection, setOpenSection] = useState<string | null>(null);
  const [perspectiveExpanded, setPerspectiveExpanded] = useState(false);

  const personInputRef = useRef<HTMLInputElement>(null);
  const garmentInputRef = useRef<HTMLInputElement>(null);

  const profileId = typeof window !== "undefined" ? localStorage.getItem("mira_profile_id") : null;

  useEffect(() => {
    loadProfile();
  }, []);

  useEffect(() => {
    if (commentaryPayload && openSection === null) {
      const first = ACCORDION_SECTIONS.find((section) => Boolean(commentaryPayload?.[section.key]));
      if (first) setOpenSection(first.key);
    }
  }, [commentaryPayload, openSection]);

  async function loadProfile() {
    if (!profileId) return;
    const res = await getProfile(profileId);
    if (res.success && res.data) {
      const nextProfile = res.data as Profile;
      setProfile(nextProfile);
      if (nextProfile.brand_size_references?.[0]?.brand) {
        setGarmentBrand(nextProfile.brand_size_references[0].brand);
      }
    }
  }

  function handleFileSelect(
    event: ChangeEvent<HTMLInputElement>,
    type: "person" | "garment"
  ) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const dataUrl = loadEvent.target?.result as string;
      if (type === "person") {
        setPersonImage(dataUrl);
        setPersonPreview(dataUrl);
      } else {
        setGarmentImage(dataUrl);
        setGarmentPreview(dataUrl);
      }
    };
    reader.readAsDataURL(file);
  }

  function handleUrlInput(url: string, type: "person" | "garment") {
    if (type === "person") {
      setPersonImage(url);
      setPersonPreview(url);
    } else {
      setGarmentImage(url);
      setGarmentPreview(url);
    }
  }

  async function handleTryOn() {
    if (!personImage || !garmentImage) return;

    setStage("processing");
    setError("");
    setCommentary("");
    setCommentaryPayload(null);
    setSizeRec(null);
    setMotionUrl("");
    setIsAnimating(false);
    setSavedLookId("");
    setIsSaved(false);
    setOpenSection(null);
    setPerspectiveExpanded(false);

    const tryOnRes = await runTryOn({
      person_image: personImage,
      garment_image: garmentImage,
    });

    if (!tryOnRes.success || !tryOnRes.data) {
      setError(tryOnRes.message || "The visualization didn't come together this time.");
      setStage("upload");
      return;
    }

    const nextResult = tryOnRes.data;
    setResult(nextResult);
    setStage("result");

    const commentaryPromise = generateCommentary({
      look_image_url: nextResult.try_on_image_url,
      mode: "concise_luxury",
      user_profile_id: profileId || undefined,
      occasion: occasion || undefined,
    });

    const sizePromise = profileId
      ? recommendSize({
          user_profile_id: profileId,
          garment_category: "tops",
          brand: garmentBrand || undefined,
          silhouette_intent: garmentFit || undefined,
        })
      : Promise.resolve(null);

    let motionPromise: ReturnType<typeof generateMotion> | null = null;
    if (motionEnabled) {
      setIsAnimating(true);
      motionPromise = generateMotion({
        source_image_url: nextResult.try_on_image_url,
        motion_preset: motionPreset,
      });
    }

    const [commentaryRes, sizeRes] = await Promise.all([commentaryPromise, sizePromise]);

    if (commentaryRes.success && commentaryRes.data) {
      setCommentaryPayload(commentaryRes.data);
      setCommentary(commentaryRes.data.text || "");
    } else {
      setCommentary(commentaryRes?.message || "MIRA has the look ready, but her notes need another moment.");
    }

    if (sizeRes?.success && sizeRes.data) {
      setSizeRec(sizeRes.data);
    }

    if (motionPromise) {
      const motionRes = await motionPromise;
      if (motionRes.success && motionRes.data?.video_url) {
        setMotionUrl(motionRes.data.video_url);
      } else if (!motionRes.success) {
        setError(motionRes.message || "Motion didn't complete. Your still image is ready.");
      }
      setIsAnimating(false);
    }
  }

  async function handleSave() {
    if (!result) return;
    const res = await saveLook({
      try_on_image_url: result.try_on_image_url,
      source_garment_url: result.source_garment_url,
      stylist_commentary: commentary,
      commentary_payload: commentaryPayload,
      recommended_size: sizeRec,
      fit_notes: garmentFit,
      garment_brand: garmentBrand || null,
      garment_fit: garmentFit || null,
      user_profile_id: profileId || null,
      occasion_tags: occasionTags,
      vibe_tags: vibeTags,
      motion_preset: motionEnabled ? motionPreset : null,
      animated_clip_url: motionUrl || null,
    });

    if (res.success && res.data) {
      setIsSaved(true);
      setSavedLookId(res.data.look_id);
    } else {
      setError("We couldn't save this look just yet.");
    }
  }

  function reset() {
    setStage("upload");
    setPersonImage("");
    setGarmentImage("");
    setPersonPreview("");
    setGarmentPreview("");
    setResult(null);
    setCommentary("");
    setCommentaryPayload(null);
    setSizeRec(null);
    setError("");
    setIsSaved(false);
    setSavedLookId("");
    setMotionUrl("");
    setIsAnimating(false);
    setOpenSection(null);
    setPerspectiveExpanded(false);
  }

  const profileSummary = [
    profile?.height_cm ? `${profile.height_cm}cm` : null,
    profile?.gender || null,
    profile?.brand_size_references?.[0]
      ? `${profile.brand_size_references[0].size} in ${profile.brand_size_references[0].brand}`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const voiceScript = commentary
    ? buildVoiceScript({ commentary, commentaryPayload, occasion, garmentBrand })
    : "";

  const vibeTags: string[] = Array.isArray(commentaryPayload?.vibe_tags)
    ? commentaryPayload.vibe_tags.filter(Boolean).slice(0, 4)
    : [];

  const occasionTags: string[] = Array.isArray(commentaryPayload?.occasion_tags)
    ? commentaryPayload.occasion_tags.filter(Boolean).slice(0, 3)
    : occasion
    ? [occasion]
    : [];

  const stylingSuggestions: string[] = Array.isArray(commentaryPayload?.styling_suggestions)
    ? commentaryPayload.styling_suggestions.filter(Boolean).slice(0, 3)
    : [];

  const refinementNotes: string[] = Array.isArray(commentaryPayload?.refinement_notes)
    ? commentaryPayload.refinement_notes.filter(Boolean).slice(0, 2)
    : [];

  const completions: string[] = Array.isArray(commentaryPayload?.complete_the_look)
    ? commentaryPayload.complete_the_look.filter(Boolean).slice(0, 4)
    : [];

  const availableAccordionSections = ACCORDION_SECTIONS.filter((section) =>
    Boolean(commentaryPayload?.[section.key])
  );

  const readyToGenerate = Boolean(personImage && garmentImage);
  const motionDescription =
    MOTION_PRESETS.find((preset) => preset.key === motionPreset)?.description || "";

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-20">
        {stage === "upload" && (
          <section className="mira-container pb-28 pt-6">
            <motion.div
              className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55 }}
            >
              <div className="space-y-5">
                <div className="mira-section overflow-hidden px-6 py-7 sm:px-7">
                  <p className="mira-overline">Virtual Try-On</p>
                  <h1 className="mira-page-title mt-3">
                    See the look on you before you decide.
                  </h1>
                  <p className="mira-subtitle mt-4 max-w-xl">
                    Add a portrait and garment, choose the occasion, and let MIRA return a calmer editorial read instead of a generic output.
                  </p>
                  <div className="mt-6 flex flex-wrap gap-2">
                    {[
                      "Quick upload",
                      "Guided commentary",
                      motionEnabled ? "Motion included" : "Still image",
                    ].map((item) => (
                      <span key={item} className="mira-tag">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                {error && (
                  <div className="rounded-[1.6rem] border border-mira-rose/25 bg-mira-rose/5 px-4 py-4 text-body text-mira-rose-muted">
                    {error}
                  </div>
                )}

                <div className="grid gap-4 sm:grid-cols-2">
                  <UploadTile
                    title="Your portrait"
                    subtitle="Front-facing, clean lighting, natural posture"
                    preview={personPreview}
                    onFileSelect={(event) => handleFileSelect(event, "person")}
                    inputRef={personInputRef}
                  />
                  <UploadTile
                    title="The garment"
                    subtitle="A clean product photo with the item clearly visible"
                    preview={garmentPreview}
                    onFileSelect={(event) => handleFileSelect(event, "garment")}
                    inputRef={garmentInputRef}
                  />
                </div>
              </div>

              <div className="space-y-5">
                <div className="mira-card-elevated p-5 sm:p-6">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="mira-overline">Styling context</p>
                      <h2 className="mt-2 text-heading text-mira-charcoal">A few details for a better read</h2>
                    </div>
                    <Link href="/profile" className="text-[0.78rem] text-mira-gold transition-colors hover:text-mira-gold-muted">
                      Edit profile
                    </Link>
                  </div>

                  {profileSummary && (
                    <div className="mt-5 rounded-[1.35rem] bg-[#f4ece1] px-4 py-3 text-[0.88rem] text-mira-graphite">
                      {profileSummary}
                    </div>
                  )}

                  <div className="mt-5 grid gap-4">
                    <Field label="Occasion">
                      <select
                        value={occasion}
                        onChange={(event) => setOccasion(event.target.value)}
                        className="mira-input"
                      >
                        {OCCASION_OPTIONS.map((option) => (
                          <option key={option}>{option}</option>
                        ))}
                      </select>
                    </Field>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label="Garment brand">
                        <input
                          value={garmentBrand}
                          onChange={(event) => setGarmentBrand(event.target.value)}
                          placeholder="Zara"
                          className="mira-input"
                        />
                      </Field>

                      <Field label="Fit intention">
                        <select
                          value={garmentFit}
                          onChange={(event) => setGarmentFit(event.target.value)}
                          className="mira-input"
                        >
                          {GARMENT_FIT_OPTIONS.map((option) => (
                            <option key={option}>{option}</option>
                          ))}
                        </select>
                      </Field>
                    </div>
                  </div>
                </div>

                <div className="mira-card-elevated p-5 sm:p-6">
                  <p className="mira-overline">Reveal style</p>
                  <h2 className="mt-2 text-heading text-mira-charcoal">Choose how the result arrives</h2>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button
                      onClick={() => setMotionEnabled(false)}
                      className={`rounded-full px-4 py-2.5 text-[0.84rem] transition-all ${
                        !motionEnabled ? "bg-mira-charcoal text-white" : "bg-[#f7f1e7] text-mira-slate"
                      }`}
                    >
                      Still image
                    </button>
                    <button
                      onClick={() => setMotionEnabled(true)}
                      className={`rounded-full px-4 py-2.5 text-[0.84rem] transition-all ${
                        motionEnabled ? "bg-mira-charcoal text-white" : "bg-[#f7f1e7] text-mira-slate"
                      }`}
                    >
                      Add motion preview
                    </button>
                  </div>

                  {motionEnabled && (
                    <>
                      <div className="mt-5 grid gap-2">
                        {MOTION_PRESETS.map((preset) => (
                          <button
                            key={preset.key}
                            onClick={() => setMotionPreset(preset.key)}
                            className={`rounded-[1.3rem] border px-4 py-3 text-left transition-all ${
                              motionPreset === preset.key
                                ? "border-mira-gold/25 bg-mira-gold/10"
                                : "border-black/6 bg-white/65"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <p className="text-[0.9rem] font-medium text-mira-charcoal">{preset.label}</p>
                                <p className="mt-1 text-[0.82rem] leading-[1.55] text-mira-slate">
                                  {preset.description}
                                </p>
                              </div>
                              {motionPreset === preset.key && (
                                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-mira-gold">
                                  <Check className="h-4 w-4" />
                                </span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                      <p className="mt-4 text-[0.83rem] leading-[1.6] text-mira-slate">{motionDescription}</p>
                    </>
                  )}

                  <div className="mt-6 border-t border-black/5 pt-5">
                    <p className="text-[0.84rem] leading-[1.6] text-mira-slate">
                      {readyToGenerate
                        ? "Everything is in place. Generate the look from here."
                        : "Add both images above, then generate the look here."}
                    </p>
                    <button
                      onClick={handleTryOn}
                      disabled={!readyToGenerate}
                      className="mira-btn-primary mt-4 flex w-full items-center justify-center gap-2"
                    >
                      {motionEnabled ? "Generate Look + Motion" : "Generate the Look"}
                      <Sparkles className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </section>
        )}

        {stage === "processing" && (
          <section className="mira-container flex min-h-[calc(100vh-5rem)] items-center justify-center py-10">
            <LoadingState
              caption="Styling your look"
              message={motionEnabled ? "Styling the look and preparing motion." : "Styling the look and reading the result."}
              detail="You will see the image as soon as it is ready, then the editorial notes settle in."
              steps={[
                "Validating the images",
                "Generating the try-on",
                "Composing MIRA's perspective",
                motionEnabled ? "Preparing motion" : "Finishing the look",
              ]}
              activeStep={motionEnabled ? 2 : 2}
            />
          </section>
        )}

        {stage === "result" && result && (
          <section className="mira-container pb-16 pt-6">
            <div className="space-y-5">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="mira-overline">Your Reveal</p>
                  <h1 className="mira-page-title mt-3">The look is ready.</h1>
                  <p className="mira-subtitle mt-3 max-w-2xl">
                    Start with the image, then move through MIRA&apos;s read, fit guidance, and the finishing notes worth keeping.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {occasion && <span className="mira-tag">{occasion}</span>}
                  {garmentBrand && <span className="mira-tag">{garmentBrand}</span>}
                  {garmentFit !== "Not sure" && <span className="mira-tag">{garmentFit} fit</span>}
                </div>
              </div>

              {error && (
                <div className="rounded-[1.5rem] border border-mira-rose/25 bg-mira-rose/5 px-4 py-4 text-body text-mira-rose-muted">
                  {error}
                </div>
              )}

              <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                <div className="space-y-5">
                  <ResultMediaCard
                    stillUrl={result.try_on_image_url}
                    motionUrl={motionUrl}
                    isAnimating={isAnimating}
                    motionEnabled={motionEnabled}
                  />

                  <div className="mira-card p-5 sm:p-6">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="mira-overline">Actions</p>
                        <p className="mt-2 text-body text-mira-slate">
                          Save the look, revisit it later, or begin a new one while this styling context is still fresh.
                        </p>
                      </div>
                    </div>
                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      {!isSaved ? (
                        <button onClick={handleSave} className="mira-btn-primary w-full">
                          Save to Wardrobe
                        </button>
                      ) : savedLookId ? (
                        <Link href={`/look/${savedLookId}`} className="mira-btn-primary w-full text-center">
                          Open Saved Look
                        </Link>
                      ) : (
                        <div className="mira-btn-primary w-full opacity-70">Saved</div>
                      )}
                      <button onClick={reset} className="mira-btn-secondary w-full">
                        Try Another Look
                      </button>
                    </div>
                  </div>
                </div>

                <div className="space-y-5">
                  <div className="mira-section px-6 py-6">
                    <div className="flex items-center justify-between gap-3">
                      <p className="mira-overline">MIRA&apos;s Perspective</p>
                      {voiceScript && <VoiceMode text={voiceScript} autoPlay variant="inline" />}
                    </div>

                    {commentary ? (
                      <>
                        <p
                          className={`mt-4 font-display text-[1.55rem] leading-[1.34] tracking-[-0.025em] text-mira-charcoal sm:text-[1.95rem] ${
                            !perspectiveExpanded ? "line-clamp-5" : ""
                          }`}
                        >
                          &ldquo;{commentary}&rdquo;
                        </p>
                        {commentary.length > 280 && (
                          <button
                            onClick={() => setPerspectiveExpanded((value) => !value)}
                            className="mt-3 text-[0.82rem] text-mira-slate transition-colors hover:text-mira-charcoal"
                          >
                            {perspectiveExpanded ? "Show less" : "Read the full note"}
                          </button>
                        )}
                      </>
                    ) : (
                      <div className="mt-4 space-y-3">
                        <div className="h-6 animate-pulse rounded-full bg-[#eadfd1]" />
                        <div className="h-6 w-[86%] animate-pulse rounded-full bg-[#eadfd1]" />
                        <div className="h-6 w-[68%] animate-pulse rounded-full bg-[#eadfd1]" />
                      </div>
                    )}
                  </div>

                  {(vibeTags.length > 0 || completions.length > 0) && (
                    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-1">
                      {vibeTags.length > 0 && (
                        <div className="mira-card p-5">
                          <p className="mira-overline">Vibe</p>
                          <div className="mt-4 flex flex-wrap gap-2">
                            {vibeTags.map((tag) => (
                              <span key={tag} className="mira-tag mira-tag-gold">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {completions.length > 0 && (
                        <div className="mira-card p-5">
                          <p className="mira-overline">Complete the look</p>
                          <div className="mt-4 space-y-2.5">
                            {completions.map((item) => (
                              <div
                                key={item}
                                className="rounded-[1.2rem] border border-black/5 bg-[#f7f1e8] px-4 py-3 text-[0.92rem] leading-[1.55] text-mira-graphite"
                              >
                                {item}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {(stylingSuggestions.length > 0 || refinementNotes.length > 0 || sizeRec) && (
                    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-1">
                      {(stylingSuggestions.length > 0 || refinementNotes.length > 0) && (
                        <div className="mira-card p-5">
                          <p className="mira-overline">Styling notes</p>
                          <div className="mt-4 space-y-2.5">
                            {stylingSuggestions.map((item) => (
                              <div
                                key={item}
                                className="rounded-[1.2rem] border border-black/5 bg-white/72 px-4 py-3 text-[0.9rem] leading-[1.55] text-mira-graphite"
                              >
                                {item}
                              </div>
                            ))}
                            {refinementNotes.map((item) => (
                              <div
                                key={item}
                                className="rounded-[1.2rem] border border-mira-gold/15 bg-[#f7f1e8] px-4 py-3 text-[0.88rem] leading-[1.55] text-[#5b5147]"
                              >
                                {item}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {sizeRec && (
                        <div className="mira-card p-5">
                          <p className="mira-overline">Suggested fit</p>
                          <div className="mt-4 flex items-start gap-4">
                            <span className="font-display text-[2.2rem] leading-none tracking-[-0.05em] text-mira-charcoal">
                              {sizeRec.recommended_size}
                            </span>
                            <div>
                              <p className="text-[0.78rem] uppercase tracking-[0.16em] text-mira-slate">
                                {Math.round((sizeRec.confidence || 0) * 100)}% confidence
                              </p>
                              <p className="mt-2 text-[0.92rem] leading-[1.6] text-mira-graphite">
                                {sizeRec.reason_summary}
                              </p>
                              {sizeRec.alternate_size && (
                                <p className="mt-2 text-[0.84rem] text-mira-gold">
                                  Also consider {sizeRec.alternate_size}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {availableAccordionSections.length > 0 && (
                    <div className="mira-card-elevated overflow-hidden">
                      {availableAccordionSections.map((section, index) => (
                        <div key={section.key} className={index > 0 ? "border-t border-black/5" : ""}>
                          <button
                            onClick={() => setOpenSection(openSection === section.key ? null : section.key)}
                            className="flex w-full items-center justify-between px-5 py-4 text-left"
                          >
                            <span className="text-[0.78rem] uppercase tracking-[0.17em] text-mira-slate">
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
                    lookImageUrl={result.try_on_image_url}
                    commentaryPayload={commentaryPayload}
                    occasion={occasion}
                    garmentBrand={garmentBrand}
                    garmentFit={garmentFit}
                  />
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      {stage === "upload" && (
        <div className="fixed inset-x-0 bottom-0 z-40 hidden border-t border-black/5 bg-[#fbf8f2]/92 px-5 pb-[calc(env(safe-area-inset-bottom,0px)+0.9rem)] pt-3 backdrop-blur-2xl md:block">
          <div className="mx-auto flex max-w-6xl items-center gap-3">
            <div className="hidden flex-1 rounded-full bg-[#f4ece1] px-4 py-3 text-[0.84rem] text-mira-slate md:block">
              {readyToGenerate
                ? "Everything is ready. MIRA can generate the look now."
                : "Add both images to continue."}
            </div>
            <button
              onClick={handleTryOn}
              disabled={!readyToGenerate}
              className="mira-btn-primary w-full md:w-auto"
            >
              {motionEnabled ? "Generate Look + Motion" : "Generate the Look"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-[0.73rem] uppercase tracking-[0.18em] text-mira-slate">
        {label}
      </span>
      {children}
    </label>
  );
}

function UploadTile({
  title,
  subtitle,
  preview,
  onFileSelect,
  inputRef,
}: {
  title: string;
  subtitle: string;
  preview: string;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  inputRef: RefObject<HTMLInputElement>;
}) {
  return (
    <div className="mira-card-elevated p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[1rem] font-medium text-mira-charcoal">{title}</p>
          <p className="mt-1 text-[0.84rem] leading-[1.6] text-mira-slate">{subtitle}</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f4ece1]">
          <ImagePlus className="h-4.5 w-4.5 text-mira-charcoal" />
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-[1.5rem] border border-black/5 bg-[#f7f1e8]">
        {preview ? (
          <img src={preview} alt={title} className="aspect-[4/5] w-full object-cover object-top" />
        ) : (
          <div className="flex aspect-[4/5] flex-col items-center justify-center px-6 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full border border-black/5 bg-white/65">
              <Sparkles className="h-5 w-5 text-mira-gold" />
            </div>
            <p className="mt-4 text-[0.95rem] text-mira-graphite">No image added yet</p>
            <p className="mt-2 max-w-[15rem] text-[0.82rem] leading-[1.6] text-mira-slate">
              Choose a photo from your camera roll and MIRA will take it from there.
            </p>
          </div>
        )}
      </div>

      <div className="mt-4">
        <button
          onClick={() => inputRef.current?.click()}
          className="mira-btn-secondary w-full"
        >
          Choose image
        </button>
        <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={onFileSelect} />
      </div>
    </div>
  );
}

function ResultMediaCard({
  stillUrl,
  motionUrl,
  isAnimating,
  motionEnabled,
}: {
  stillUrl: string;
  motionUrl: string;
  isAnimating: boolean;
  motionEnabled: boolean;
}) {
  const [mode, setMode] = useState<"still" | "motion">("still");

  useEffect(() => {
    if (motionUrl) {
      setMode("motion");
    }
  }, [motionUrl]);

  const hasMotion = Boolean(motionUrl);

  return (
    <div className="mira-card-elevated overflow-hidden p-4 sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex rounded-full bg-[#f4ece1] p-1">
          <button
            onClick={() => setMode("still")}
            className={`rounded-full px-4 py-2 text-[0.82rem] transition-all ${
              mode === "still" ? "bg-white text-mira-charcoal shadow-soft" : "text-mira-slate"
            }`}
          >
            Still
          </button>
          <button
            onClick={() => setMode("motion")}
            disabled={!hasMotion && !isAnimating}
            className={`rounded-full px-4 py-2 text-[0.82rem] transition-all disabled:opacity-40 ${
              mode === "motion" ? "bg-white text-mira-charcoal shadow-soft" : "text-mira-slate"
            }`}
          >
            Motion
          </button>
        </div>

        {motionEnabled && (
          <span className="inline-flex items-center gap-2 rounded-full bg-[#f7f1e8] px-3 py-2 text-[0.74rem] uppercase tracking-[0.16em] text-mira-slate">
            <Film className="h-3.5 w-3.5" />
            {hasMotion ? "Motion ready" : isAnimating ? "Generating motion" : "Still image"}
          </span>
        )}
      </div>

      <div className="relative overflow-hidden rounded-[1.8rem] bg-[#ebdfcf]">
        <AnimatePresence mode="wait">
          {mode === "motion" && motionUrl ? (
            <motion.video
              key="motion"
              src={motionUrl}
              autoPlay
              loop
              muted
              playsInline
              className="aspect-[4/5] w-full object-cover object-top"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          ) : (
            <motion.img
              key="still"
              src={stillUrl}
              alt="Your styled look"
              className="aspect-[4/5] w-full object-cover object-top"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          )}
        </AnimatePresence>

        {mode === "motion" && isAnimating && !motionUrl && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#f5ece0]/82 backdrop-blur-sm">
            <div className="max-w-xs text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-white/75">
                <Wand2 className="h-5 w-5 animate-pulse text-mira-gold" />
              </div>
              <p className="mt-4 text-[0.95rem] text-mira-charcoal">MIRA is bringing the look to life.</p>
              <p className="mt-2 text-[0.82rem] leading-[1.6] text-mira-slate">
                The still image is ready first. Motion settles in just after.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
