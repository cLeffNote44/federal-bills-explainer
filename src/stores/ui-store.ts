import { create } from "zustand";

interface UIState {
  mobileNavOpen: boolean;
  authModalOpen: boolean;
  authModalMode: "login" | "register";

  setMobileNavOpen: (open: boolean) => void;
  openAuthModal: (mode?: "login" | "register") => void;
  closeAuthModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  mobileNavOpen: false,
  authModalOpen: false,
  authModalMode: "login",

  setMobileNavOpen: (open) => set({ mobileNavOpen: open }),
  openAuthModal: (mode = "login") =>
    set({ authModalOpen: true, authModalMode: mode }),
  closeAuthModal: () => set({ authModalOpen: false }),
}));
