import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { ActivatedRoute } from '@angular/router';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';

import { NavBarComponent } from './nav-bar.component';
import { authActions } from '../../state/auth/auth.actions';
import { AuthService } from '../../services/auth/auth.service';

describe('NavBarComponent', () => {
  let component: NavBarComponent;
  let fixture: ComponentFixture<NavBarComponent>;
  let store: MockStore;
  let authService: jest.Mocked<AuthService>;

  beforeEach(async () => {
    const authServiceMock = {
      removeToken: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [NavBarComponent, HttpClientTestingModule],
      providers: [
        provideMockStore({
          initialState: {
            auth: {
              isAuthenticated: false,
              showLoginModal: false,
            },
          },
        }),
        {
          provide: ActivatedRoute,
          useValue: {
            params: of({}),
          },
        },
        {
          provide: AuthService,
          useValue: authServiceMock,
        },
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    authService = TestBed.inject(AuthService) as jest.Mocked<AuthService>;
    fixture = TestBed.createComponent(NavBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show login option when not authenticated', () => {
    store.setState({
      auth: { isAuthenticated: false, showLoginModal: false },
    });
    fixture.detectChanges();
    const loginOption = fixture.debugElement.query(
      By.css('.dropdown-end > ul > li:nth-child(1)')
    );
    expect(loginOption.nativeElement.textContent).toContain('Login');
  });

  it('should show logout option when authenticated', () => {
    store.setState({
      auth: { isAuthenticated: true, showLoginModal: false },
    });
    fixture.detectChanges();
    const logoutOption = fixture.debugElement.query(
      By.css('.dropdown-end > ul > li:nth-child(1)')
    );
    expect(logoutOption.nativeElement.textContent).toContain('Logout');
  });

  it('should dispatch showLoginModal action when login option is clicked', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.openLoginModal();
    expect(dispatchSpy).toHaveBeenCalledWith(authActions.showLoginModal());
  });

  it('should dispatch hideLoginModal action when closing login modal', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.closeLoginModal();
    expect(dispatchSpy).toHaveBeenCalledWith(authActions.hideLoginModal());
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
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.logout();
    expect(dispatchSpy).toHaveBeenCalledWith(authActions.logout());
    expect(authService.removeToken).toHaveBeenCalled();
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

  it('should update login modal visibility based on store state', () => {
    store.setState({
      auth: { isAuthenticated: false, showLoginModal: true },
    });
    fixture.detectChanges();
    const modalToggle = fixture.debugElement.query(By.css('input[type="checkbox"]')); 
    expect(modalToggle.nativeElement.checked).toBe(true);

    store.setState({
      auth: { isAuthenticated: false, showLoginModal: false },
    });
    fixture.detectChanges();
    expect(modalToggle.nativeElement.checked).toBe(false);
  });
});
