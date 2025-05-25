import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';
import { SettingsRequest } from '../models';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private settingsUrl = environment.apiUrl + '/settings';

  constructor(private httpClient: HttpClient) {}

  getSettings(): Observable<SettingsRequest> {
    return this.httpClient.get<SettingsRequest>(this.settingsUrl);
  }

  updateSettings(request: SettingsRequest): Observable<void> {
    return this.httpClient.post<void>(this.settingsUrl, request);
  }
}
