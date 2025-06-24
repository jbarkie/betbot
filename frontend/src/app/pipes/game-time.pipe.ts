import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'gameTime',
  standalone: true,
})
export class GameTimePipe implements PipeTransform {
  transform(value: string): string {
    if (!value) {
      return '';
    }

    try {
      const [dateStr, timeStr] = value.split(' ');
      const [year, month, day] = dateStr.split('-').map(Number);

      // Create a date object in Eastern timezone
      const tempDate = new Date(year, month - 1, day); // month is 0-indexed

      // Determine if Eastern Time is in DST on this date
      const isDST = this.isEasternDST(tempDate);
      const offset = isDST ? '-04:00' : '-05:00'; // EST vs EDT

      // Create the ISO string with proper timezone offset
      const easternTimeString = `${dateStr}T${timeStr}${offset}`;
      const date = new Date(easternTimeString);

      // Check if the date is valid
      if (isNaN(date.getTime())) {
        return value; // Return original value if parsing fails
      }

      // Format to show time in user's local timezone
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    } catch (error) {
      console.error('Error formatting game time:', error);
      return value; // Return original value on error
    }
  }

  private isEasternDST(date: Date): boolean {
    const year = date.getFullYear();

    // DST starts on the second Sunday in March
    const marchSecondSunday = this.getNthSundayOfMonth(year, 2, 2); // March = 2

    // DST ends on the first Sunday in November
    const novemberFirstSunday = this.getNthSundayOfMonth(year, 10, 1); // November = 10

    return date >= marchSecondSunday && date < novemberFirstSunday;
  }

  private getNthSundayOfMonth(year: number, month: number, n: number): Date {
    const firstDay = new Date(year, month, 1);
    const firstSunday = new Date(
      year,
      month,
      1 + ((7 - firstDay.getDay()) % 7)
    );
    return new Date(year, month, firstSunday.getDate() + (n - 1) * 7);
  }
}
