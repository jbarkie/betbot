import { Injectable, signal, type WritableSignal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  private themeSignal: WritableSignal<'light' | 'dark'> = signal(
    this.getInitialTheme()
  );

  constructor() {
    this.setTheme(this.themeSignal());
  }

  private getInitialTheme(): 'light' | 'dark' {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || savedTheme === 'light') {
      return savedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }

  get theme() {
    return this.themeSignal.asReadonly();
  }

  setTheme(theme: 'light' | 'dark') {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    this.themeSignal.set(theme);
  }

  toggleTheme() {
    const newTheme = this.themeSignal() === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }
}
