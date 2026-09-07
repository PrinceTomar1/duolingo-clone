"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";

import { Icon } from "@/components/ui/Icon";
import { useToastStore } from "@/store/useToastStore";

/**
 * The stack of celebration toasts, rendered once by the app shell.
 *
 * Each toast dismisses itself after four seconds and can be dismissed by tap.
 * Positioned above the mobile tab bar so it never covers navigation.
 */
export function ToastStack() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-20 z-40 flex flex-col items-center gap-2 px-4 lg:bottom-6">
      <AnimatePresence initial={false}>
        {toasts.map((toast) => (
          <ToastCard key={toast.id} toast={toast} onDismiss={() => dismiss(toast.id)} />
        ))}
      </AnimatePresence>
    </div>
  );
}

interface ToastCardProps {
  toast: ReturnType<typeof useToastStore.getState>["toasts"][number];
  onDismiss: () => void;
}

function ToastCard({ toast, onDismiss }: ToastCardProps) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, 4000);
    return () => window.clearTimeout(timer);
  }, [onDismiss]);

  return (
    <motion.button
      type="button"
      onClick={onDismiss}
      layout
      initial={{ opacity: 0, y: 24, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 12, scale: 0.95 }}
      transition={{ type: "spring", stiffness: 420, damping: 30 }}
      role="status"
      className="pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-2xl border-2 border-b-4 bg-snow px-4 py-3 text-left shadow-lg dark:bg-night-raised"
      style={{ borderColor: toast.color }}
    >
      <Icon name={toast.icon} size={30} style={{ color: toast.color }} />
      <span className="min-w-0">
        <span className="block text-sm font-extrabold" style={{ color: toast.color }}>
          {toast.title}
        </span>
        <span className="block truncate text-xs font-bold text-wolf">{toast.detail}</span>
      </span>
    </motion.button>
  );
}
