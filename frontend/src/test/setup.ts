import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

afterEach(() => {
  cleanup();
});

// Type declaration for jest-dom matchers
declare module 'vitest' {
  interface Assertion<T = any> extends jest.Matchers<void, T> {
    toBeInTheDocument(): T;
    toHaveAttribute(attr: string, value?: string): T;
  }
}
