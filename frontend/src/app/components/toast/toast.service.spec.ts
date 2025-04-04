import { TestBed } from '@angular/core/testing';
import { ToastService } from './toast.service';

describe('ToastService', () => {
  let service: ToastService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ToastService],
    });
    service = TestBed.inject(ToastService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should emit success toast', (done) => {
    const testMessage = 'Test success message';

    service.toast$.subscribe((toast) => {
      expect(toast).toEqual({
        message: testMessage,
        type: 'success',
      });
      done();
    });

    service.showSuccess(testMessage);
  });

  it('should emit error toast', (done) => {
    const testMessage = 'Test error message';

    service.toast$.subscribe((toast) => {
      expect(toast).toEqual({
        message: testMessage,
        type: 'error',
      });
      done();
    });

    service.showError(testMessage);
  });

  it('should maintain separate subscriptions for multiple subscribers', () => {
    const successMessage = 'Success message';
    const errorMessage = 'Error message';
    const receivedToasts: any[] = [];

    // First subscriber
    const subscription1 = service.toast$.subscribe((toast) => {
      receivedToasts.push({ subscriber: 1, toast });
    });

    // Second subscriber
    const subscription2 = service.toast$.subscribe((toast) => {
      receivedToasts.push({ subscriber: 2, toast });
    });

    service.showSuccess(successMessage);
    service.showError(errorMessage);

    expect(receivedToasts).toEqual([
      {
        subscriber: 1,
        toast: { message: successMessage, type: 'success' },
      },
      {
        subscriber: 2,
        toast: { message: successMessage, type: 'success' },
      },
      {
        subscriber: 1,
        toast: { message: errorMessage, type: 'error' },
      },
      {
        subscriber: 2,
        toast: { message: errorMessage, type: 'error' },
      },
    ]);

    subscription1.unsubscribe();
    subscription2.unsubscribe();
  });
});
