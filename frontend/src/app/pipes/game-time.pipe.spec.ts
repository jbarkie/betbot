import { GameTimePipe } from './game-time.pipe';

describe('GameTimePipe', () => {
  let pipe: GameTimePipe;

  beforeEach(() => {
    pipe = new GameTimePipe();
  });

  it('create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should format a valid datetime string to 12-hour format', () => {
    const testTime = '2025-06-21T19:30:00';
    const result = pipe.transform(testTime);
    expect(result).toMatch(/\d{1,2}:\d{2}\s?(AM|PM)/);
  });

  it('should handle invalid datetime strings gracefully', () => {
    const invalidTime = 'invalid-date';
    const result = pipe.transform(invalidTime);
    expect(result).toBe(invalidTime);
  });

  it('should handle empty string', () => {
    const result = pipe.transform('');
    expect(result).toBe('');
  });

  it('should handle null or undefined', () => {
    const result = pipe.transform(null as any);
    expect(result).toBe('');
  });
});
