"use client";

import { motion } from "framer-motion";

interface CommentaryDisplayProps {
  text: string;
  vibeTags?: string[];
  occasionTags?: string[];
  stylingSuggestions?: string[];
  refinementNotes?: string[];
  isLoading?: boolean;
}

export default function CommentaryDisplay({
  text,
  vibeTags = [],
  occasionTags = [],
  stylingSuggestions = [],
  refinementNotes = [],
  isLoading = false,
}: CommentaryDisplayProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="h-4 bg-mira-sand/30 rounded mira-shimmer" />
        <div className="h-4 bg-mira-sand/30 rounded w-5/6 mira-shimmer" />
        <div className="h-4 bg-mira-sand/30 rounded w-2/3 mira-shimmer" />
      </div>
    );
  }

  return (
    <motion.div
      className="space-y-5"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Main commentary */}
      <p className="text-body-lg text-mira-graphite leading-relaxed italic font-display">
        &ldquo;{text}&rdquo;
      </p>

      {/* Tags */}
      {(vibeTags.length > 0 || occasionTags.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          {vibeTags.map((tag) => (
            <span key={tag} className="mira-tag mira-tag-gold text-[11px]">
              {tag}
            </span>
          ))}
          {occasionTags.map((tag) => (
            <span key={tag} className="mira-tag text-[11px]">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Styling suggestions */}
      {stylingSuggestions.length > 0 && (
        <div>
          <p className="mira-overline mb-2">Styling Ideas</p>
          <ul className="space-y-1.5">
            {stylingSuggestions.map((suggestion, i) => (
              <li
                key={i}
                className="text-body text-mira-graphite pl-3 border-l-2 border-mira-gold/30"
              >
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Refinement notes */}
      {refinementNotes.length > 0 && (
        <div>
          <p className="mira-overline mb-2">Refinements to Consider</p>
          <ul className="space-y-1.5">
            {refinementNotes.map((note, i) => (
              <li
                key={i}
                className="text-body text-mira-slate pl-3 border-l-2 border-mira-sand/50 italic"
              >
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
