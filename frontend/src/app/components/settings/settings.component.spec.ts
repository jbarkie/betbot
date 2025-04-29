import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ReactiveFormsModule } from '@angular/forms';

import { SettingsComponent } from './settings.component';
import { ThemeToggleComponent } from './theme-toggle/theme-toggle.component';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

describe('SettingsComponent', () => {
  let component: SettingsComponent;
  let fixture: ComponentFixture<SettingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsComponent, ReactiveFormsModule, ThemeToggleComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty form values', () => {
    expect(component.settingsForm.get('email')?.value).toBe('');
    expect(component.settingsForm.get('username')?.value).toBe('');
    expect(component.settingsForm.get('password')?.value).toBe('');
    expect(component.settingsForm.get('emailNotifications')?.value).toBe(false);
  });

  it('should render account settings section', () => {
    const accountSection = fixture.debugElement.query(
      By.css('.card:first-child')
    );
    expect(accountSection).toBeTruthy();
    expect(
      accountSection.query(By.css('.card-title')).nativeElement.textContent
    ).toContain('Account Settings');
  });

  it('should render preferences section', () => {
    const preferencesSection = fixture.debugElement.query(
      By.css('.card:nth-child(2)')
    );
    expect(preferencesSection).toBeTruthy();
    expect(
      preferencesSection.query(By.css('.card-title')).nativeElement.textContent
    ).toContain('Preferences');
  });

  it('should toggle email notifications', () => {
    const toggleInput = fixture.debugElement.query(By.css('.toggle'));
    const emailNotificationsControl =
      component.settingsForm.get('emailNotifications');

    // Initial state should be false
    expect(emailNotificationsControl?.value).toBe(false);

    // Simulate toggle change
    emailNotificationsControl?.setValue(true);
    fixture.detectChanges();

    expect(emailNotificationsControl?.value).toBe(true);
  });

  it('should include ThemeToggleComponent', () => {
    const themeToggle = fixture.debugElement.query(By.css('app-theme-toggle'));
    expect(themeToggle).toBeTruthy();
  });
});
