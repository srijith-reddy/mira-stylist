"use client";

import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { Bookmark, Heart, Layers3, SlidersHorizontal, X } from "lucide-react";
import Navigation from "@/components/Navigation";
import LoadingState from "@/components/LoadingState";
import { deleteLook, listLooks, toggleFavorite } from "@/lib/api";

interface Look {
  look_id: string;
  try_on_image_url: string;
  source_garment_url: string;
  stylist_commentary: string;
  is_favorite: boolean;
  vibe_tags: string[];
  occasion_tags: string[];
  commentary_payload?: {
    vibe_tags?: string[];
    occasion_tags?: string[];
  } | null;
  collection_ids?: string[];
  created_at: string;
  animated_clip_url?: string;
}

function normalizeTag(tag: string) {
  return tag.trim().toLowerCase();
}

function formatTag(tag: string) {
  return tag
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function uniqueTags(tags: string[]) {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const tag of tags) {
    const normalized = normalizeTag(tag);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

function getEffectiveOccasionTags(look: Look) {
  const direct = Array.isArray(look.occasion_tags) ? look.occasion_tags : [];
  const payload = Array.isArray(look.commentary_payload?.occasion_tags)
    ? look.commentary_payload?.occasion_tags || []
    : [];
  return uniqueTags([...direct, ...payload]);
}

function getEffectiveVibeTags(look: Look) {
  const direct = Array.isArray(look.vibe_tags) ? look.vibe_tags : [];
  const payload = Array.isArray(look.commentary_payload?.vibe_tags)
    ? look.commentary_payload?.vibe_tags || []
    : [];
  return uniqueTags([...direct, ...payload]);
}

export default function WardrobePage() {
  const [looks, setLooks] = useState<Look[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [selectedOccasion, setSelectedOccasion] = useState<string | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    const looksRes = await listLooks();
    if (looksRes.success) setLooks(looksRes.data || []);
    setIsLoading(false);
  }

  async function handleToggleFavorite(lookId: string) {
    const res = await toggleFavorite(lookId);
    if (res.success) {
      setLooks((current) =>
        current.map((look) =>
          look.look_id === lookId ? { ...look, is_favorite: !look.is_favorite } : look
        )
      );
    }
  }

  async function handleDelete(lookId: string) {
    if (typeof window !== "undefined") {
      const confirmed = window.confirm("Remove this look from your wardrobe?");
      if (!confirmed) return;
    }

    const res = await deleteLook(lookId);
    if (res.success) {
      setLooks((current) => current.filter((look) => look.look_id !== lookId));
    }
  }

  const filterChips = ["all", "favorites"];
  const occasionFilterCounts = new Map<string, number>();
  for (const look of looks) {
    for (const tag of getEffectiveOccasionTags(look)) {
      occasionFilterCounts.set(tag, (occasionFilterCounts.get(tag) || 0) + 1);
    }
  }
  const occasionFilters = Array.from(occasionFilterCounts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([tag]) => tag);

  const filteredByPrimary =
    activeFilter === "favorites" ? looks.filter((look) => look.is_favorite) : looks;

  const filteredLooks = selectedOccasion
    ? filteredByPrimary.filter((look) =>
        getEffectiveOccasionTags(look).includes(normalizeTag(selectedOccasion))
      )
    : filteredByPrimary;

  const favoriteCount = looks.filter((look) => look.is_favorite).length;
  const motionCount = looks.filter((look) => Boolean(look.animated_clip_url)).length;

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-20 pb-14">
        <div className="mira-container">
          <motion.div
            className="mira-section mb-8 overflow-hidden px-6 py-7 sm:px-8"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="mira-overline">Your Collection</p>
                <h1 className="mira-page-title mt-3">Wardrobe</h1>
                <p className="mira-subtitle mt-4 max-w-2xl">
                  Every look you chose to keep, with enough context to return quickly and pick up where you left off.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <StatCard icon={Layers3} label="All looks" value={String(looks.length)} />
                <StatCard icon={Heart} label="Favorites" value={String(favoriteCount)} />
                <StatCard icon={Bookmark} label="Motion" value={String(motionCount)} />
              </div>
            </div>
          </motion.div>

          <div className="mb-6 flex items-center gap-2 overflow-x-auto pb-2">
            {filterChips.map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`whitespace-nowrap rounded-full px-4 py-2.5 text-[0.82rem] transition-all ${
                  activeFilter === filter
                    ? "bg-mira-charcoal text-white"
                    : "bg-white/70 text-mira-slate"
                }`}
              >
                {filter === "all" ? "All Looks" : "Favorites"}
              </button>
            ))}

            {occasionFilters.length > 0 && (
              <button
                onClick={() => setIsFilterOpen(true)}
                className={`inline-flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2.5 text-[0.82rem] transition-all ${
                  selectedOccasion
                    ? "bg-mira-gold/15 text-mira-charcoal"
                    : "bg-white/70 text-mira-slate"
                }`}
              >
                <SlidersHorizontal className="h-4 w-4" />
                {selectedOccasion ? formatTag(selectedOccasion) : "Filter"}
              </button>
            )}
          </div>

          {selectedOccasion && (
            <div className="mb-6 flex items-center gap-2">
              <span className="rounded-full bg-[#f4ece1] px-4 py-2 text-[0.78rem] uppercase tracking-[0.12em] text-mira-charcoal">
                {formatTag(selectedOccasion)}
              </span>
              <button
                onClick={() => setSelectedOccasion(null)}
                className="text-[0.78rem] uppercase tracking-[0.14em] text-mira-slate transition-colors hover:text-mira-charcoal"
              >
                Clear
              </button>
            </div>
          )}

          {isLoading ? (
            <div className="flex min-h-[40vh] items-center justify-center">
              <LoadingState
                caption="Opening your wardrobe"
                message="Bringing your saved looks back into view."
              />
            </div>
          ) : filteredLooks.length === 0 ? (
            <EmptyWardrobe />
          ) : (
            <motion.div
              className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <AnimatePresence>
                {filteredLooks.map((look, index) => (
                  <motion.div
                    key={look.look_id}
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96 }}
                    transition={{ delay: index * 0.03, duration: 0.35 }}
                  >
                    <LookCard
                      look={look}
                      onToggleFavorite={() => handleToggleFavorite(look.look_id)}
                      onDelete={() => handleDelete(look.look_id)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </main>

      <AnimatePresence>
        {isFilterOpen && (
          <>
            <motion.button
              type="button"
              aria-label="Close filters"
              className="fixed inset-0 z-40 bg-[#1f1b17]/20 backdrop-blur-[2px]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsFilterOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 18 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="fixed inset-x-0 bottom-0 z-50 mx-auto w-full max-w-2xl rounded-t-[2rem] border border-black/5 bg-[#fbf8f2] px-5 pb-[calc(env(safe-area-inset-bottom,0px)+1.2rem)] pt-5 shadow-[0_-24px_60px_rgba(36,28,21,0.12)]"
            >
              <div className="mx-auto h-1.5 w-14 rounded-full bg-[#dfd3c4]" />
              <div className="mt-5 flex items-start justify-between gap-4">
                <div>
                  <p className="mira-overline">Filter</p>
                  <h2 className="mt-2 text-heading text-mira-charcoal">Refine by occasion</h2>
                  <p className="mt-2 text-body text-mira-slate">
                    Keep the wardrobe calm by default, then narrow it only when you need to.
                  </p>
                </div>
                <button
                  onClick={() => setIsFilterOpen(false)}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-white/80 text-mira-slate transition-colors hover:text-mira-charcoal"
                  aria-label="Close filters"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-6 flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedOccasion(null)}
                  className={`rounded-full px-4 py-2.5 text-[0.82rem] transition-all ${
                    selectedOccasion === null
                      ? "bg-mira-charcoal text-white"
                      : "bg-white/72 text-mira-slate"
                  }`}
                >
                  Any occasion
                </button>
                {occasionFilters.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setSelectedOccasion(tag)}
                    className={`rounded-full px-4 py-2.5 text-[0.82rem] transition-all ${
                      selectedOccasion === tag
                        ? "bg-mira-charcoal text-white"
                        : "bg-white/72 text-mira-slate"
                    }`}
                  >
                    {formatTag(tag)}
                  </button>
                ))}
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <button
                  onClick={() => {
                    setSelectedOccasion(null);
                    setIsFilterOpen(false);
                  }}
                  className="mira-btn-secondary w-full"
                >
                  Clear Filter
                </button>
                <button
                  onClick={() => setIsFilterOpen(false)}
                  className="mira-btn-primary w-full"
                >
                  View Looks
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[1.4rem] bg-white/68 px-4 py-4">
      <Icon className="h-4 w-4 text-mira-gold" />
      <p className="mt-4 text-[1.45rem] font-medium tracking-[-0.04em] text-mira-charcoal">{value}</p>
      <p className="mt-1 text-[0.78rem] uppercase tracking-[0.16em] text-mira-slate">{label}</p>
    </div>
  );
}

function LookCard({
  look,
  onToggleFavorite,
  onDelete,
}: {
  look: Look;
  onToggleFavorite: () => void;
  onDelete: () => void;
}) {
  const occasionTags = getEffectiveOccasionTags(look);
  const vibeTags = getEffectiveVibeTags(look);

  return (
    <div className="mira-card-elevated overflow-hidden">
      <Link href={`/look/${look.look_id}`} className="block">
        <div className="relative aspect-[4/5] overflow-hidden bg-[#efe6da]">
          <img
            src={look.try_on_image_url}
            alt="Styled look"
            className="h-full w-full object-cover object-top transition-transform duration-500 hover:scale-[1.02]"
          />

          {(occasionTags.length > 0 || vibeTags.length > 0) && (
            <div className="absolute inset-x-3 bottom-3 flex flex-wrap gap-1.5">
              {[...occasionTags.slice(0, 1), ...vibeTags.slice(0, 1)].map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-white/80 px-2 py-1 text-[0.64rem] uppercase tracking-[0.12em] text-mira-charcoal"
                >
                  {formatTag(tag)}
                </span>
              ))}
            </div>
          )}

          {look.animated_clip_url && (
            <div className="absolute left-3 top-3 rounded-full bg-mira-charcoal px-2.5 py-1 text-[0.62rem] uppercase tracking-[0.14em] text-white">
              Motion
            </div>
          )}
        </div>
      </Link>

      <div className="p-3">
        <p className="line-clamp-2 text-[0.86rem] leading-[1.55] text-mira-graphite">
          {look.stylist_commentary || "Saved look"}
        </p>
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={onToggleFavorite}
              className="text-body transition-colors duration-200"
              aria-label={look.is_favorite ? "Remove from favorites" : "Add to favorites"}
            >
              {look.is_favorite ? (
                <span className="text-mira-rose">&#9829;</span>
              ) : (
                <span className="text-mira-slate hover:text-mira-rose">&#9825;</span>
              )}
            </button>
            <button
              onClick={onDelete}
              className="text-[0.74rem] uppercase tracking-[0.14em] text-mira-slate transition-colors hover:text-mira-rose"
              aria-label="Delete look"
            >
              Remove
            </button>
          </div>
          <span className="text-[0.7rem] uppercase tracking-[0.12em] text-mira-slate/70">
            {new Date(look.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyWardrobe() {
  return (
    <motion.div
      className="mira-section px-6 py-10 text-center"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[#f4ece1]">
        <Bookmark className="h-8 w-8 text-mira-slate" />
      </div>
      <h3 className="mt-6 text-heading text-mira-charcoal">Your wardrobe is still empty</h3>
      <p className="mx-auto mt-3 max-w-sm text-body text-mira-slate">
        Save a look and it will appear here with enough context to revisit gracefully later.
      </p>
      <Link href="/try-on" className="mira-btn-primary mt-8 inline-flex">
        Visualize Your First Look
      </Link>
    </motion.div>
  );
}
