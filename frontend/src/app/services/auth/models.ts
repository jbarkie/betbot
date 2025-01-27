import { Signal } from "@angular/core";
import { LoginRequest, RegisterRequest } from "../../components/models";

export interface AuthStoreMethods {
    login: (request: LoginRequest) => Promise<void>;
    register: (request: RegisterRequest) => Promise<void>;
    initializeAuth: () => Promise<void>;
    showLoginModal: () => void;
    hideLoginModal: () => void;
}

export interface AuthStoreSignals {
    isAuthenticated: Signal<boolean>;
    token: Signal<string | null>;
    error: Signal<string | null>;
    showLoginModal: Signal<boolean>;
    hasError: Signal<boolean>;
}

export type AuthStoreService = AuthStoreMethods & AuthStoreSignals;