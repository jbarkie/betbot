module.exports = {
    preset: 'jest-preset-angular',
    setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
    testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/dist/'],
    transform: {
      '^.+\\.(ts|js|mjs|html|svg)$': [
        'jest-preset-angular',
        {
          tsconfig: '<rootDir>/tsconfig.spec.json',
          stringifyContentPathRegex: '\\.html$',
        },
      ],
    },
    moduleNameMapper: {
      '@app/(.*)': '<rootDir>/src/app/$1',
      '@assets/(.*)': '<rootDir>/src/assets/$1',
      '@environments/(.*)': '<rootDir>/src/environments/$1',
    },
  };