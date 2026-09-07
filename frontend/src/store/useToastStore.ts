"use client";

/**
 * Transient celebration messages.
 *
 * A store rather than component state because the toast is *raised* by the
 * lesson player and *shown* on the path the learner lands on afterwards — the
 * two never exist at the same time, so there is no component to hold it.
 */

import { create } from "zustand";

import type { IconRef } from "@/lib/icon-paths";

export interface Toast {
  id: number;
  icon: IconRef;
  title: string;
  detail: string;
  color: string;
}

interface ToastState {
  toasts: Toast[];
  push: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: number) => void;
}

let nextId = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => set((state) => ({ toasts: [...state.toasts, { ...toast, id: nextId++ }] })),
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((item) => item.id !== id) })),
}));
