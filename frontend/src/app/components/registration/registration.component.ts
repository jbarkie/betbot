import { Component } from '@angular/core';
import { ReactiveFormsModule, FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [ReactiveFormsModule],
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
        />
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
        />
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
        />
      </div>
      <button type="submit" class="btn btn-primary mt-6 float-right" [disabled]="registration.invalid">
        Register
      </button>
  `,
  styles: ``
})
export class RegistrationComponent {
  registration: FormGroup;

  constructor(private formBuilder: FormBuilder) {
    this.registration = this.formBuilder.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
      confirmPassword: ['', Validators.required],
      email: ['', Validators.required]
    });
  }
}
