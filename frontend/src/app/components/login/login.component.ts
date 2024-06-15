import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { LoginRequest, LoginResponse } from '../models';
import { LoginService } from './login.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
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
          <p *ngIf="isInvalid('username')" class="text-error mt-1">Username is required.</p>
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
          <p *ngIf="isInvalid('password')" class="text-error mt-1" >Password is required.</p>
        </div>
        <div class="modal-action">
          <p>Need an account? <a (click)="onRegisterLinkClick()" routerLink="/register">Register here</a></p>
          <button type="submit" class="btn btn-primary" [disabled]="loginForm.invalid">Login</button>
          <label for="login-modal" class="btn">Cancel</label>
        </div>
      </form>
    </div>
  `,
  styles: ``,
})
export class LoginComponent {
  loginForm: FormGroup;
  @Output() closeModal = new EventEmitter<void>();

  constructor(private formBuilder: FormBuilder, private loginService: LoginService) {
    this.loginForm = this.formBuilder.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });
  }

  onSubmit() {
    if (this.loginForm.valid) {
      const request: LoginRequest = {
        username: this.loginForm.get('username')?.value,
        password: this.loginForm.get('password')?.value
      };

      this.loginService.login(request)
        .subscribe({
          next: (response: LoginResponse) => {
            localStorage.setItem('token', response.token);
            console.log('Login successful', response);
          },
          error: (error) => {
            console.error('Login failed', error);
          }    
        });
    }
  }

  isInvalid(controlName: string) {
    return this.loginForm.get(controlName)?.invalid && (this.loginForm.get(controlName)?.dirty || this.loginForm.get(controlName)?.touched);
  }

  onRegisterLinkClick() {
    this.closeModal.emit();
  }
}
