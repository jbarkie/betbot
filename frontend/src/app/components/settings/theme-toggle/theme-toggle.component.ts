import { Component, inject } from '@angular/core';

import { ThemeService } from '../../../services/theme/theme.service';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [],
  template: `
    <div class="form-control">
      <label class="label cursor-pointer">
        <span class="label-text">Dark Mode</span>
        <input
          type="checkbox"
          class="toggle"
          [checked]="themeService.theme() === 'dark'"
          (change)="themeService.toggleTheme()"
        />
      </label>
    </div>
  `,
  styles: ``,
})
export class ThemeToggleComponent {
  protected themeService = inject(ThemeService);
}
