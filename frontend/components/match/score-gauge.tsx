"use client";

import { motion } from "framer-motion";

interface ScoreGaugeProps {
  /** 0–100 fit score. */
  score: number;
  label?: string;
}

function toneColor(score: number): string {
  if (score >= 70) return "hsl(var(--success))";
  if (score >= 45) return "hsl(var(--warning))";
  return "hsl(var(--danger))";
}

/** Animated circular gauge for the candidate fit score. */
export function ScoreGauge({ score, label = "Fit Score" }: ScoreGaugeProps) {
  const radius = 70;
  const stroke = 12;
  const normalizedRadius = radius - stroke / 2;
  const circumference = 2 * Math.PI * normalizedRadius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;
  const color = toneColor(clamped);

  return (
    <div className="relative flex h-[160px] w-[160px] items-center justify-center">
      <svg height={radius * 2} width={radius * 2} className="-rotate-90">
        <circle
          stroke="hsl(var(--surface-2))"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <motion.circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <motion.span
          className="text-3xl font-semibold"
          style={{ color }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {Math.round(clamped)}
        </motion.span>
        <span className="text-xs text-muted">{label}</span>
      </div>
    </div>
  );
}
