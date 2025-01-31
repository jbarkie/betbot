import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { AppComponent } from './app.component';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { ToastComponent } from './components/toast/toast.component';
import { provideHttpClient } from '@angular/common/http';
import { AuthStore } from './services/auth/auth.store';
import { signal } from '@angular/core';

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let mockAuthStore: jest.Mocked<typeof AuthStore.prototype>;

  beforeEach(async () => {
    mockAuthStore = {
      initializeAuth: jest.fn().mockResolvedValue(undefined),
      logout: jest.fn(),
      hideLoginModal: jest.fn(),
      isAuthenticated: signal(false),
      showLoginModal: signal(false),
      token: signal(null),
      error: signal(null),
      hasError: signal(false),
    } as unknown as jest.Mocked<typeof AuthStore.prototype>;

    await TestBed.configureTestingModule({
      imports: [AppComponent, PageHeaderComponent, ToastComponent],
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

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app', () => {
    expect(component).toBeTruthy();
  });

  it(`should have the 'BetBot' title`, () => {
    expect(component.title).toEqual('BetBot');
  });

  it('should render the page header', () => {
    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('app-page-header')).toBeTruthy();
  });

  it('should render the toast component', () => {
    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('app-toast')).toBeTruthy();
  });

  it('should render the router outlet', () => {
    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('router-outlet')).toBeTruthy();
  });

  it('should call initializeAuth on construction', () => {
    expect(mockAuthStore['initializeAuth']).toHaveBeenCalled();
  });
});
