import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-nba',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './nba.component.html',
  styleUrl: './nba.component.css'
})
export class NbaComponent {
  today: Date = new Date();
}
