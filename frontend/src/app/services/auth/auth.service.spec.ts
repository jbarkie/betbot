import { jwtDecode } from 'jwt-decode';
import { AuthService } from './auth.service';
import { TestBed } from '@angular/core/testing';

jest.mock('jwt-decode');

describe('AuthService', () => {
  let service: AuthService;
  let localStorageMock: { [key: string]: string } = {};

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthService);

    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key) => localStorageMock[key] || null),
        setItem: jest.fn((key, value) => (localStorageMock[key] = value)),
        removeItem: jest.fn((key) => delete localStorageMock[key]),
      },
      writable: true,
    });
  });

  afterEach(() => {
    localStorageMock = {};
    jest.resetAllMocks();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('setToken', () => {
    it('should set token in local storage', () => {
      service.setToken('token');
      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'token');
    });
  });

  describe('getToken', () => {
    it('should get token from local storage', () => {
      localStorageMock['token'] = 'token';
      expect(service.getToken()).toBe('token');
      expect(localStorage.getItem).toHaveBeenCalledWith('token');
    });

    it('should return null if token is not in local storage', () => {
      expect(service.getToken()).toBeNull();
    });
  });

  describe('isTokenValid', () => {
    it('should return false if token is not in local storage', () => {
      expect(service.isTokenValid()).toBe(false);
    });

    it('should return false if token is expired', () => {
      localStorageMock['token'] = 'token';
      (jwtDecode as jest.Mock).mockReturnValue({ exp: 1 });
      expect(service.isTokenValid()).toBe(false);
    });

    it('should return true for valid token', () => {
      localStorageMock['token'] = 'token';
      (jwtDecode as jest.Mock).mockReturnValue({
        exp: Date.now() / 1000 + 1000,
      });
      expect(service.isTokenValid()).toBe(true);
    });
  });

  describe('getTokenPayload', () => {
    it('should return null if no token exists', () => {
      expect(service.getTokenPayload()).toBeNull();
    });

    it('should return decoded payload for valid token', () => {
      const payload = { sub: 'user', exp: Date.now() / 1000 + 1000 };
      localStorageMock['token'] = 'token';
      (jwtDecode as jest.Mock).mockReturnValue(payload);
      expect(service.getTokenPayload()).toEqual(payload);
    });
  });

  describe('getUserId', () => {
    it('should return null if no token exists', () => {
      expect(service.getUserId()).toBeNull();
    });

    it('should return user id from token payload', () => {
      localStorageMock['token'] = 'token';
      (jwtDecode as jest.Mock).mockReturnValue({
        sub: 'user',
        exp: Date.now() / 1000 + 1000,
      });
      expect(service.getUserId()).toBe('user');
    });
  });
});
