import { create } from 'zustand';

/**
 * WebSocket 连接状态 Store
 */
export interface WSState {
  connected: boolean;
  channels: Record<string, boolean>;
  lastError: string | null;
  fallbackPolling: boolean;
  lastMessage: Record<string, unknown> | null;
}

export interface WSActions {
  setConnected: (connected: boolean) => void;
  setChannel: (channel: string, active: boolean) => void;
  setError: (error: string | null) => void;
  setFallbackPolling: (polling: boolean) => void;
  setLastMessage: (msg: Record<string, unknown> | null) => void;
}

const initialState: WSState = {
  connected: false,
  channels: {},
  lastError: null,
  fallbackPolling: false,
  lastMessage: null,
};

export const useWSStore = create<WSState & WSActions>()((set) => ({
  ...initialState,

  setConnected: (connected) => set({ connected }),

  setChannel: (channel, active) =>
    set((state) => ({
      channels: { ...state.channels, [channel]: active },
    })),

  setError: (error) => set({ lastError: error }),

  setFallbackPolling: (polling) => set({ fallbackPolling: polling }),

  setLastMessage: (msg) => set({ lastMessage: msg }),
}));
