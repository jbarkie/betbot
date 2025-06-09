import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { SettingsService } from './settings.service';
import { environment } from '../../../environments/environment';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { SettingsRequest } from '../models';

describe('SettingsService', () => {
  let service: SettingsService;
  let httpMock: HttpTestingController;
  const apiUrl = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        SettingsService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(SettingsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getSettings', () => {
    it('should make a GET request with the correct URL for settings', () => {
      const expectedUrl = `${apiUrl}/settings`;

      service.getSettings().subscribe();

      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('GET');
    });
  });

  describe('updateSettings', () => {
    it('should make a POST request with the correct URL for settings', () => {
      const expectedUrl = `${apiUrl}/settings`;
      const mockRequest: SettingsRequest = {
        username: 'testuser',
        email: 'test@test.com',
        email_notifications_enabled: true,
      };

      service.updateSettings(mockRequest).subscribe();

      const req = httpMock.expectOne(expectedUrl);
      expect(req.request.method).toBe('POST');
    });
  });
});
