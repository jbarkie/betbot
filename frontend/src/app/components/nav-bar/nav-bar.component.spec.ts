import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { AuthStore } from '../../services/auth/auth.store';
import { LoginComponent } from '../login/login.component';
import { NavBarComponent } from './nav-bar.component';

const mockAuthStore = {
  isAuthenticated: signal(false),
  isLoginModalDisplayed: signal(false),
  shouldShowLoginModal: signal(false),
  showLoginModal: jest.fn(),
  logout: jest.fn(),
  hideLoginModal: jest.fn(),
};

describe('NavBarComponent', () => {
  let component: NavBarComponent;
  let fixture: ComponentFixture<NavBarComponent>;

  beforeEach(async () => {
    jest.clearAllMocks();
    mockAuthStore.isAuthenticated.set(false);
    mockAuthStore.isLoginModalDisplayed.set(false);

    await TestBed.configureTestingModule({
      imports: [NavBarComponent, LoginComponent],
      providers: [
        { provide: AuthStore, useValue: mockAuthStore },
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({}),
          },
        },
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NavBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show login option when not authenticated', () => {
    mockAuthStore.isAuthenticated.set(false);
    fixture.detectChanges();
    const loginOption = fixture.debugElement.query(
      By.css('.dropdown-end > ul > li:nth-child(1)')
    );
    expect(loginOption.nativeElement.textContent).toContain('Login');
  });

  it('should show logout option when authenticated', () => {
    mockAuthStore.isAuthenticated.set(true);
    fixture.detectChanges();
    const logoutOption = fixture.debugElement.query(
      By.css('.dropdown-end > ul > li:nth-child(1)')
    );
    expect(logoutOption.nativeElement.textContent).toContain('Logout');
  });

  it('should call showLoginModal when the login option is clicked', () => {
    fixture.nativeElement.querySelector('[data-testid="open-login"]').click();
    expect(mockAuthStore.showLoginModal).toHaveBeenCalled();
  });

  it('should call hideLoginModal  when closing login modal', () => {
    component.closeLoginModal();
    expect(mockAuthStore.hideLoginModal).toHaveBeenCalled();
  });

  it('should dispatch logout action and remove token when logging out', () => {
    component.logout();
    expect(mockAuthStore.logout).toHaveBeenCalled();
  });

  it('should have correct navigation links in menu', () => {
    const links = fixture.debugElement.queryAll(By.css('.menu a[routerLink]'));
    const expectedLinks = [
      '/',
      '/nba',
      '/mlb',
      '/nfl',
      '/nhl',
      '/about',
      '/settings',
    ];
    expect(links.length).toBe(7);
    links.forEach((link, index) => {
      expect(link.nativeElement.getAttribute('routerLink')).toBe(
        expectedLinks[index]
      );
    });
  });

  it('should open and close the login dialog with auth store state', () => {
    const dialog: HTMLDialogElement = fixture.nativeElement.querySelector(
      '[data-testid="login-dialog"]'
    );
    expect(dialog.open).toBe(false);

    mockAuthStore.isLoginModalDisplayed.set(true);
    fixture.detectChanges();
    expect(dialog.open).toBe(true);

    mockAuthStore.isLoginModalDisplayed.set(false);
    fixture.detectChanges();
    expect(dialog.open).toBe(false);
  });

  it('should call hideLoginModal when the dialog closes itself (Escape or backdrop)', () => {
    mockAuthStore.isLoginModalDisplayed.set(true);
    fixture.detectChanges();
    const dialog: HTMLDialogElement = fixture.nativeElement.querySelector(
      '[data-testid="login-dialog"]'
    );

    dialog.close();

    expect(mockAuthStore.hideLoginModal).toHaveBeenCalled();
  });

  it('should close the login dialog when Cancel is clicked', () => {
    mockAuthStore.isLoginModalDisplayed.set(true);
    fixture.detectChanges();
    const dialog: HTMLDialogElement = fixture.nativeElement.querySelector(
      '[data-testid="login-dialog"]'
    );

    dialog.querySelector<HTMLButtonElement>('[data-testid="cancel-login"]')!.click();

    expect(dialog.open).toBe(false);
    expect(mockAuthStore.hideLoginModal).toHaveBeenCalled();
  });

  it('should clear the login form and its errors when the dialog closes', () => {
    mockAuthStore.isLoginModalDisplayed.set(true);
    fixture.detectChanges();
    const dialog: HTMLDialogElement = fixture.nativeElement.querySelector(
      '[data-testid="login-dialog"]'
    );
    const login = fixture.debugElement.query(By.directive(LoginComponent))
      .componentInstance as LoginComponent;
    login.loginForm.patchValue({ username: '', password: 'secret' });
    login.loginForm.markAllAsTouched();
    fixture.detectChanges();
    expect(dialog.textContent).toContain('Username is required.');

    dialog.close();
    fixture.detectChanges();

    expect(login.loginForm.get('password')?.value).toBeNull();
    expect(dialog.textContent).not.toContain('Username is required.');
  });

  it('should clear touched state left over from a previous open when reopening', () => {
    const login = fixture.debugElement.query(By.directive(LoginComponent))
      .componentInstance as LoginComponent;
    // Reopening moves focus, which can blur a field left focused last time
    login.loginForm.markAllAsTouched();

    mockAuthStore.isLoginModalDisplayed.set(true);
    fixture.detectChanges();

    expect(login.loginForm.touched).toBe(false);
    expect(fixture.nativeElement.textContent).not.toContain('Username is required.');
  });

  it('should label the login dialog with its heading', () => {
    const dialog = fixture.nativeElement.querySelector('[data-testid="login-dialog"]');
    const labelId = dialog.getAttribute('aria-labelledby');
    expect(fixture.nativeElement.querySelector(`#${labelId}`).textContent).toContain('Login');
  });
});
