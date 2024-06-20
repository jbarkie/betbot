import { Component } from '@angular/core';

@Component({
  selector: 'app-registration',
  standalone: true,
  imports: [],
  template: `
    <h3 class="font-bold text-lg mb-2 text-center">Register for an account</h3>
    <form class="mx-auto w-96">
      <div class="form-control">
        <label class="label">
          <span class="label-text">Username</span>
        </label>
        <input
          type="text"
          placeholder="Username"
          class="input input-bordered w-full"
        />
      </div>
      <div class="form-control mt-2">
        <label class="label">
          <span class="label-text">Password</span>
        </label>
        <input
          type="password"
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
          placeholder="Confirm Password"
          class="input input-bordered w-full mt-2"
        />
      </div>
      <div class="form-control mt-2">
        <label class="label">
          <span class="label-text">Email</span>
        </label>
        <input
          type="email"
          placeholder="Email"
          class="input input-bordered w-full mt-2"
        />
      </div>
  `,
  styles: ``
})
export class RegistrationComponent {

}
