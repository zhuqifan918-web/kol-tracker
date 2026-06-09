export interface Analysis {
  is_investment_related: boolean;
  tickers: string[];
  direction: "bullish" | "bearish" | "neutral" | null;
  summary: string | null;
  confidence: "high" | "medium" | "low" | null;
}

export interface Tweet {
  tweet_id: string;
  kol_username: string;
  kol_display_name: string;
  kol_avatar_url: string;
  kol_focus: string;
  content: string;
  tweet_url: string;
  published_at: string;
  fetched_at: string;
  analysis: Analysis;
}

export interface KOL {
  username: string;
  display_name: string;
  focus: string;
  enabled: boolean;
  notify: boolean;
}

export interface KolSummary {
  generated_at: string;
  focus_tickers: string[];
  overall_bias: "bullish" | "bearish" | "neutral";
  key_themes: string[];
  recent_shift: string;
  representative_quotes: string[];
}

export type Summaries = Record<string, KolSummary>;

