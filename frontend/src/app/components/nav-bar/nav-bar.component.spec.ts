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
  isLoginModalDisplayed: jest.fn().mockReturnValue(false),
  shouldShowLoginModal: signal(false),
  showLoginModal: signal(false),
  logout: jest.fn(),
  hideLoginModal: jest.fn(),
}

describe('NavBarComponent', () => {
  let component: NavBarComponent;
  let fixture: ComponentFixture<NavBarComponent>;

  beforeEach(async () => {
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

  it('should set showLoginModal true when login option is clicked', () => {
    component.openLoginModal();
    expect(mockAuthStore.showLoginModal).toBeTruthy();
  });

  it('should call hideLoginModal  when closing login modal', () => {
    component.closeLoginModal();
    expect(mockAuthStore.hideLoginModal).toHaveBeenCalled();
  });

  it('should toggle login modal based on checkbox state', () => {
    const openSpy = jest.spyOn(component, 'openLoginModal');
    const closeSpy = jest.spyOn(component, 'closeLoginModal');

    const event = { target: { checked: true } } as any;
    component.toggleLoginModal(event);
    expect(openSpy).toHaveBeenCalled();

    event.target.checked = false;
    component.toggleLoginModal(event);
    expect(closeSpy).toHaveBeenCalled();
  });

  it('should dispatch logout action and remove token when logging out', () => {
    component.logout();
    expect(mockAuthStore.logout).toHaveBeenCalled();
  });

  it('should have correct navigation links', () => {
    const links = fixture.debugElement.queryAll(By.css('a[routerLink]'));
    expect(links.length).toBe(8);
    expect(links[0].nativeElement.getAttribute('routerLink')).toBe('/');
    expect(links[1].nativeElement.getAttribute('routerLink')).toBe('/nba');
    expect(links[2].nativeElement.getAttribute('routerLink')).toBe('/mlb');
    expect(links[3].nativeElement.getAttribute('routerLink')).toBe('/nfl');
    expect(links[4].nativeElement.getAttribute('routerLink')).toBe('/nhl');
    expect(links[5].nativeElement.getAttribute('routerLink')).toBe('/about');
  });

  it('should update login modal visibility based on auth store state', () => {
    mockAuthStore.isLoginModalDisplayed.mockReturnValue(true);
    fixture.detectChanges();
    const modalToggle = fixture.debugElement.query(
      By.css('input[type="checkbox"]')
    );
    expect(modalToggle.nativeElement.checked).toBe(true);

    mockAuthStore.isLoginModalDisplayed.mockReturnValue(false);
    fixture.detectChanges();
    expect(modalToggle.nativeElement.checked).toBe(false);
  });
});
