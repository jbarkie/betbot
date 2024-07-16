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
  token: string;
};

export type RegisterRequest = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

export type RegisterResponse = {
  accessToken: string;
  tokenType: string;
};
