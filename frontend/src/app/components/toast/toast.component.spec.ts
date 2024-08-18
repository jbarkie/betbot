import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { BehaviorSubject } from 'rxjs';

import { ToastComponent } from './toast.component';
import { ToastService } from './toast.service';

describe('ToastComponent', () => {
  let component: ToastComponent;
  let fixture: ComponentFixture<ToastComponent>;
  let toastService: jest.Mocked<ToastService>;
  let toastSubject: BehaviorSubject<any>;

  beforeEach(async () => {
    toastSubject = new BehaviorSubject<any>(null);
    const toastServiceMock = {
      toast$: toastSubject.asObservable(),
    } as Partial<ToastService>;

    await TestBed.configureTestingModule({
      imports: [ToastComponent],
      providers: [{ provide: ToastService, useValue: toastServiceMock }],
    }).compileComponents();

    fixture = TestBed.createComponent(ToastComponent);
    component = fixture.componentInstance;
    toastService = TestBed.inject(ToastService) as jest.Mocked<ToastService>;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with null toast', () => {
    expect(component.toast).toBeNull();
  });

  it('should set toast when service emits a toast', fakeAsync(() => {
    const testToast = { type: 'success', message: 'Test message' };
    toastSubject.next(testToast);
    fixture.detectChanges();

    expect(component.toast).toEqual(testToast);

    tick(5000);
    expect(component.toast).toBeNull();
  }));
  
  it('should set correct class for toast success', () => {
    const testToast = { type: 'success', message: 'Test message' };
    toastSubject.next(testToast);
    fixture.detectChanges();

    const toastElement = fixture.nativeElement.querySelector('.toast');
    expect(toastElement).toBeTruthy();

    const alertElement = fixture.nativeElement.querySelector('.alert');
    expect(alertElement).toBeTruthy();
    expect(alertElement.classList).toContain('alert-success');
    expect(alertElement.classList).not.toContain('alert-error');
  });

  it('should set correct class for toast error', () => {
    const testToast = { type: 'error', message: 'Test message' };
    toastSubject.next(testToast);
    fixture.detectChanges();

    const toastElement = fixture.nativeElement.querySelector('.toast');
    expect(toastElement).toBeTruthy();

    const alertElement = fixture.nativeElement.querySelector('.alert');
    expect(alertElement).toBeTruthy();
    expect(alertElement.classList).toContain('alert-error');
    expect(alertElement.classList).not.toContain('alert-success');
  });

  it('should display correct message', () => {
    const testToast = { type: 'success', message: 'Test message' };
    toastSubject.next(testToast);
    fixture.detectChanges();

    const messageElement = fixture.nativeElement.querySelector('.alert span');
    expect(messageElement).toBeTruthy();
    expect(messageElement.textContent).toBe('Test message');
  });

  it('should not display toast when toast is null', () => {
    toastSubject.next(null);
    fixture.detectChanges();

    const toastElement = fixture.nativeElement.querySelector('.toast');
    expect(toastElement).toBeFalsy();
  });

  it('should unsubscribe on destroy', () => {
    const unsubscribeSpy = jest.spyOn(component['subscription'] as any, 'unsubscribe');
    component.ngOnDestroy();
    expect(unsubscribeSpy).toHaveBeenCalled();
  });
});
