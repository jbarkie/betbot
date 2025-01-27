import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';

import { LoginComponent } from './login.component';
import { LoginService } from './login.service';
import { ToastService } from '../toast/toast.service';
import { AuthService } from '../../services/auth/auth.service';
import { ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { authActions } from '../../state/auth/auth.actions';
import { AuthStore } from '../../services/auth/auth.store';
import { AuthStoreService } from '../../services/auth/models';
import { signal } from '@angular/core';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockToastService: jest.Mocked<ToastService>;
  let mockAuthStore: jest.Mocked<AuthStoreService>;

  beforeEach(async () => {
    jest.spyOn(console, 'error').mockImplementation(jest.fn());

    mockToastService = {
      showSuccess: jest.fn(),
      showError: jest.fn(),
    } as unknown as jest.Mocked<ToastService>;

    mockAuthStore = {
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      initializeAuth: jest.fn(),
      showLoginModal: jest.fn(),
      hideLoginModal: jest.fn(),
      isAuthenticated: signal(false),
      token: signal(null),
      error: signal(null),
      hasError: signal(false),
    } as unknown as jest.Mocked<AuthStoreService>;

    await TestBed.configureTestingModule({
      imports: [LoginComponent, ReactiveFormsModule],
      providers: [
        provideMockStore(),
        { provide: ToastService, useValue: mockToastService },
        { provide: AuthStore, useValue: mockAuthStore },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({}),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize login for with empty fields', () => {
    expect(component.loginForm.get('username')?.value).toBe('');
    expect(component.loginForm.get('password')?.value).toBe('');
  });

  it('should mark form as invalid when empty', () => {
    expect(component.loginForm.valid).toBeFalsy();
  });

  it('should mark form as valid when fields are populated', () => {
    component.loginForm.patchValue({
      username: 'username',
      password: 'password',
    });
    expect(component.loginForm.valid).toBeTruthy();
  });

  it('should mark username as invalid after field is touched', () => {
    component.loginForm.get('username')?.markAsTouched();
    expect(component.isInvalid('username')).toBeTruthy();
  });

  it('should mark password as invalid after field is touched', () => {
    component.loginForm.get('password')?.markAsTouched();
    expect(component.isInvalid('password')).toBeTruthy();
  });

  it('should call loginService.login() when form is submitted', async () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockAuthStore.login.mockResolvedValue(undefined);
    await component.onSubmit();
    expect(mockAuthStore.login).toHaveBeenCalledWith(loginRequest);
    expect(mockToastService.showSuccess).toHaveBeenCalledWith(
      'Login successful'
    );
  });

  it('should handle login error', async () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockAuthStore.login?.mockRejectedValue({ status: 401 });

    await component.onSubmit();

    expect(mockToastService.showError).toHaveBeenCalledWith(
      'Invalid username or password.'
    );
  });

  it('should reset form after successful login', async () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockAuthStore.login?.mockResolvedValue(undefined);

    await component.onSubmit();

    expect(component.loginForm.get('username')?.value).toBeNull();
    expect(component.loginForm.get('password')?.value).toBeNull();
  });

  it('should call hideLoginModal when register link is clicked', () => {
    component.onRegisterLinkClick();
    expect(mockAuthStore.hideLoginModal).toHaveBeenCalled();
  });
});
