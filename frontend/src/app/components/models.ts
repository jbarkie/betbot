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
}

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
}

export type SettingsResponse = {
  success: boolean;
  message: string;
  username: string;
  email: string;
  email_notifications_enabled: boolean;
};