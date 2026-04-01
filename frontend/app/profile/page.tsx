"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navigation from "@/components/Navigation";
import LoadingState from "@/components/LoadingState";
import { getProfile, updateProfile } from "@/lib/api";

type BrandSizeReference = {
  category: string;
  brand: string;
  size: string;
};

interface Profile {
  id: string;
  name: string;
  pronouns?: string | null;
  gender?: string | null;
  height_cm?: number | null;
  preferred_aesthetic: string;
  preferred_silhouettes: string[];
  style_goals: string[];
  favorite_colors: string[];
  disliked_colors: string[];
  occasions: string[];
  comfort_vs_statement: number;
  modesty_preference: string;
  luxury_preference: string;
  narrative_summary: string;
  measurements: Record<string, number>;
  approximate_size_history: Record<string, string>;
  brand_size_references: BrandSizeReference[];
  typical_size_ranges: string[];
  stylist_notes: string[];
  confidence_level_sizing: number;
  confidence_level_avatar: number;
}

type SnapshotDraft = {
  name: string;
  gender: string;
  height_cm: string;
};

function normalizeNarrativeSummary(profile: Profile) {
  const narrative = profile.narrative_summary?.trim();
  if (!narrative) return "";

  const gender = profile.gender?.trim().toLowerCase() || "";
  const readsMale = gender.includes("male") && !gender.includes("female");
  const readsFemale = gender.includes("female");
  const hasFemininePronouns = /\b(she|her|hers)\b/i.test(narrative);
  const hasMasculinePronouns = /\b(he|him|his)\b/i.test(narrative);

  const mismatchedPronouns =
    (readsMale && hasFemininePronouns) || (readsFemale && hasMasculinePronouns);

  if (!mismatchedPronouns) {
    return narrative;
  }

  const displayName = profile.name?.trim() || "They";

  return narrative
    .replace(/\b[Ss]he\b/g, displayName)
    .replace(/\b[Hh]e\b/g, displayName)
    .replace(/\b[Hh]im\b/g, "them")
    .replace(/\b[Hh]ers\b/g, "theirs")
    .replace(/\b[Hh]is\b/g, "their")
    .replace(/\b[Hh]er\b/g, "their");
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editSection, setEditSection] = useState<string | null>(null);
  const [snapshotDraft, setSnapshotDraft] = useState<SnapshotDraft>({
    name: "",
    gender: "",
    height_cm: "",
  });
  const [brandDraft, setBrandDraft] = useState<BrandSizeReference[]>([]);
  const [saveError, setSaveError] = useState("");

  const profileId = typeof window !== "undefined" ? localStorage.getItem("mira_profile_id") : null;

  useEffect(() => {
    if (profileId) {
      loadProfile();
    } else {
      setIsLoading(false);
    }
  }, [profileId]);

  useEffect(() => {
    if (!profileId || !profile || profile.narrative_summary) {
      return;
    }

    const activeProfileId = profileId;
    let cancelled = false;

    async function refreshPendingNarrative() {
      for (let attempt = 0; attempt < 10; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        if (cancelled) {
          return;
        }

        const res = await getProfile(activeProfileId);
        if (!res.success || !res.data?.narrative_summary?.trim()) {
          continue;
        }

        const updated = normalizeProfile(res.data);
        if (!cancelled) {
          setProfile(updated);
          syncDrafts(updated);
        }
        return;
      }
    }

    refreshPendingNarrative();

    return () => {
      cancelled = true;
    };
  }, [profileId, profile?.id, profile?.narrative_summary]);

  async function loadProfile() {
    if (!profileId) return;
    const res = await getProfile(profileId);
    if (res.success && res.data) {
      const loadedProfile = normalizeProfile(res.data);
      setProfile(loadedProfile);
      syncDrafts(loadedProfile);
    }
    setIsLoading(false);
  }

  function normalizeProfile(data: any): Profile {
    return {
      ...data,
      measurements: data.measurements || {},
      approximate_size_history: data.approximate_size_history || {},
      brand_size_references: data.brand_size_references || [],
      typical_size_ranges: data.typical_size_ranges || [],
      style_goals: data.style_goals || [],
      preferred_silhouettes: data.preferred_silhouettes || [],
      favorite_colors: data.favorite_colors || [],
      disliked_colors: data.disliked_colors || [],
      occasions: data.occasions || [],
      stylist_notes: data.stylist_notes || [],
    };
  }

  function syncDrafts(nextProfile: Profile) {
    setSnapshotDraft({
      name: nextProfile.name || "",
      gender: nextProfile.gender || "",
      height_cm: nextProfile.height_cm ? String(nextProfile.height_cm) : "",
    });
    setBrandDraft(
      nextProfile.brand_size_references.length > 0
        ? nextProfile.brand_size_references
        : [{ category: "Tops", brand: "", size: "" }]
    );
  }

  function startEditing(section: "snapshot" | "brandSizing") {
    if (!profile) return;
    syncDrafts(profile);
    setSaveError("");
    setEditSection(section);
  }

  function cancelEditing() {
    if (profile) {
      syncDrafts(profile);
    }
    setSaveError("");
    setEditSection(null);
  }

  async function saveSnapshot() {
    if (!profileId) return;
    const payload = {
      name: snapshotDraft.name.trim() || "Your Profile",
      gender: snapshotDraft.gender.trim() || null,
      height_cm: snapshotDraft.height_cm.trim() ? Number(snapshotDraft.height_cm) : null,
    };

    const res = await updateProfile(profileId, payload);
    if (res.success && res.data) {
      const updated = normalizeProfile(res.data);
      setProfile(updated);
      syncDrafts(updated);
      setEditSection(null);
      setSaveError("");
      return;
    }

    setSaveError(res.message || "We couldn't save your profile details.");
  }

  async function saveBrandSizing() {
    if (!profileId) return;
    const cleaned = brandDraft
      .map((reference) => ({
        category: reference.category.trim() || "Tops",
        brand: reference.brand.trim(),
        size: reference.size.trim(),
      }))
      .filter((reference) => reference.brand && reference.size);

    const approximateSizeHistory = Object.fromEntries(cleaned.map((reference) => [reference.brand, reference.size]));

    const res = await updateProfile(profileId, {
      brand_size_references: cleaned,
      approximate_size_history: approximateSizeHistory,
    });

    if (res.success && res.data) {
      const updated = normalizeProfile(res.data);
      setProfile(updated);
      syncDrafts(updated);
      setEditSection(null);
      setSaveError("");
      return;
    }

    setSaveError(res.message || "We couldn't save your brand sizing references.");
  }

  function updateBrandDraft(index: number, key: keyof BrandSizeReference, value: string) {
    setBrandDraft((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item))
    );
  }

  function addBrandReference() {
    setBrandDraft((current) => [...current, { category: "Tops", brand: "", size: "" }]);
  }

  function removeBrandReference(index: number) {
    setBrandDraft((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  if (isLoading) {
    return (
      <>
        <Navigation />
        <main className="flex min-h-screen items-center justify-center px-5 pt-20">
          <LoadingState
            caption="Opening your profile"
            message="Gathering the details MIRA styles against."
          />
        </main>
      </>
    );
  }

  if (!profile) {
    return (
      <>
        <Navigation />
        <main className="flex min-h-screen items-center justify-center px-5 pt-20">
          <motion.div
            className="mira-section max-w-md px-6 py-8 text-center"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p className="mira-overline">Your profile</p>
            <h2 className="mira-page-title mt-3">Let&apos;s get to know you</h2>
            <p className="mt-4 text-body text-mira-slate">
              Complete your style consultation so MIRA can offer truly personal guidance.
            </p>
            <button onClick={() => router.push("/onboarding")} className="mira-btn-primary mt-8">
              Begin Your Style Journey
            </button>
          </motion.div>
        </main>
      </>
    );
  }

  const profileSummary = [
    profile.height_cm ? `${profile.height_cm}cm` : null,
    profile.gender || null,
    profile.brand_size_references[0]
      ? `${profile.brand_size_references[0].size} in ${profile.brand_size_references[0].brand}`
      : null,
  ]
    .filter(Boolean)
    .join(" · ");
  const displayNarrative = normalizeNarrativeSummary(profile);

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-20 pb-14">
        <div className="mira-container max-w-5xl">
          <motion.div
            className="mira-section mb-8 overflow-hidden px-6 py-7 sm:px-8"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="text-left">
                <p className="mira-overline">Your Style Identity</p>
                <h1 className="mira-page-title mt-3">{profile.name || "Your Profile"}</h1>
                {profileSummary && (
                  <div className="mt-5 inline-flex items-center rounded-full bg-[#f4ece1] px-5 py-2 text-body text-mira-slate">
                    {profileSummary}
                  </div>
                )}
                {displayNarrative && (
                  <p className="mt-5 max-w-2xl text-body-lg italic text-mira-graphite">
                    &ldquo;{displayNarrative}&rdquo;
                  </p>
                )}
                {!displayNarrative && (
                  <p className="mt-5 max-w-2xl text-body text-mira-slate">
                    MIRA is still refining your written profile. It should appear here shortly.
                  </p>
                )}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Link href="/try-on" className="mira-btn-primary w-full text-center">
                  Visualize a Look
                </Link>
                <Link href="/wardrobe" className="mira-btn-secondary w-full text-center">
                  Open Wardrobe
                </Link>
              </div>
            </div>
          </motion.div>

          {saveError && (
            <div className="mb-6 rounded-[1.5rem] border border-mira-rose/30 bg-mira-rose/5 p-4">
              <p className="text-body text-mira-rose-muted">{saveError}</p>
            </div>
          )}

          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-6">
              <ProfileSection
                title="Profile Snapshot"
                subtitle="MIRA carries this context into every future look."
                isEditing={editSection === "snapshot"}
                onEdit={() => startEditing("snapshot")}
                onSave={saveSnapshot}
                onCancel={cancelEditing}
              >
                {editSection === "snapshot" ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    <ProfileInput
                      label="Name"
                      value={snapshotDraft.name}
                      onChange={(value) => setSnapshotDraft((current) => ({ ...current, name: value }))}
                      placeholder="Your name"
                    />
                    <ProfileInput
                      label="Height (cm)"
                      type="number"
                      value={snapshotDraft.height_cm}
                      onChange={(value) => setSnapshotDraft((current) => ({ ...current, height_cm: value }))}
                      placeholder="175"
                    />
                    <ProfileInput
                      label="Gender"
                      value={snapshotDraft.gender}
                      onChange={(value) => setSnapshotDraft((current) => ({ ...current, gender: value }))}
                      placeholder="Prefer not to say"
                    />
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    <ProfileField label="Height" value={profile.height_cm ? `${profile.height_cm} cm` : "Not set"} />
                    <ProfileField label="Gender" value={profile.gender || "Prefer not to say"} />
                    <ProfileField label="Profile Name" value={profile.name || "Your Profile"} />
                  </div>
                )}
              </ProfileSection>

              <ProfileSection
                title="Brand Sizing References"
                subtitle="A few familiar brands make MIRA's fit direction more reliable."
                isEditing={editSection === "brandSizing"}
                onEdit={() => startEditing("brandSizing")}
                onSave={saveBrandSizing}
                onCancel={cancelEditing}
              >
                {editSection === "brandSizing" ? (
                  <div className="space-y-3">
                    {brandDraft.map((reference, index) => (
                      <div key={index} className="grid gap-3 md:grid-cols-[1fr_1.3fr_1fr_auto] md:items-end">
                        <ProfileSelect
                          label="Category"
                          value={reference.category}
                          options={["Tops", "Bottoms", "Dresses", "Outerwear"]}
                          onChange={(value) => updateBrandDraft(index, "category", value)}
                        />
                        <ProfileInput
                          label="Brand"
                          value={reference.brand}
                          onChange={(value) => updateBrandDraft(index, "brand", value)}
                          placeholder="Zara"
                        />
                        <ProfileInput
                          label="Size"
                          value={reference.size}
                          onChange={(value) => updateBrandDraft(index, "size", value)}
                          placeholder="M"
                        />
                        <button
                          onClick={() => removeBrandReference(index)}
                          className="pb-3 text-caption text-mira-slate transition-colors hover:text-mira-charcoal"
                          aria-label="Remove brand reference"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                    <button onClick={addBrandReference} className="text-body text-mira-gold">
                      + Add brand
                    </button>
                  </div>
                ) : profile.brand_size_references.length > 0 ? (
                  <div className="space-y-3">
                    {profile.brand_size_references.map((reference, index) => (
                      <div
                        key={`${reference.brand}-${reference.category}-${index}`}
                        className="grid gap-3 rounded-[1.4rem] bg-[#f7f1e8] px-4 py-4 md:grid-cols-3"
                      >
                        <ProfileField label="Category" value={reference.category} />
                        <ProfileField label="Brand" value={reference.brand} />
                        <ProfileField label="Size" value={reference.size} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-body text-mira-slate">
                    No brand references saved yet. Add a few familiar sizes to improve recommendations.
                  </p>
                )}
              </ProfileSection>

              <ProfileSection title="Style Identity" hideEditButton>
                <ProfileField label="Aesthetic" value={profile.preferred_aesthetic || "Not set"} />
                <ProfileField
                  label="Preferred Silhouettes"
                  value={profile.preferred_silhouettes.join(", ") || "Not set"}
                />
                <ProfileField label="Style Goals" value={profile.style_goals.join(", ") || "Not set"} />
                <ProfileField
                  label="Comfort vs Statement"
                  value={
                    profile.comfort_vs_statement <= 0.3
                      ? "Leans comfort"
                      : profile.comfort_vs_statement >= 0.7
                      ? "Leans statement"
                      : "Balanced"
                  }
                />
              </ProfileSection>
            </div>

            <div className="space-y-6">
              <div className="mira-card-elevated p-6">
                <p className="mira-overline">Why this matters</p>
                <div className="mt-4 space-y-3">
                  {[
                    "MIRA keeps your preferred tone, silhouette, and occasion context in mind.",
                    "Brand references improve fit direction during try-on.",
                    "Saved context makes each visit feel faster and more personal.",
                  ].map((item) => (
                    <div
                      key={item}
                      className="rounded-[1.2rem] bg-[#f7f1e8] px-4 py-3 text-[0.9rem] leading-[1.6] text-mira-graphite"
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <ProfileSection title="Colour Palette" hideEditButton>
                <ProfileField label="Colours You Love" value={profile.favorite_colors.join(", ") || "Not set"} />
                <ProfileField
                  label="Colours You Avoid"
                  value={profile.disliked_colors.join(", ") || "None specified"}
                />
              </ProfileSection>

              <ProfileSection title="Fit & Sizing" hideEditButton>
                <ProfileField
                  label="Typical Sizes"
                  value={profile.typical_size_ranges.join(", ") || "Not recorded"}
                />
                <ProfileField
                  label="Sizing Confidence"
                  value={`${Math.round(profile.confidence_level_sizing * 100)}%`}
                />
                <ProfileField
                  label="Modesty Preference"
                  value={profile.modesty_preference || "No specific preference"}
                />
              </ProfileSection>

              <ProfileSection title="Occasions" hideEditButton>
                <div className="flex flex-wrap gap-2">
                  {profile.occasions.length > 0 ? (
                    profile.occasions.map((occasion) => (
                      <span key={occasion} className="mira-tag mira-tag-gold">
                        {occasion}
                      </span>
                    ))
                  ) : (
                    <span className="text-body text-mira-slate">No occasions specified</span>
                  )}
                </div>
              </ProfileSection>

              <ProfileSection title="Measurements" hideEditButton>
                {Object.keys(profile.measurements).length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(profile.measurements).map(([key, value]) => (
                      <ProfileField
                        key={key}
                        label={key.charAt(0).toUpperCase() + key.slice(1)}
                        value={`${value} cm`}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-body text-mira-slate">
                    No measurements saved yet. Adding measurements improves size recommendations.
                  </p>
                )}
              </ProfileSection>

              <ProfileSection title="Stylist Notes" hideEditButton>
                {profile.stylist_notes.length > 0 ? (
                  <ul className="space-y-2">
                    {profile.stylist_notes.map((note, index) => (
                      <li key={index} className="border-l-2 border-mira-gold/30 pl-4 text-body text-mira-graphite">
                        {note}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-body text-mira-slate">
                    Notes will appear here as MIRA learns more about your preferences.
                  </p>
                )}
              </ProfileSection>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}

function ProfileSection({
  title,
  subtitle,
  children,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  hideEditButton,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  isEditing?: boolean;
  onEdit?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  hideEditButton?: boolean;
}) {
  return (
    <motion.div className="mira-card-elevated p-6" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="mira-overline">{title}</h3>
          {subtitle && <p className="mt-2 max-w-2xl text-caption text-mira-slate">{subtitle}</p>}
        </div>
        {!hideEditButton && (
          <div>
            {isEditing ? (
              <div className="flex gap-3">
                <button onClick={onSave} className="text-caption font-medium text-mira-gold">
                  Save
                </button>
                <button onClick={onCancel} className="text-caption text-mira-slate">
                  Cancel
                </button>
              </div>
            ) : (
              <button onClick={onEdit} className="text-caption text-mira-slate transition-colors hover:text-mira-gold">
                Edit
              </button>
            )}
          </div>
        )}
      </div>
      <div className="space-y-3">{children}</div>
    </motion.div>
  );
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-caption text-mira-slate">{label}</dt>
      <dd className="mt-0.5 text-body text-mira-charcoal">{value}</dd>
    </div>
  );
}

function ProfileInput({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="text-caption text-mira-slate">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mira-input mt-2"
      />
    </label>
  );
}

function ProfileSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-caption text-mira-slate">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mira-input mt-2">
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
