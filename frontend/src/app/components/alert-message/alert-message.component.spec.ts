import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';

import { AlertMessageComponent } from './alert-message.component';

describe('AlertMessageComponent', () => {
  let component: AlertMessageComponent;
  let fixture: ComponentFixture<AlertMessageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlertMessageComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(AlertMessageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have empty message by default', () => {
    expect(component.message).toBe('');
  })

  it('should have correct alert role', () => {
    const div = fixture.nativeElement.querySelector('div');
    expect(div).toBeTruthy();
    expect(div.getAttribute('role')).toBe('alert');
    expect(div.classList.contains('alert')).toBe(true);
  });

  it('should have correct CSS classes', () => {
    const alertElement = fixture.debugElement.query(By.css('.alert'));
    expect(alertElement).toBeTruthy();
  })

  it('should contain an SVG element', () => {
    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg).toBeTruthy();
  });

  it('should display input message', () => {
    component.message = 'This is an alert message';
    fixture.detectChanges();
    const span = fixture.nativeElement.querySelector('span');
    expect(span.textContent).toBe('This is an alert message');
  });
});
