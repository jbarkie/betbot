export type Game = {
  id: string;
  sport: string;
  awayTeam: string;
  homeTeam: string;
  date: string;
  time: string;
  odds: { [key: string]: string };
};
