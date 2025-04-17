import { setupZoneTestEnv } from 'jest-preset-angular/setup-env/zone';
    
setupZoneTestEnv();

Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
        matches: false,
    })),
});