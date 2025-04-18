import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';

import { SettingsComponent } from './settings.component';
import { ThemeToggleComponent } from './theme-toggle/theme-toggle.component';

describe('SettingsComponent', () => {
  let component: SettingsComponent;
  let fixture: ComponentFixture<SettingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsComponent, FormsModule, ThemeToggleComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with empty form values', () => {
    expect(component.email).toBe('');
    expect(component.username).toBe('');
    expect(component.password).toBe('');
    expect(component.emailNotifications).toBe(false);
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

    // Initial state should be false
    expect(component.emailNotifications).toBe(false);

    // Click the toggle
    toggleInput.nativeElement.click();
    fixture.detectChanges();

    expect(component.emailNotifications).toBe(true);
  });

  it('should include ThemeToggleComponent', () => {
    const themeToggle = fixture.debugElement.query(By.css('app-theme-toggle'));
    expect(themeToggle).toBeTruthy();
  });

  it('should call saveSettings when save button is clicked', () => {
    const saveSpy = jest.spyOn(component, 'saveSettings');
    const saveButton = fixture.debugElement.query(By.css('.btn-primary'));

    saveButton.nativeElement.click();
    fixture.detectChanges();

    expect(saveSpy).toHaveBeenCalled();
  });

  it('should log settings when save button is clicked', () => {
    const consoleSpy = jest.spyOn(console, 'log');
    const saveButton = fixture.debugElement.query(By.css('.btn-primary'));

    // Set up test values
    component.email = 'test@example.com';
    component.username = 'testuser';
    component.password = 'password123';
    component.emailNotifications = true;
    fixture.detectChanges();

    saveButton.nativeElement.click();

    expect(consoleSpy).toHaveBeenCalledWith('Saving settings...');
  });
});
