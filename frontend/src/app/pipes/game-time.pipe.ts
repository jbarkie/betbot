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
      // Parse the datetime string
      const date = new Date(value);

      // Check if the date is valid
      if (isNaN(date.getTime())) {
        return value; // Return original value if parsing fails
      }

      // Format to show time in 12-hour format
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
}
