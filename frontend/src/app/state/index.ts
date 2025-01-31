export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  error: string | null;
  showLoginModal: boolean;
}

export const initialAuthState: AuthState = {
  isAuthenticated: false,
  token: null,
  error: null,
  showLoginModal: false,
};
export interface ApplicationState {
  auth: AuthState;
}
