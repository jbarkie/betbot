import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { RegistrationService } from './registration.service';
import { RegisterRequest, RegisterResponse } from '../models';
import { environment } from '../../../environments/environment';
import { provideHttpClient, withFetch } from '@angular/common/http';

describe('RegistrationService', () => {
  let service: RegistrationService;
  let httpMock: HttpTestingController;
  const apiUrl = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        RegistrationService,
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(RegistrationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('register', () => {
    it('should send a POST request with correct parameters', () => {
      // Arrange
      const registerRequest: RegisterRequest = {
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        email: 'test@example.com',
        password: 'password123',
      };

      const mockResponse: RegisterResponse = {
        access_token: 'test-register-token',
        token_type: 'bearer',
      };

      // Act
      service.register(registerRequest).subscribe((response) => {
        // Assert
        expect(response).toEqual(mockResponse);
      });

      // Assert HTTP request
      const req = httpMock.expectOne(`${apiUrl}/register`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(registerRequest);

      // Respond with mock data
      req.flush(mockResponse);
    });

    it('should handle registration failure properly', () => {
      // Arrange
      const registerRequest: RegisterRequest = {
        username: 'existinguser',
        first_name: 'Existing',
        last_name: 'User',
        email: 'existing@example.com',
        password: 'password123',
      };

      const errorResponse = {
        status: 400,
        statusText: 'Bad Request',
      };

      // Act
      let actualError: any;
      service.register(registerRequest).subscribe({
        next: () => fail('Should have failed with 400 error'),
        error: (error) => {
          actualError = error;
        },
      });

      // Assert HTTP request
      const req = httpMock.expectOne(`${apiUrl}/register`);
      expect(req.request.method).toBe('POST');

      // Respond with mock error
      req.flush('Username already exists', errorResponse);

      // Error should be handled
      expect(actualError.status).toBe(400);
    });
  });
});
