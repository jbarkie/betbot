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

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockLoginService: jest.Mocked<LoginService>;
  let mockToastService: jest.Mocked<ToastService>;
  let mockAuthService: jest.Mocked<AuthService>;
  let mockStore: MockStore;

  beforeEach(async () => {
    jest.spyOn(console, 'error').mockImplementation(jest.fn());

    mockLoginService = {
      login: jest.fn(),
    } as unknown as jest.Mocked<LoginService>;

    mockToastService = {
      showSuccess: jest.fn(),
      showError: jest.fn(),
    } as unknown as jest.Mocked<ToastService>;

    mockAuthService = {
      setToken: jest.fn(),
    } as unknown as jest.Mocked<AuthService>;

    await TestBed.configureTestingModule({
      imports: [LoginComponent, ReactiveFormsModule],
      providers: [
        provideMockStore(),
        { provide: LoginService, useValue: mockLoginService },
        { provide: ToastService, useValue: mockToastService },
        { provide: AuthService, useValue: mockAuthService },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({}),
          },
        },
      ],
    }).compileComponents();

    mockStore = TestBed.inject(MockStore);
    jest.spyOn(mockStore, 'dispatch');

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

  it('should call loginService.login() when form is submitted', () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockLoginService.login.mockReturnValue(
      of({ access_token: 'token', token_type: 'bearer' })
    );
    component.onSubmit();
    expect(mockLoginService.login).toHaveBeenCalledWith(loginRequest);
  });

  it('should dispatch loginSuccess action on successful login', () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockLoginService.login.mockReturnValue(
      of({ access_token: 'token', token_type: 'bearer' })
    );

    component.onSubmit();

    expect(mockStore.dispatch).toHaveBeenCalledWith(
      authActions.loginSuccess({ token: 'token' })
    );
    expect(mockStore.dispatch).toHaveBeenCalledWith(
      authActions.hideLoginModal()
    );
    expect(mockAuthService.setToken).toHaveBeenCalledWith('token');
    expect(mockToastService.showSuccess).toHaveBeenCalledWith(
      'Login successful'
    );
  });

  it('should handle login error', () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockLoginService.login.mockReturnValue(
      throwError(() => ({ status: 401}))
    );

    component.onSubmit();

    expect(mockStore.dispatch).toHaveBeenCalledWith(
      authActions.loginFailure({ error: 'Invalid username or password.' })
    );
    expect(mockToastService.showError).toHaveBeenCalledWith('Invalid username or password.');
  });

  it('should reset form after successful login', () => {
    const loginRequest = { username: 'username', password: 'password' };
    component.loginForm.patchValue(loginRequest);
    mockLoginService.login.mockReturnValue(
      of({ access_token: 'token', token_type: 'bearer' })
    );

    component.onSubmit();

    expect(component.loginForm.get('username')?.value).toBe('');
    expect(component.loginForm.get('password')?.value).toBe('');
  });

  it('should emit closeModal event when register link is clicked', () => {
    jest.spyOn(component.closeModal, 'emit');

    component.onRegisterLinkClick();

    expect(mockStore.dispatch).toHaveBeenCalledWith(authActions.hideLoginModal());
  });
});
