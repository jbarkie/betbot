import { Component } from '@angular/core';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [],
  template: `
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-2">Login</h3>
      <form>
        <input
          type="text"
          placeholder="Username"
          class="input input-bordered w-full"
        />
        <input
          type="password"
          placeholder="Password"
          class="input input-bordered w-full mt-2"
        />
        <div class="modal-action">
          <button type="submit" class="btn btn-primary">Login</button>
          <label for="login-modal" class="btn">Cancel</label>
        </div>
      </form>
    </div>
  `,
  styles: ``,
})
export class LoginComponent {}
