import { Pipe, PipeTransform } from '@angular/core';

/** Game times from the API are Eastern wall-clock times: `YYYY-MM-DD HH:mm[:ss]`. */
const GAME_TIME_PATTERN = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?$/;

// The browser's time zone database knows when Eastern Time switches between
// EST and EDT, including any future rule changes, so the pipe does not
// encode DST rules itself.
const easternOffsetFormat = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  timeZoneName: 'longOffset',
});

@Pipe({
  name: 'gameTime',
  standalone: true,
})
export class GameTimePipe implements PipeTransform {
  transform(value: string): string {
    if (!value) {
      return '';
    }

    const match = GAME_TIME_PATTERN.exec(value);
    if (!match) {
      return value;
    }

    const [year, month, day, hour, minute] = match.slice(1, 6).map(Number);
    const second = Number(match[6] ?? 0);

    // The wall-clock fields read as if they were UTC. Out-of-range fields
    // (month 13, hour 25) roll over, so reject anything that changed.
    const wallClockAsUtc = Date.UTC(year, month - 1, day, hour, minute, second);
    const check = new Date(wallClockAsUtc);
    if (
      check.getUTCFullYear() !== year ||
      check.getUTCMonth() !== month - 1 ||
      check.getUTCDate() !== day ||
      check.getUTCHours() !== hour ||
      check.getUTCMinutes() !== minute ||
      check.getUTCSeconds() !== second
    ) {
      return value;
    }

    // Shift by Eastern's offset, then re-read the offset at the shifted
    // instant so times within hours of a DST switch use the right one.
    const firstGuess = wallClockAsUtc - easternOffsetMs(wallClockAsUtc);
    const instant = wallClockAsUtc - easternOffsetMs(firstGuess);

    // Format to show time in the user's local time zone
    return new Date(instant).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  }
}

/** Eastern Time's UTC offset in milliseconds at the given instant (e.g. -4h during EDT). */
function easternOffsetMs(epochMs: number): number {
  const zoneName =
    easternOffsetFormat
      .formatToParts(epochMs)
      .find((part) => part.type === 'timeZoneName')?.value ?? '';
  // "GMT-04:00"; a zero offset is written as plain "GMT"
  const offset = /GMT([+-])(\d{2}):(\d{2})/.exec(zoneName);
  if (!offset) {
    return 0;
  }
  const sign = offset[1] === '-' ? -1 : 1;
  return sign * (Number(offset[2]) * 60 + Number(offset[3])) * 60_000;
}
