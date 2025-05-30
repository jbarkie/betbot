import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { createSportsStore } from './sports.store';
import { environment } from '../../../environments/environment';
import { Signal } from '@angular/core';
import { Game } from '../../components/models';
import { DatePipe } from '@angular/common';
import { provideHttpClient } from '@angular/common/http';

describe('SportsStore', () => {
  const TestStore = createSportsStore('TEST');
  let store: {
    games: Signal<Game[]>;
    isLoading: Signal<boolean>;
    error: Signal<string | null>;
    loadGames: (date: Date) => void;
    clearError: () => void;
  };
  let httpMock: HttpTestingController;
  let datePipe: DatePipe;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        TestStore,
        DatePipe,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    store = TestBed.inject(TestStore);
    httpMock = TestBed.inject(HttpTestingController);
    datePipe = TestBed.inject(DatePipe);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create store', () => {
    expect(store).toBeTruthy();
  });

  it('should load games', () => {
    const testDate = new Date('2024-01-01T12:00:00Z');
    const mockGames = { list: [{ id: '1', sport: 'TEST' } as Game] };
    const formattedDate = datePipe.transform(testDate, 'yyyy-MM-dd');

    store.loadGames(testDate);

    const req = httpMock.expectOne(
      `${environment.apiUrl}/test/games?date=${formattedDate}`
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockGames);

    expect(store.games()).toEqual(mockGames.list);
    expect(store.isLoading()).toBeFalsy();
    expect(store.error()).toBeNull();
  });

  it('should handle errors', () => {
    const testDate = new Date('2024-01-01T12:00:00Z');
    const errorMessage = 'Test error';
    const formattedDate = datePipe.transform(testDate, 'yyyy-MM-dd');

    store.loadGames(testDate);

    const req = httpMock.expectOne(
      `${environment.apiUrl}/test/games?date=${formattedDate}`
    );
    req.error(new ErrorEvent('error'), { statusText: errorMessage });

    expect(store.games()).toEqual([]);
    expect(store.isLoading()).toBeFalsy();
    expect(store.error()).toContain(errorMessage);
  });

  it('should clear error', () => {
    store.clearError();
    expect(store.error()).toBeNull();
  });
});
