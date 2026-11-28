import { setupZoneTestEnv } from 'jest-preset-angular/setup-env/zone';
    
setupZoneTestEnv();

// jsdom does not implement HTMLDialogElement.showModal()/close(). This stub
// covers only the open state and the close event that components react to;
// focus handling, inertness and Escape stay browser behavior.
if (typeof HTMLDialogElement.prototype.showModal !== 'function') {
    HTMLDialogElement.prototype.showModal = function (this: HTMLDialogElement) {
        this.setAttribute('open', '');
    };
    HTMLDialogElement.prototype.close = function (this: HTMLDialogElement) {
        if (!this.hasAttribute('open')) return;
        this.removeAttribute('open');
        this.dispatchEvent(new Event('close'));
    };
}

Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
        matches: false,
    })),
});