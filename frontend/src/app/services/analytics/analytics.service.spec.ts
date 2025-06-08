import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import { AnalyticsRequest, AnalyticsResponse } from '../../components/models';
import { AnalyticsService } from './analytics.service';

describe('AnalyticsService', () => {
  let service: AnalyticsService;
  let httpMock: HttpTestingController;
  const apiUrl = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        AnalyticsService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    
    service = TestBed.inject(AnalyticsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('analyze', () => {
    it('should make a GET request with the correct URL for MLB', () => {
      const mockRequest: AnalyticsRequest = { gameId: '123' };
      const sport = 'MLB';
      const expectedUrl = `${apiUrl}/analytics/mlb/game?id=123`;
      
      service.analyze(mockRequest, sport).subscribe();
      
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
    });

    it('should make a GET request with the correct URL for NBA', () => {
      const mockRequest: AnalyticsRequest = { gameId: '456' };
      const sport = 'NBA';
      const expectedUrl = `${apiUrl}/analytics/nba/game?id=456`;
      
      service.analyze(mockRequest, sport).subscribe();
      
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
    });

    it('should convert sport to lowercase in the URL', () => {
      const mockRequest: AnalyticsRequest = { gameId: '789' };
      const sport = 'NFL';
      const expectedUrl = `${apiUrl}/analytics/nfl/game?id=789`;
      
      service.analyze(mockRequest, sport).subscribe();
      
      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
    });

    it('should return the expected data when the API responds', () => {
      const mockRequest: AnalyticsRequest = { gameId: '123' };
      const sport = 'MLB';
      const mockResponse: AnalyticsResponse = { gameId: '123' };
      
      let actualResponse: AnalyticsResponse | undefined;
      
      service.analyze(mockRequest, sport).subscribe(response => {
        actualResponse = response;
      });
      
      const req = httpMock.expectOne(`${apiUrl}/analytics/mlb/game?id=123`);
      req.flush(mockResponse);
      
      expect(actualResponse).toEqual(mockResponse);
    });

    it('should handle API errors appropriately', () => {
      const mockRequest: AnalyticsRequest = { gameId: '123' };
      const sport = 'MLB';
      const mockError = { status: 404, statusText: 'Not Found' };
      
      let actualError: any;
      
      service.analyze(mockRequest, sport).subscribe(
        () => {},
        error => {
          actualError = error;
        }
      );
      
      const req = httpMock.expectOne(`${apiUrl}/analytics/mlb/game?id=123`);
      req.flush('Not found', mockError);
      
      expect(actualError.status).toBe(404);
    });
  });
});