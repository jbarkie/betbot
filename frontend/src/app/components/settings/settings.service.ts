import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';
import { SettingsRequest, SettingsResponse } from '../models';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private settingsUrl = environment.apiUrl + '/settings';

  constructor(private httpClient: HttpClient) {}

  getSettings(): Observable<SettingsResponse> {
    return this.httpClient.get<SettingsResponse>(this.settingsUrl);
  }

  updateSettings(request: SettingsRequest): Observable<SettingsResponse> {
    return this.httpClient.post<SettingsResponse>(this.settingsUrl, request);
  }
}
