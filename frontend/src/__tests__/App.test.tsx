import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    // App should render something - login page or secrets page
    expect(document.body).toBeTruthy();
  });
});
