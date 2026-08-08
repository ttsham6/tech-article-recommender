import { useEffect, useState } from "react";
import liff from "@line/liff";

import { appConfig, isLiffConfigured } from "../config";
import type { LiffProfile } from "../types";

type LiffPhase = "loading" | "unconfigured" | "redirecting" | "ready" | "error";

export interface LiffState {
  phase: LiffPhase;
  statusText: string;
  statusClassName: string;
  profile: LiffProfile | null;
  token: string | null;
  isInClient: boolean;
  isConfigured: boolean;
  openWindow: (url: string) => void;
}

const initialState: Omit<LiffState, "openWindow"> = {
  phase: "loading",
  statusText: "LIFF 初期化中",
  statusClassName: "is-idle",
  profile: null,
  token: null,
  isInClient: false,
  isConfigured: isLiffConfigured(),
};

export function useLiff(): LiffState {
  const [state, setState] = useState(initialState);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      if (!isLiffConfigured()) {
        if (!cancelled) {
          setState((current) => ({
            ...current,
            phase: "unconfigured",
            statusText: "LIFF_ID 未設定",
            statusClassName: "is-pending",
          }));
        }
        return;
      }

      try {
        await liff.init({
          liffId: appConfig.liffId,
          withLoginOnExternalBrowser: true,
        });

        if (!liff.isLoggedIn()) {
          liff.login();
          if (!cancelled) {
            setState((current) => ({
              ...current,
              phase: "redirecting",
              statusText: "LINE ログイン遷移",
              statusClassName: "is-pending",
            }));
          }
          return;
        }

        const token = liff.getIDToken() ?? liff.getAccessToken() ?? null;
        const isInClient = liff.isInClient();
        let profile: LiffProfile | null = null;

        try {
          profile = await liff.getProfile();
        } catch (error) {
          console.warn("profile fetch failed", error);
        }

        if (!cancelled) {
          setState({
            phase: "ready",
            statusText: isInClient ? "LINE アプリ内" : "外部ブラウザ",
            statusClassName: isInClient ? "is-succeeded" : "is-pending",
            profile,
            token,
            isInClient,
            isConfigured: true,
          });
        }
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setState((current) => ({
            ...current,
            phase: "error",
            statusText: "LIFF 初期化失敗",
            statusClassName: "is-failed",
          }));
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  return {
    ...state,
    openWindow(url: string) {
      if (liff.openWindow) {
        liff.openWindow({ url, external: true });
        return;
      }
      window.open(url, "_blank", "noopener,noreferrer");
    },
  };
}
