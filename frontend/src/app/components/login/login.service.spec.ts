import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { LoginService } from './login.service';
import { LoginRequest, LoginResponse } from '../models';
import { environment } from '../../../environments/environment';
import { provideHttpClient, withFetch } from '@angular/common/http';

describe('LoginService', () => {
  let service: LoginService;
  let httpMock: HttpTestingController;
  const apiUrl = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        LoginService,
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(LoginService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should send a POST request with correct parameters', () => {
      // Arrange
      const loginRequest: LoginRequest = {
        username: 'testuser',
        password: 'password123',
      };

      const mockResponse: LoginResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
      };

      // Act
      service.login(loginRequest).subscribe((response) => {
        // Assert
        expect(response).toEqual(mockResponse);
      });

      // Assert HTTP request
      const req = httpMock.expectOne(`${apiUrl}/login`);
      expect(req.request.method).toBe('POST');
      expect(req.request.headers.get('Content-Type')).toBe(
        'application/x-www-form-urlencoded'
      );
      expect(req.request.body).toBe('username=testuser&password=password123');

      // Respond with mock data
      req.flush(mockResponse);
    });

    it('should handle login failure properly', () => {
      // Arrange
      const loginRequest: LoginRequest = {
        username: 'testuser',
        password: 'wrongpassword',
      };

      const errorResponse = {
        status: 401,
        statusText: 'Unauthorized',
      };

      // Act
      let actualError: any;
      service.login(loginRequest).subscribe({
        next: () => fail('Should have failed with 401 error'),
        error: (error) => {
          actualError = error;
        },
      });

      // Assert HTTP request
      const req = httpMock.expectOne(`${apiUrl}/login`);
      expect(req.request.method).toBe('POST');

      // Respond with mock error
      req.flush('Invalid credentials', errorResponse);

      // Error should be handled
      expect(actualError.status).toBe(401);
    });
  });
});
