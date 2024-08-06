import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SportWrapperComponent } from './sport-wrapper.component';

describe('SportWrapperComponent', () => {
  let component: SportWrapperComponent;
  let fixture: ComponentFixture<SportWrapperComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SportWrapperComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SportWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
