import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthStore } from './auth.store';
import { AuthService } from '../../services/auth/auth.service';
import { RegistrationService } from '../../components/registration/registration.service';
import { LoginService } from '../../components/login/login.service';
import { LoginRequest, RegisterRequest } from '../../components/models';
import { of, throwError } from 'rxjs';
import { provideHttpClient } from '@angular/common/http';

describe('AuthStore', () => {
  let store: InstanceType<typeof AuthStore>;
  let authService: {
    getToken: jest.Mock;
    isTokenValid: jest.Mock;
    setToken: jest.Mock;
    removeToken: jest.Mock;
  };
  let registrationService: { register: jest.Mock };
  let loginService: { login: jest.Mock };

  beforeEach(() => {
    authService = {
      getToken: jest.fn(),
      isTokenValid: jest.fn(),
      setToken: jest.fn(),
      removeToken: jest.fn(),
    };

    registrationService = {
      register: jest.fn(),
    };

    loginService = {
      login: jest.fn(),
    };

    TestBed.configureTestingModule({
      imports: [],
      providers: [
        AuthStore,
        { provide: AuthService, useValue: authService },
        { provide: RegistrationService, useValue: registrationService },
        { provide: LoginService, useValue: loginService },
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    store = TestBed.inject(AuthStore);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should create the store', () => {
    expect(store).toBeTruthy();
  });

  describe('initializeAuth', () => {
    it('should set isAuthenticated to true when token is valid', async () => {
      const mockToken = 'valid-token';
      authService.getToken.mockReturnValue(mockToken);
      authService.isTokenValid.mockReturnValue(true);

      await store.initializeAuth();

      expect(store.isAuthenticated()).toEqual(true);
      expect(store.token()).toEqual(mockToken);
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(false);
    });

    it('should set isAuthenticated to false when token is invalid', async () => {
      const mockToken = 'invalid-token';
      authService.getToken.mockReturnValue(mockToken);
      authService.isTokenValid.mockReturnValue(false);

      await store.initializeAuth();

      expect(authService.removeToken).toHaveBeenCalled();
      expect(store.isAuthenticated()).toEqual(false);
      expect(store.token()).toBeNull();
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(true);
    });

    it('should set isAuthenticated to false when no token exists', async () => {
      authService.getToken.mockReturnValue(null);

      await store.initializeAuth();

      expect(store.isAuthenticated()).toEqual(false);
      expect(store.token()).toBeNull();
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(true);
    });
  });

  describe('register', () => {
    it('should set isAuthenticated to true when registration succeeds', async () => {
      const mockRequest: RegisterRequest = {
        email: 'test@example.com',
        password: 'password123',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
      };
      const mockResponse = { access_token: 'new-token' };

      registrationService.register.mockReturnValue(of(mockResponse));

      await store.register(mockRequest);

      expect(registrationService.register).toHaveBeenCalledWith(mockRequest);
      expect(authService.setToken).toHaveBeenCalledWith(
        mockResponse.access_token
      );
      expect(store.isAuthenticated()).toEqual(true);
      expect(store.token()).toEqual(mockResponse.access_token);
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(false);
    });

    it('should set error when registration fails', async () => {
      const mockRequest: RegisterRequest = {
        email: 'test@example.com',
        password: 'password123',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
      };
      const mockError = new Error('Registration failed');

      registrationService.register.mockReturnValue(throwError(() => mockError));

      await store.register(mockRequest);

      expect(registrationService.register).toHaveBeenCalledWith(mockRequest);
      expect(store.isAuthenticated()).toEqual(false);
      expect(store.token()).toBeNull();
      expect(store.error()).toEqual(mockError.message);
      expect(store.shouldShowLoginModal()).toEqual(false);
    });
  });

  describe('login', () => {
    it('should set isAuthenticated to true when login succeeds', async () => {
      const mockRequest: LoginRequest = {
        username: 'test@example.com',
        password: 'password123',
      };
      const mockResponse = { access_token: 'new-token' };

      loginService.login.mockReturnValue(of(mockResponse));

      await store.login(mockRequest);

      expect(loginService.login).toHaveBeenCalledWith(mockRequest);
      expect(authService.setToken).toHaveBeenCalledWith(
        mockResponse.access_token
      );
      expect(store.isAuthenticated()).toEqual(true);
      expect(store.token()).toEqual(mockResponse.access_token);
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(false);
    });

    it('should set error when login fails', async () => {
      const mockRequest: LoginRequest = {
        username: 'test@example.com',
        password: 'password123',
      };
      const mockError = new Error('Login failed');

      loginService.login.mockReturnValue(throwError(() => mockError));

      await store.login(mockRequest);

      expect(loginService.login).toHaveBeenCalledWith(mockRequest);
      expect(store.isAuthenticated()).toEqual(false);
      expect(store.token()).toBeNull();
      expect(store.error()).toEqual(mockError.message);
      expect(store.shouldShowLoginModal()).toEqual(true);
    });
  });

  describe('logout', () => {
    it('should reset state to initial values', () => {
      // Setup initial state with login first
      const mockRequest: LoginRequest = {
        username: 'test@example.com',
        password: 'password123',
      };
      const mockResponse = { access_token: 'new-token' };

      loginService.login.mockReturnValue(of(mockResponse));

      // Call login and then logout
      store.login(mockRequest);
      store.logout();

      expect(authService.removeToken).toHaveBeenCalled();
      expect(store.isAuthenticated()).toEqual(false);
      expect(store.token()).toBeNull();
      expect(store.error()).toBeNull();
      expect(store.shouldShowLoginModal()).toEqual(false);
    });
  });

  describe('showLoginModal', () => {
    it('should set shouldShowLoginModal to true', () => {
      store.showLoginModal();
      expect(store.shouldShowLoginModal()).toEqual(true);
    });
  });

  describe('hideLoginModal', () => {
    it('should set shouldShowLoginModal to false', () => {
      // First show the modal
      store.showLoginModal();
      expect(store.shouldShowLoginModal()).toEqual(true);

      // Then hide it
      store.hideLoginModal();
      expect(store.shouldShowLoginModal()).toEqual(false);
    });
  });

  describe('computed selectors', () => {
    it('should return correct value for hasError', async () => {
      expect(store.hasError()).toEqual(false);

      // Create an error condition
      const mockRequest: LoginRequest = {
        username: 'test@example.com',
        password: 'wrong',
      };
      const mockError = new Error('Login failed');

      loginService.login.mockReturnValue(throwError(() => mockError));

      await store.login(mockRequest);

      expect(store.hasError()).toEqual(true);
    });

    it('should return correct value for isLoginModalDisplayed', () => {
      expect(store.isLoginModalDisplayed()).toEqual(false);

      store.showLoginModal();

      expect(store.isLoginModalDisplayed()).toEqual(true);
    });
  });
});
