"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

/**
 * The burst on the completion screen.
 *
 * Forty absolutely-positioned squares given randomised start columns, delays
 * and rotations, animated straight down past the viewport. Generated once with
 * `useMemo` so a re-render does not reshuffle mid-fall.
 */

const COLORS = ["#58CC02", "#1CB0F6", "#FFC800", "#FF4B4B", "#CE82FF", "#FF9600"];
const PIECE_COUNT = 40;

export function Confetti() {
  const pieces = useMemo(
    () =>
      Array.from({ length: PIECE_COUNT }, (_, index) => ({
        id: index,
        left: Math.random() * 100,
        delay: Math.random() * 1.2,
        duration: 2.4 + Math.random() * 1.6,
        rotation: Math.random() * 720 - 360,
        color: COLORS[index % COLORS.length] ?? "#58CC02",
        size: 6 + Math.random() * 7,
      })),
    [],
  );

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
      {pieces.map((piece) => (
        <motion.span
          key={piece.id}
          initial={{ y: "-10vh", opacity: 1, rotate: 0 }}
          animate={{ y: "110vh", opacity: [1, 1, 0], rotate: piece.rotation }}
          transition={{ duration: piece.duration, delay: piece.delay, ease: "linear" }}
          style={{
            left: `${piece.left}%`,
            width: piece.size,
            height: piece.size * 1.6,
            backgroundColor: piece.color,
          }}
          className="absolute top-0 rounded-sm"
        />
      ))}
    </div>
  );
}
