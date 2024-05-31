import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, catchError, of } from "rxjs";
import { LoginRequest, LoginResponse } from "../models";
import { environment } from "../../../environments/environment";

@Injectable({
    providedIn: 'root'
})
export class LoginService {
    private loginUrl = environment.apiUrl + '/login';

    constructor(private http: HttpClient) { }

    login(request: LoginRequest): Observable<LoginResponse> {
        return this.http.post<LoginResponse>(this.loginUrl, request)
            .pipe(
                catchError(this.handleError<LoginResponse>('login'))
            );
    }

    private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      console.error(error);
      console.log(`${operation} failed: ${error.message}`);
      return of(result as T);
    };
  }
}