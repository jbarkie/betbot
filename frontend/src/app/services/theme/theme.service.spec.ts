import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  let localStorageMock: { [key: string]: string } = {};
  let matchMediaMock: jest.Mock;

  beforeEach(() => {
    localStorageMock = {};
    matchMediaMock = jest.fn();

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn((key) => localStorageMock[key] || null),
        setItem: jest.fn((key, value) => (localStorageMock[key] = value)),
        removeItem: jest.fn((key) => delete localStorageMock[key]),
      },
      writable: true,
    });

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      value: matchMediaMock,
      writable: true,
    });

    // Default to light system theme
    matchMediaMock.mockImplementation(() => ({
      matches: false,
    }));

    TestBed.configureTestingModule({});
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('should be created', () => {
    service = TestBed.inject(ThemeService);
    expect(service).toBeTruthy();
  });

  describe('initialization', () => {
    it('should initialize with light theme when no saved theme exists and system prefers light', () => {
      service = TestBed.inject(ThemeService);

      expect(service.theme()).toBe('light');
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    it('should initialize with dark theme when no saved theme exists and system prefers dark', () => {
      // Set up dark theme preference before creating service
      matchMediaMock.mockImplementation(() => ({
        matches: true, // System prefers dark theme
      }));

      service = TestBed.inject(ThemeService);

      expect(service.theme()).toBe('dark');
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('should use saved theme from localStorage over system preference', () => {
      matchMediaMock.mockImplementation(() => ({
        matches: true, // System prefers dark theme
      }));
      localStorageMock['theme'] = 'light'; // But light theme is saved

      service = TestBed.inject(ThemeService);

      expect(service.theme()).toBe('light');
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });
  });

  describe('setTheme', () => {
    beforeEach(() => {
      service = TestBed.inject(ThemeService);
    });

    it('should update theme in localStorage', () => {
      service.setTheme('dark');

      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark');
      expect(localStorageMock['theme']).toBe('dark');
    });

    it('should update data-theme attribute on html element', () => {
      service.setTheme('dark');

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('should update theme signal', () => {
      service.setTheme('dark');

      expect(service.theme()).toBe('dark');
    });
  });

  describe('toggleTheme', () => {
    beforeEach(() => {
      service = TestBed.inject(ThemeService);
    });

    it('should toggle from light to dark', () => {
      service.setTheme('light');
      service.toggleTheme();

      expect(service.theme()).toBe('dark');
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('should toggle from dark to light', () => {
      service.setTheme('dark');
      service.toggleTheme();

      expect(service.theme()).toBe('light');
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    it('should persist toggled theme to localStorage', () => {
      service.setTheme('light');
      service.toggleTheme();

      expect(localStorage.setItem).toHaveBeenLastCalledWith('theme', 'dark');
    });
  });
});
