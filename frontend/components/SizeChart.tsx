"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getSizeChart } from "@/lib/api";

interface SizeEntry {
  size_label: string;
  measurements: Record<string, number>;
}

interface SizeChartData {
  brand: string;
  garment_category: string;
  sizes: SizeEntry[];
}

interface SizeChartProps {
  brand?: string;
  category?: string;
  highlightSize?: string;
}

export default function SizeChart({
  brand,
  category,
  highlightSize,
}: SizeChartProps) {
  const [chart, setChart] = useState<SizeChartData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    loadChart();
  }, [brand, category]);

  async function loadChart() {
    const res = await getSizeChart(brand, category);
    if (res.success && res.data) {
      setChart(res.data);
    }
    setIsLoading(false);
  }

  if (isLoading) {
    return (
      <div className="mira-card p-5">
        <div className="h-4 bg-mira-sand/30 rounded mira-shimmer w-1/3 mb-3" />
        <div className="h-20 bg-mira-sand/20 rounded mira-shimmer" />
      </div>
    );
  }

  if (!chart || chart.sizes.length === 0) return null;

  const measurementKeys = chart.sizes.length > 0
    ? Object.keys(chart.sizes[0].measurements)
    : [];

  return (
    <div className="mira-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 flex items-center justify-between hover:bg-mira-sand/10 transition-colors"
      >
        <div>
          <p className="mira-overline text-left">Size Reference</p>
          <p className="text-caption text-mira-slate mt-1">
            {chart.brand || "Standard"} &middot;{" "}
            {chart.garment_category || "General"}
          </p>
        </div>
        <motion.span
          className="text-mira-slate"
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-mira-sand/40">
                    <th className="py-2.5 pr-4 text-overline uppercase tracking-widest text-mira-slate font-medium">
                      Size
                    </th>
                    {measurementKeys.map((key) => (
                      <th
                        key={key}
                        className="py-2.5 px-4 text-overline uppercase tracking-widest text-mira-slate font-medium text-center"
                      >
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {chart.sizes.map((entry) => {
                    const isHighlighted =
                      highlightSize &&
                      entry.size_label.toLowerCase() ===
                        highlightSize.toLowerCase();
                    return (
                      <tr
                        key={entry.size_label}
                        className={`border-b border-mira-sand/20 transition-colors ${
                          isHighlighted
                            ? "bg-mira-gold/8"
                            : "hover:bg-mira-sand/10"
                        }`}
                      >
                        <td
                          className={`py-3 pr-4 text-body font-medium ${
                            isHighlighted
                              ? "text-mira-gold"
                              : "text-mira-charcoal"
                          }`}
                        >
                          {entry.size_label}
                          {isHighlighted && (
                            <span className="ml-2 text-[10px] text-mira-gold bg-mira-gold/10 px-1.5 py-0.5 rounded-full">
                              Suggested
                            </span>
                          )}
                        </td>
                        {measurementKeys.map((key) => (
                          <td
                            key={key}
                            className="py-3 px-4 text-body text-mira-graphite text-center"
                          >
                            {entry.measurements[key]} cm
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
