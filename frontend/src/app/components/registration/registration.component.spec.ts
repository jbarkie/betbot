import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { signal } from '@angular/core';
import { AuthStore } from '../../services/auth/auth.store';
import { ToastService } from '../toast/toast.service';
import { RegistrationComponent } from './registration.component';

const mockAuthStore = {
  register: jest.fn(),
  isAuthenticated: signal(false),
  token: signal(null),
  error: signal(null),
  hasError: signal(false),
}

describe('RegistrationComponent', () => {
  let component: RegistrationComponent;
  let fixture: ComponentFixture<RegistrationComponent>;
  let router: jest.Mocked<Router>;
  let toastService: jest.Mocked<ToastService>;

  beforeEach(async () => {
    jest.spyOn(console, 'error').mockImplementation(jest.fn());

    const routerMock = {
      navigate: jest.fn(),
    };
    const toastServiceMock = {
      showSuccess: jest.fn(),
      showError: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [RegistrationComponent, ReactiveFormsModule],
      providers: [
        { provide: Router, useValue: routerMock },
        { provide: ToastService, useValue: toastServiceMock },
        { provide: AuthStore, useValue: mockAuthStore },
      ],
    }).compileComponents();

    router = TestBed.inject(Router) as jest.Mocked<Router>;
    toastService = TestBed.inject(ToastService) as jest.Mocked<ToastService>;

    fixture = TestBed.createComponent(RegistrationComponent);
    component = fixture.componentInstance;
    component.ngOnInit(); // Manually call ngOnInit to initialize the form
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize form with empty fields', () => {
    expect(component.registration.get('username')?.value).toBe('');
    expect(component.registration.get('firstName')?.value).toBe('');
    expect(component.registration.get('lastName')?.value).toBe('');
    expect(component.registration.get('email')?.value).toBe('');
    expect(component.registration.get('password')?.value).toBe('');
    expect(component.registration.get('confirmPassword')?.value).toBe('');
  });

  it('should validate required fields', () => {
    expect(component.registration.valid).toBeFalsy();
    expect(
      component.registration.get('username')?.hasError('required')
    ).toBeTruthy();
    expect(
      component.registration.get('firstName')?.hasError('required')
    ).toBeTruthy();
    expect(
      component.registration.get('lastName')?.hasError('required')
    ).toBeTruthy();
    expect(
      component.registration.get('email')?.hasError('required')
    ).toBeTruthy();
    expect(
      component.registration.get('password')?.hasError('required')
    ).toBeTruthy();
    expect(
      component.registration.get('confirmPassword')?.hasError('required')
    ).toBeTruthy();
  });

  it('should validate email format', () => {
    const emailControl = component.registration.get('email');
    emailControl?.setValue('invalid-email');
    expect(emailControl?.hasError('email')).toBeTruthy();
    emailControl?.setValue('valid@email.com');
    expect(emailControl?.hasError('email')).toBeFalsy();
  });

  it('should validate password length', () => {
    const passwordControl = component.registration.get('password');
    passwordControl?.setValue('short');
    expect(passwordControl?.hasError('minlength')).toBeTruthy();
    passwordControl?.setValue('long-enough-password');
    expect(passwordControl?.hasError('minlength')).toBeFalsy();
  });

  it('should validate password match', () => {
    component.registration.patchValue({
      password: 'password123',
      confirmPassword: 'password456',
    });
    expect(component.registration.hasError('passwordMismatch')).toBeTruthy();
    component.registration.patchValue({
      password: 'password123',
      confirmPassword: 'password123',
    });
    expect(component.registration.hasError('passwordMismatch')).toBeFalsy();
  });

  it('should mark control as invalid when touched', () => {
    const usernameControl = component.registration.get('username');
    usernameControl?.markAsTouched();
    expect(component.isInvalid(usernameControl)).toBeTruthy();
  });

  it('should handle successful registration when form is valid', async () => {
    const registrationRequest = {
      username: 'testuser',
      firstName: 'Test',
      lastName: 'User',
      email: 'test@example.com',
      password: 'password123',
      confirmPassword: 'password123',
    };
    component.registration.patchValue(registrationRequest);

    const expectedRequest = {
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      email: 'test@example.com',
      password: 'password123',
    };

    mockAuthStore.register.mockResolvedValue(undefined);

    await component.onSubmit();

    expect(mockAuthStore.register).toHaveBeenCalledWith(expectedRequest);
    expect(router.navigate).toHaveBeenCalledWith(['/']);
    expect(toastService.showSuccess).toHaveBeenCalledWith(
      'Registration successful'
    );
  });

  it('should handle registration error', async () => {
    const registrationRequest = {
      username: 'testuser',
      firstName: 'Test',
      lastName: 'User',
      email: 'test@example.com',
      password: 'password123',
      confirmPassword: 'password123',
    };
    component.registration.patchValue(registrationRequest);

    const error = {
      status: 403,
      message: 'Username already exists',
    };

    mockAuthStore.register.mockRejectedValue(error);

    await component.onSubmit();

    expect(router.navigate).not.toHaveBeenCalled();
    expect(toastService.showError).toHaveBeenCalledWith(
      'Username already exists.'
    );
  });
});
