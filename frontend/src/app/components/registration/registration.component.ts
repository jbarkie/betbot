import { Component, inject } from '@angular/core';
import {
  ReactiveFormsModule,
  FormGroup,
  Validators,
  FormControl,
  ValidatorFn,
  AbstractControl,
  ValidationErrors,
} from '@angular/forms';

import { RegisterRequest } from '../models';
import { Router } from '@angular/router';
import { ToastService } from '../toast/toast.service';
import { AuthStore } from '../../services/auth/auth.store';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <h3 class="font-bold text-lg mt-2 mb-2 text-center">
      Register for an account
    </h3>
    <form
      [formGroup]="registration"
      class="mx-auto w-96"
      (ngSubmit)="onSubmit()"
      >
      <div class="form-control">
        <label class="label" for="register-username">
          <span class="label-text">Username</span>
        </label>
        <input
          id="register-username"
          name="username"
          type="text"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          formControlName="username"
          placeholder="Username"
          class="input input-bordered w-full"
          required
          />
        @if (isInvalid(username)) {
          <div>
            @if (username?.hasError('required')) {
              <p class="text-error mt-1">
                Username is required.
              </p>
            }
          </div>
        }
      </div>
      <div class="form-control mt-2">
        <label class="label" for="register-first-name">
          <span class="label-text">First Name</span>
        </label>
        <input
          id="register-first-name"
          name="firstName"
          type="text"
          autocomplete="given-name"
          formControlName="firstName"
          placeholder="Johnny"
          class="input input-bordered w-full mt-2"
          required
          />
        @if (isInvalid(firstName)) {
          <div>
            @if (firstName?.hasError('required')) {
              <p class="text-error mt-1">
                First name is required.
              </p>
            }
          </div>
        }
      </div>
      <div class="form-control mt-2">
        <label class="label" for="register-last-name">
          <span class="label-text">Last Name</span>
        </label>
        <input
          id="register-last-name"
          name="lastName"
          type="text"
          autocomplete="family-name"
          formControlName="lastName"
          placeholder="Appleseed"
          class="input input-bordered w-full mt-2"
          required
          />
        @if (isInvalid(lastName)) {
          <div>
            @if (lastName?.hasError('required')) {
              <p class="text-error mt-1">
                Last name is required.
              </p>
            }
          </div>
        }
      </div>
      <div class="form-control mt-2">
        <label class="label" for="register-email">
          <span class="label-text">Email</span>
        </label>
        <input
          id="register-email"
          name="email"
          type="email"
          autocomplete="email"
          formControlName="email"
          placeholder="Email"
          class="input input-bordered w-full mt-2"
          required
          />
        @if (isInvalid(email)) {
          <div>
            @if (email?.hasError('required')) {
              <p class="text-error mt-1">
                Email is required.
              </p>
            }
            @if (email?.hasError('email')) {
              <p class="text-error mt-1">
                Please enter a valid email address.
              </p>
            }
          </div>
        }
      </div>
      <div class="form-control mt-2">
        <label class="label" for="register-password">
          <span class="label-text">Password</span>
        </label>
        <input
          id="register-password"
          name="password"
          type="password"
          autocomplete="new-password"
          formControlName="password"
          placeholder="Password"
          class="input input-bordered w-full mt-2"
          required
          />
        @if (isInvalid(password)) {
          <div>
            @if (password?.hasError('required')) {
              <p class="text-error mt-1">
                Password is required.
              </p>
            }
            @if (password?.hasError('minlength')) {
              <p class="text-error mt-1">
                Password must be at least 8 characters.
              </p>
            }
          </div>
        }
      </div>
      <div class="form-control mt-2">
        <label class="label" for="register-confirm-password">
          <span class="label-text">Confirm Password</span>
        </label>
        <input
          id="register-confirm-password"
          name="confirmPassword"
          type="password"
          autocomplete="new-password"
          formControlName="confirmPassword"
          placeholder="Confirm Password"
          class="input input-bordered w-full mt-2"
          required
          />
        @if (isInvalid(confirmPassword)) {
          <div>
            @if (confirmPassword?.hasError('required')) {
              <p
                class="text-error mt-1"
                >
                Password confirmation is required.
              </p>
            }
            @if (confirmPassword?.hasError('minlength')) {
              <p
                class="text-error mt-1"
                >
                Password must be at least 8 characters.
              </p>
            }
            @if (confirmPassword?.hasError('passwordMismatch')) {
              <p
                class="text-error mt-1"
                >
                Passwords must match.
              </p>
            }
          </div>
        }
      </div>
      <button
        type="submit"
        class="btn btn-primary mt-6 float-right"
        [disabled]="registration.invalid"
        >
        Register
      </button>
    </form>
    `,
  styles: ``,
})
export class RegistrationComponent {
  registration!: FormGroup;

  private router = inject(Router);
  private toastService = inject(ToastService);
  private authStore = inject(AuthStore);

  ngOnInit() {
    this.registration = new FormGroup(
      {
        username: new FormControl('', [Validators.required]),
        firstName: new FormControl('', [Validators.required]),
        lastName: new FormControl('', [Validators.required]),
        email: new FormControl('', [Validators.required, Validators.email]),
        password: new FormControl('', [
          Validators.required,
          Validators.minLength(8),
        ]),
        confirmPassword: new FormControl(''),
      },
      { validators: this.passwordMatchValidator() }
    );
  }

  isInvalid(control: AbstractControl | null) {
    return control?.invalid && (control?.touched || control?.dirty);
  }

  get username() {
    return this.registration.get('username');
  }

  get firstName() {
    return this.registration.get('firstName');
  }

  get lastName() {
    return this.registration.get('lastName');
  }

  get email() {
    return this.registration.get('email');
  }

  get password() {
    return this.registration.get('password');
  }

  get confirmPassword() {
    return this.registration.get('confirmPassword');
  }

  passwordMatchValidator(): ValidatorFn {
    return (formGroup: AbstractControl): ValidationErrors | null => {
      const password = formGroup.get('password');
      const confirmPassword = formGroup.get('confirmPassword');

      if (!confirmPassword?.value) {
        confirmPassword?.setErrors({ required: true });
        return { confirmPasswordRequired: true };
      }

      if (confirmPassword?.value.length < 8) {
        confirmPassword?.setErrors({ minlength: true });
        return { confirmPasswordMinLength: true };
      }

      if (
        password &&
        confirmPassword &&
        password.value !== confirmPassword.value
      ) {
        confirmPassword.setErrors({ passwordMismatch: true });
        return { passwordMismatch: true };
      }

      confirmPassword?.setErrors(null);
      return null;
    };
  }

  async onSubmit() {
    if (this.registration.valid) {
      try {
        const request: RegisterRequest = {
          username: this.username?.value,
          first_name: this.firstName?.value,
          last_name: this.lastName?.value,
          email: this.email?.value,
          password: this.password?.value,
        };

        await this.authStore.register(request);
        this.router.navigate(['/']);
        this.toastService.showSuccess('Registration successful');
      } catch (error) {
        this.handleRegistrationError(error);
      }
    }
  }

  private handleRegistrationError(error: any) {
    console.error('Registration failed', error);
    let errorMessage = 'Registration failed. Please try again.';
    if (error.status === 403) {
      errorMessage = 'Username already exists.';
    }
    this.toastService.showError(errorMessage);
  }
}
