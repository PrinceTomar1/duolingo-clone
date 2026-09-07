/**
 * Theme constants shared by a server component and a client store.
 *
 * This deliberately has no `"use client"` directive. A value imported into a
 * *server* component from a client module is replaced by a client-reference
 * proxy, not the value itself -- which silently turned the storage key into
 * `{}` inside the pre-paint script. Plain constants therefore live in their own
 * neutral module that either side can import.
 */

export const THEME_STORAGE_KEY = "duo-theme";

export type Theme = "light" | "dark";
