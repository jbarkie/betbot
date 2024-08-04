import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { RegisterRequest, RegisterResponse } from '../models';
import { catchError, Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class RegistrationService {
  private registrationUrl = environment.apiUrl + '/register';

  constructor(private httpClient: HttpClient) {}

  register(request: RegisterRequest): Observable<RegisterResponse> {
    return this.httpClient.post<RegisterResponse>(
      this.registrationUrl,
      request
    );
  }
}
