export type Game = {
  id: string;
  sport: string;
  awayTeam: string;
  homeTeam: string;
  date: string;
  time: string;
  homeOdds: string;
  awayOdds: string;
};

export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterRequest = {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
};

export type RegisterResponse = {
  access_token: string;
  token_type: string;
};

export interface LoginError {
  status?: number;
  message?: string;
}

export type SettingsRequest = {
  username: string;
  email: string;
  password?: string;
  email_notifications_enabled: boolean;
};

export type SettingsResponse = {
  success: boolean;
  message: string;
  username: string;
  email: string;
  email_notifications_enabled: boolean;
};

export type AnalyticsRequest = {
  gameId: string;
};

export type TeamAnalytics = {
  name: string;
  winning_percentage: number;
  rolling_win_percentage?: number;
  offensive_rating?: number;
  defensive_rating?: number;
  days_rest?: number;
  momentum_score?: number;
};

export type AnalyticsResponse = {
  id: string;
  home_team: string;
  away_team: string;
  predicted_winner: string;
  win_probability: number;
  home_analytics?: TeamAnalytics;
  away_analytics?: TeamAnalytics;
  key_factors?: Record<string, string>;
  confidence_level?: string;
  ml_model_name?: string;
  ml_confidence?: string;
  home_win_probability?: number;
  away_win_probability?: number;
  prediction_method?: 'machine_learning' | 'rule_based';
  feature_importance?: Record<string, number>;
};
