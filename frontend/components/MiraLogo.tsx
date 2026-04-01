"use client";

import { motion } from "framer-motion";

interface MiraLogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  showTagline?: boolean;
}

const SIZES = {
  sm: "text-display-md",
  md: "text-display-lg",
  lg: "text-display-xl",
  xl: "text-[4.5rem]",
};

export default function MiraLogo({ size = "lg", showTagline = true }: MiraLogoProps) {
  return (
    <motion.div
      className="text-center"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <h1 className={`font-display ${SIZES[size]} text-mira-charcoal tracking-tight`}>
        MIRA
      </h1>
      {showTagline && (
        <motion.p
          className="text-overline uppercase tracking-[0.2em] text-mira-gold mt-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          Your Personal Stylist
        </motion.p>
      )}
    </motion.div>
  );
}
