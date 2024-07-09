import { Component } from '@angular/core';
import { ReactiveFormsModule, FormGroup, Validators, FormControl, ValidatorFn, AbstractControl, ValidationErrors } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  template: `
    <h3 class="font-bold text-lg mt-2 mb-2 text-center">Register for an account</h3>
    <form [formGroup]="registration" class="mx-auto w-96">
      <div class="form-control">
        <label class="label">
          <span class="label-text">Username</span>
        </label>
        <input
          type="text"
          formControlName="username"
          placeholder="Username"
          class="input input-bordered w-full"
          required
        />
        <div *ngIf="isInvalid(username)">
          <p *ngIf="username?.hasError('required')" class="text-error mt-1">Username is required.</p>
        </div>
      </div>
      <div class="form-control mt-2">
        <label class="label">
          <span class="label-text">Email</span>
        </label>
        <input
          type="email"
          formControlName="email"
          placeholder="Email"
          class="input input-bordered w-full mt-2"
          required
        />
        <div *ngIf="isInvalid(email)">
          <p *ngIf="email?.hasError('required')" class="text-error mt-1">Email is required.</p>
        </div>
      </div>
      <div class="form-control mt-2">
        <label class="label">
          <span class="label-text">Password</span>
        </label>
        <input
          type="password"
          formControlName="password"
          placeholder="Password"
          class="input input-bordered w-full mt-2"
          required
        />
        <div *ngIf="isInvalid(password)">
          <p *ngIf="password?.hasError('required')" class="text-error mt-1">Password is required.</p>
          <p *ngIf="password?.hasError('minlength')" class="text-error mt-1">Password must be at least 8 characters.</p>
        </div>
      </div>
      <div class="form-control mt-2">
        <label class="label">
          <span class="label-text">Confirm Password</span>
        </label>
        <input
          type="password"
          formControlName="confirmPassword"
          placeholder="Confirm Password"
          class="input input-bordered w-full mt-2"
          required
        />
        <div *ngIf="isInvalid(confirmPassword)">
          <p *ngIf="confirmPassword?.hasError('required')" class="text-error mt-1">Password confirmation is required.</p>
          <p *ngIf="confirmPassword?.hasError('minlength')" class="text-error mt-1">Password must be at least 8 characters.</p>
          <p *ngIf="confirmPassword?.hasError('passwordMismatch')" class="text-error mt-1">Passwords must match.</p>
        </div>
      </div>
      <button type="submit" class="btn btn-primary mt-6 float-right" [disabled]="registration.invalid">
        Register
      </button>
  `,
  styles: ``
})
export class RegistrationComponent {
  registration!: FormGroup;

  ngOnInit() {
    this.registration = new FormGroup({
      username: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required]),
      password: new FormControl('', [Validators.required, Validators.minLength(8)]),
      confirmPassword: new FormControl('')
    }, { validators: this.passwordMatchValidator() });
  } 

  isInvalid(control: AbstractControl | null) {
    return control?.invalid && (control?.touched || control?.dirty);
  }

  get username() {
    return this.registration.get('username');
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

      if (password && confirmPassword && password.value !== confirmPassword.value) {
        confirmPassword.setErrors({ passwordMismatch: true });
        return { passwordMismatch: true };
      }

      confirmPassword?.setErrors(null);
      return null;
    };
  }
}
