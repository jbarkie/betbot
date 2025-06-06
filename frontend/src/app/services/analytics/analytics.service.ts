import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AnalyticsRequest, AnalyticsResponse } from '../../components/models';
import { Observable } from 'rxjs';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class AnalyticsService {
  private analyticsUrl = environment.apiUrl + '/analytics';

  constructor(private httpClient: HttpClient) {}

  analyze(
    request: AnalyticsRequest,
    sport: string
  ): Observable<AnalyticsRequest> {
    const analyticsUrlForGame = `${
      this.analyticsUrl
    }/${sport.toLowerCase()}/game?id=${request.gameId}`;
    return this.httpClient.get<AnalyticsRequest>(analyticsUrlForGame);
  }
}
