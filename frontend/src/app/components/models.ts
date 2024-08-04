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
