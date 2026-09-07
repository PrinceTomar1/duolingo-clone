"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";

import { Icon } from "@/components/ui/Icon";
import type { IconName } from "@/lib/icon-paths";

/**
 * The shared modal chrome: scrim, centred card, escape-to-close.
 *
 * Every dialog in the app uses this, so focus handling and the close key are
 * implemented once rather than three slightly different times.
 */
interface ModalProps {
  title: string;
  icon: IconName;
  accentColor: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function Modal({ title, icon, accentColor, onClose, children }: ModalProps) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    // Body scroll is locked while a modal is open so the page behind it does
    // not move under the scrim on mobile.
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true">
      <button type="button" aria-label="Close" onClick={onClose} className="absolute inset-0 bg-black/50" />

      <motion.div
        initial={{ opacity: 0, y: 40, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 420, damping: 32 }}
        className="relative w-full max-w-sm rounded-t-3xl bg-snow p-6 pb-8 dark:bg-night-raised sm:rounded-3xl"
      >
        <div className="mb-4 flex flex-col items-center gap-2" style={{ color: accentColor }}>
          {/* The accent is set once on the wrapper; the icon inherits it via
              currentColor, so there is no colour prop to keep in sync. */}
          <Icon name={icon} size={48} />
          <h2 className="text-center text-xl font-extrabold">
            {title}
          </h2>
        </div>
        {children}
      </motion.div>
    </div>
  );
}
