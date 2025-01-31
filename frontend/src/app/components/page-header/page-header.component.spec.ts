import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { By } from '@angular/platform-browser';

import { PageHeaderComponent } from './page-header.component';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AuthStore } from '../../services/auth/auth.store';
import { signal } from '@angular/core';

const mockAuthStore = {
  isAuthenticated: jest.fn(),
  showLoginModal: signal(false),
};

describe('PageHeaderComponent', () => {
  let component: PageHeaderComponent;
  let fixture: ComponentFixture<PageHeaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageHeaderComponent],
      providers: [
        provideMockStore({}),
        { provide: AuthStore, useValue: mockAuthStore },
        { provide: ActivatedRoute, useValue: { params: of({}) } },
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PageHeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a header element', () => {
    const header = fixture.debugElement.query(By.css('header'));
    expect(header).toBeTruthy();
  });

  it('should include the NavBarComponent', () => {
    const navBar = fixture.debugElement.query(By.css('app-nav-bar'));
    expect(navBar).toBeTruthy();
  });
});
