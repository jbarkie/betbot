import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-2">Login</h3>
      <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" >
        <div class="form-control">
          <label class="label">
            <span class="label-text">Username</span>
          </label>
          <input
          type="text"
          formControlName="username"
          placeholder="Username"
          class="input input-bordered w-full"
          />
          <div *ngIf="isValid('username')" class="text-error mt-1" >
            <div *ngIf="isRequired('username')">Username is required.</div>
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
            />
            <div *ngIf="isValid('password')" class="text-error mt-1" >
              <div *ngIf="isRequired('password')">Password is required.</div>
            </div>
          </div>
          <div class="modal-action">
            <button type="submit" class="btn btn-primary" [disabled]="loginForm.invalid">Login</button>
            <label for="login-modal" class="btn">Cancel</label>
          </div>
        </div>
      </form>
    </div>
  `,
  styles: ``,
})
export class LoginComponent {
  loginForm: FormGroup;

  constructor(private formBuilder: FormBuilder) {
    this.loginForm = this.formBuilder.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });
  }

  onSubmit() {
    if (this.loginForm.valid) {
      console.log('Form submitted');
    }
  }

  isValid(controlName: string) {
    return this.loginForm.get(controlName)?.invalid && (this.loginForm.get(controlName)?.dirty || this.loginForm.get(controlName)?.touched);
  }

  isRequired(controlName: string) {
    return this.loginForm.get(controlName)?.errors?.['required'];
  }
}
