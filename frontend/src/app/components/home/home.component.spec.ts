import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HomeComponent } from './home.component';
import { AuthStore } from '../../services/auth/auth.store';
import { By } from '@angular/platform-browser';

const mockAuthStore = {
  isAuthenticated: jest.fn().mockReturnValue(false),
  showLoginModal: jest.fn(),
};

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomeComponent],
      providers: [{ provide: AuthStore, useValue: mockAuthStore }],
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display the proper verbiage and content', () => {
    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('h1').textContent).toContain(
      'Outsmart the Odds'
    );
    expect(compiled.querySelector('button').textContent).toContain(
      'Login or Register Now!'
    );
  });

  it('should call authStore.showLoginModal when login button is clicked', () => {
    const loginButton = fixture.debugElement.query(By.css('.btn-primary'));

    loginButton.nativeElement.click();

    expect(mockAuthStore.showLoginModal).toHaveBeenCalledTimes(1);
  });

  it('should call showRegistration method when button is clicked', () => {
    const showRegistrationSpy = jest.spyOn(component, 'showRegistration');

    const button = fixture.nativeElement.querySelector('button');
    button.click();

    expect(showRegistrationSpy).toHaveBeenCalled();
    expect(mockAuthStore.showLoginModal).toHaveBeenCalled();
  });

  it('should disable registration button if user already authenticated', () => {
    mockAuthStore.isAuthenticated.mockReturnValue(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button.disabled).toBe(true);
  });
});
