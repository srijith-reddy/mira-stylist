"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { Bookmark, Home, Sparkles, User } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/try-on", label: "Try On", icon: Sparkles, primary: true },
  { href: "/wardrobe", label: "Wardrobe", icon: Bookmark },
  { href: "/profile", label: "Profile", icon: User },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <>
      <nav className="fixed left-0 right-0 top-0 z-50 border-b border-black/5 bg-[#fbf8f2]/82 backdrop-blur-2xl">
        <div className="mira-container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-black/5 bg-white/70 shadow-[0_8px_20px_rgba(35,24,15,0.05)]">
              <span className="font-display text-[1.15rem] tracking-[-0.05em] text-mira-charcoal">
                M
              </span>
            </div>
            <div>
              <p className="font-display text-[1.2rem] leading-none tracking-[-0.04em] text-mira-charcoal">
                MIRA
              </p>
              <p className="mt-1 text-[0.62rem] uppercase tracking-[0.24em] text-mira-gold">
                Personal Stylist
              </p>
            </div>
          </Link>

          <div className="hidden items-center gap-2 md:flex">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "inline-flex h-11 items-center rounded-full px-5 text-body font-medium transition-all duration-200",
                  pathname === item.href
                    ? item.primary
                      ? "bg-mira-charcoal text-white shadow-elevated"
                      : "bg-white/80 text-mira-charcoal shadow-soft"
                    : "text-mira-slate hover:bg-white/65 hover:text-mira-charcoal"
                )}
              >
                {item.label}
              </Link>
            ))}
            <div className="ml-2 rounded-full border border-black/5 bg-white/65 px-4 py-2 text-[0.72rem] uppercase tracking-[0.18em] text-mira-slate">
              By MIRA
            </div>
          </div>

          <Link
            href="/try-on"
            className="inline-flex h-10 items-center rounded-full bg-mira-charcoal px-4 text-[0.74rem] font-medium tracking-[0.16em] text-white md:hidden"
          >
            Try On
          </Link>
        </div>
      </nav>

      <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-black/5 bg-[#fbf8f2]/88 px-4 pb-[calc(env(safe-area-inset-bottom,0px)+0.75rem)] pt-3 backdrop-blur-2xl md:hidden">
        <div className="mx-auto flex max-w-md items-center justify-between gap-2 rounded-[1.7rem] border border-black/5 bg-white/72 px-3 py-2 shadow-[0_14px_40px_rgba(35,24,15,0.12)]">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex min-w-0 flex-1 flex-col items-center justify-center rounded-[1.2rem] px-2 py-2 text-[0.68rem] font-medium transition-all duration-200",
                  item.primary
                    ? isActive
                      ? "bg-mira-charcoal text-white shadow-elevated"
                      : "bg-mira-charcoal text-white"
                    : isActive
                    ? "bg-[#f4eee5] text-mira-charcoal"
                    : "text-mira-slate"
                )}
              >
                <Icon className="mb-1 h-[1.05rem] w-[1.05rem]" strokeWidth={1.8} />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
