import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { ReactiveFormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';

import { RegistrationComponent } from './registration.component';
import { RegistrationService } from './registration.service';
import { ToastService } from '../toast/toast.service';
import { AuthService } from '../../services/auth/auth.service';
import { authActions } from '../../state/auth/auth.actions';

describe('RegistrationComponent', () => {
  let component: RegistrationComponent;
  let fixture: ComponentFixture<RegistrationComponent>;
  let registrationService: jest.Mocked<RegistrationService>;
  let router: jest.Mocked<Router>;
  let toastService: jest.Mocked<ToastService>;
  let store: jest.Mocked<Store>;
  let authService: jest.Mocked<AuthService>;

  beforeEach(async () => {
    const registrationServiceMock = {
      register: jest.fn(),
    };
    const routerMock = {
      navigate: jest.fn(),
    };
    const toastServiceMock = {
      showSuccess: jest.fn(),
      showError: jest.fn(),
    };
    const storeMock = {
      dispatch: jest.fn(),
    };
    const authServiceMock = {
      setToken: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [RegistrationComponent, ReactiveFormsModule],
      providers: [
        { provide: RegistrationService, useValue: registrationServiceMock },
        { provide: Router, useValue: routerMock },
        { provide: ToastService, useValue: toastServiceMock },
        { provide: Store, useValue: storeMock },
        { provide: AuthService, useValue: authServiceMock },
      ],
    }).compileComponents();

    registrationService = TestBed.inject(
      RegistrationService
    ) as jest.Mocked<RegistrationService>;
    router = TestBed.inject(Router) as jest.Mocked<Router>;
    toastService = TestBed.inject(ToastService) as jest.Mocked<ToastService>;
    store = TestBed.inject(Store) as jest.Mocked<Store>;
    authService = TestBed.inject(AuthService) as jest.Mocked<AuthService>;

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

  it('should handle successful registration when form is valid', () => {
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

    registrationService.register.mockReturnValue(
      of({ access_token: 'fake-token', token_type: 'bearer' })
    );

    component.onSubmit();

    expect(registrationService.register).toHaveBeenCalledWith(expectedRequest);
    expect(store.dispatch).toHaveBeenCalledWith(
      authActions.registerSuccess({ token: 'fake-token' })
    );
    expect(authService.setToken).toHaveBeenCalledWith('fake-token');
    expect(router.navigate).toHaveBeenCalledWith(['/']);
    expect(toastService.showSuccess).toHaveBeenCalledWith(
      'Registration successful'
    );
  });

  it('should handle registration error', () => {
    const registrationRequest = {
      username: 'testuser',
      firstName: 'Test',
      lastName: 'User',
      email: 'test@example.com',
      password: 'password123',
      confirmPassword: 'password123',
    };
    component.registration.patchValue(registrationRequest);

    registrationService.register.mockReturnValue(
      throwError(() => ({ status: 403 }))
    );

    component.onSubmit();

    expect(store.dispatch).toHaveBeenCalledWith(
      authActions.registerFailure({ error: 'Username already exists.' })
    );
    expect(toastService.showError).toHaveBeenCalledWith(
      'Username already exists.'
    );
  });
});
