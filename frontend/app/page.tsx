"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Bookmark, Sparkles, UserRound, Wand2 } from "lucide-react";
import Navigation from "@/components/Navigation";
import MiraLogo from "@/components/MiraLogo";

const ENTRY_CARDS = [
  {
    title: "Visualize a look",
    description: "Upload your portrait and a garment to see the silhouette, drape, and overall read.",
    href: "/try-on",
    icon: Sparkles,
  },
  {
    title: "Refine your profile",
    description: "Save a few signals MIRA can use to make every future recommendation feel more personal.",
    href: "/profile",
    icon: UserRound,
  },
  {
    title: "Return to your wardrobe",
    description: "Revisit past looks, favorites, and saved styling notes without starting from scratch.",
    href: "/wardrobe",
    icon: Bookmark,
  },
];

const PRINCIPLES = [
  "A calm styling experience",
  "Editorial guidance that feels human",
  "A wardrobe worth returning to",
];

export default function HomePage() {
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setHasProfile(Boolean(localStorage.getItem("mira_profile_id")));
    }
  }, []);

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-20">
        <section className="mira-container py-8 sm:py-10">
          <div className="mira-section overflow-hidden px-5 py-6 sm:px-7 sm:py-8">
            <div className="relative">
              <div className="absolute inset-x-0 top-0 h-48 rounded-[2rem] bg-[radial-gradient(circle_at_top,rgba(196,162,101,0.18),transparent_58%)]" />
              <div className="relative">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.7 }}
                >
                  <MiraLogo size="md" />
                </motion.div>

                <motion.div
                  className="mx-auto mt-8 max-w-xl text-center"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15, duration: 0.65 }}
                >
                  <p className="mira-overline">MIRA</p>
                  <h1 className="mira-page-title mt-3">
                    A calmer way to see a look on you before you commit.
                  </h1>
                  <p className="mira-subtitle mt-4">
                    MIRA brings virtual try-on, concise editorial guidance, and a saved wardrobe into one elegant experience.
                  </p>
                </motion.div>

                <motion.div
                  className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.55 }}
                >
                  <Link href="/try-on" className="mira-btn-primary w-full sm:w-auto">
                    {hasProfile ? "Visualize a New Look" : "Begin with a Look"}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link href={hasProfile ? "/wardrobe" : "/onboarding"} className="mira-btn-secondary w-full sm:w-auto">
                    {hasProfile ? "Open Your Wardrobe" : "Shape Your Style Profile"}
                  </Link>
                </motion.div>

                <motion.div
                  className="mt-8 grid gap-3 sm:grid-cols-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4, duration: 0.6 }}
                >
                  {PRINCIPLES.map((item) => (
                    <div
                      key={item}
                      className="rounded-[1.5rem] border border-black/5 bg-white/68 px-4 py-4 text-left shadow-[0_10px_26px_rgba(48,32,20,0.05)]"
                    >
                      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-[#f4ece1]">
                        <Wand2 className="h-4 w-4 text-mira-gold" strokeWidth={1.8} />
                      </div>
                      <p className="text-[0.9rem] leading-[1.6] text-mira-graphite">{item}</p>
                    </div>
                  ))}
                </motion.div>
              </div>
            </div>
          </div>
        </section>

        <section className="mira-container pb-8">
          <div className="grid gap-4 md:grid-cols-3">
            {ENTRY_CARDS.map((card, index) => {
              const Icon = card.icon;
              return (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.08, duration: 0.5 }}
                >
                  <Link href={card.href} className="block h-full">
                    <div className="mira-card h-full p-5 transition-transform duration-300 hover:-translate-y-[2px]">
                      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#f3ece2]">
                        <Icon className="h-5 w-5 text-mira-charcoal" strokeWidth={1.8} />
                      </div>
                      <h2 className="mt-5 text-heading text-mira-charcoal">{card.title}</h2>
                      <p className="mt-3 text-body text-mira-slate">{card.description}</p>
                      <div className="mt-6 inline-flex items-center gap-2 text-[0.78rem] uppercase tracking-[0.18em] text-mira-gold">
                        Enter
                        <ArrowRight className="h-3.5 w-3.5" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </section>

        <section className="mira-container pb-12">
          <motion.div
            className="mira-card-elevated overflow-hidden p-6 sm:p-8"
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="grid gap-6 md:grid-cols-[1.1fr_0.9fr] md:items-center">
              <div>
                <p className="mira-overline">How it feels</p>
                <h2 className="mt-3 text-[2rem] leading-[1] tracking-[-0.04em] text-mira-charcoal sm:text-[2.4rem]">
                  Upload in moments. Leave with clarity.
                </h2>
                <p className="mt-4 max-w-xl text-body-lg text-mira-slate">
                  MIRA is designed to feel composed from the first upload to the final save, with a clearer sense of what works and why.
                </p>
              </div>

              <div className="grid gap-3">
                {[
                  "Start with a portrait and garment",
                  "Get an editorial read while the look is still fresh",
                  "Save the looks you want to revisit later",
                ].map((item, index) => (
                  <div
                    key={item}
                    className="rounded-[1.4rem] border border-black/5 bg-[#f8f3ec] px-4 py-4 text-body text-mira-graphite"
                  >
                    <span className="mr-3 inline-flex h-7 w-7 items-center justify-center rounded-full bg-white text-[0.76rem] font-semibold text-mira-gold">
                      {index + 1}
                    </span>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </section>
      </main>
    </>
  );
}
