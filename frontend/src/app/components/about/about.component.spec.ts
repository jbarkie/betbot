import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AboutComponent } from './about.component';

describe('AboutComponent', () => {
  let component: AboutComponent;
  let fixture: ComponentFixture<AboutComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AboutComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AboutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should contain proper headings', () => {
    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('h1').textContent).toEqual('About BetBot');

    const h2Elements = compiled.querySelectorAll('h2');
    expect(h2Elements[0].textContent).toEqual('Our Mission');
    expect(h2Elements[1].textContent).toEqual('Features');
    expect(h2Elements[2].textContent).toEqual('Supported Sports');
  });
});
