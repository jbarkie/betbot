import { GameTimePipe } from './game-time.pipe';

describe('GameTimePipe', () => {
  let pipe: GameTimePipe;

  beforeEach(() => {
    pipe = new GameTimePipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should format a valid datetime string to 12-hour format (DST period)', () => {
    // June 21st should be in DST (EDT = UTC-4)
    const testTime = '2025-06-21 19:30:00';
    const result = pipe.transform(testTime);
    expect(result).toMatch(/\d{1}:\d{2}\s?PM/);
  });

  it('should format a valid datetime string to 12-hour format (Standard time period)', () => {
    // January 15th should be in standard time (EST = UTC-5)
    const testTime = '2025-01-15 19:30:00';
    const result = pipe.transform(testTime);
    // Create expected result based on the actual Eastern time conversion
    const expectedDate = new Date('2025-01-15T19:30:00-05:00');
    const expectedTime = expectedDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
    expect(result).toBe(expectedTime);
  });

  it('should handle morning times correctly', () => {
    const testTime = '2025-06-21 09:15:00';
    const result = pipe.transform(testTime);
    // Create expected result based on the actual Eastern time conversion
    const expectedDate = new Date('2025-06-21T09:15:00-04:00'); // DST
    const expectedTime = expectedDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
    expect(result).toBe(expectedTime);
  });

  it('should handle evening times correctly', () => {
    const testTime = '2025-06-21 21:45:00';
    const result = pipe.transform(testTime);
    // Create expected result based on the actual Eastern time conversion
    const expectedDate = new Date('2025-06-21T21:45:00-04:00'); // DST
    const expectedTime = expectedDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
    expect(result).toBe(expectedTime);
  });

  it('should handle invalid datetime strings gracefully', () => {
    const invalidTime = 'invalid-date';
    const result = pipe.transform(invalidTime);
    expect(result).toBe(invalidTime);
  });

  it('should handle malformed datetime strings gracefully', () => {
    const malformedTime = '2025-13-45 25:70:80'; // Invalid month, day, hour, minute, second
    const result = pipe.transform(malformedTime);
    expect(result).toBe(malformedTime);
  });

  it('should handle ISO format strings gracefully (wrong format)', () => {
    // The pipe expects space-separated format, not T-separated
    const isoTime = '2025-06-21T19:30:00';
    const result = pipe.transform(isoTime);
    expect(result).toBe(isoTime); // Should return original value
  });

  it('should handle empty string', () => {
    const result = pipe.transform('');
    expect(result).toBe('');
  });

  it('should handle null or undefined', () => {
    const result = pipe.transform(null as any);
    expect(result).toBe('');
  });

  it('should correctly determine DST vs Standard time', () => {
    // Test a known DST date (June)
    const dstTime = '2025-06-15 15:00:00';
    const dstResult = pipe.transform(dstTime);
    const expectedDstResult = new Date('2025-06-15T15:00:00-04:00').toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
    expect(dstResult).toBe(expectedDstResult);

    // Test a known Standard time date (December)
    const stdTime = '2025-12-15 15:00:00';
    const stdResult = pipe.transform(stdTime);
    const expectedStdResult = new Date('2025-12-15T15:00:00-05:00').toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
    expect(stdResult).toBe(expectedStdResult);
  });
});
