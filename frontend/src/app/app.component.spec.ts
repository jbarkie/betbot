import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MockStore } from '@ngrx/store/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { AppComponent } from './app.component';
import { PageHeaderComponent } from './components/page-header/page-header.component';
import { ToastComponent } from './components/toast/toast.component';
import { appActions } from './state/actions';
import { authActions } from './state/auth/auth.actions';

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let store: MockStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent, PageHeaderComponent, ToastComponent, HttpClientTestingModule],
      providers: [provideMockStore(),
        { provide: ActivatedRoute, useValue: {
          params: of({})
        }}
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
    jest.spyOn(store, 'dispatch');

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it(`should have the 'BetBot' title`, () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('BetBot');
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

  it('should dispatch applicationStarted action on init', () => {
    expect(store.dispatch).toHaveBeenCalledWith(appActions.applicationStarted());
  });

  it('should dispatch initializeAuth action on init', () => {
    expect(store.dispatch).toHaveBeenCalledWith(authActions.initializeAuth());
  });
});
