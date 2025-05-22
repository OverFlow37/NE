import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../button';

// Jest의 describe, it 함수를 사용
describe('Button', () => {
  it('renders correctly with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-primary-600');
  });

  it('renders with different variants', () => {
    const { rerender } = render(<Button variant="outline">Outline Button</Button>);
    let button = screen.getByRole('button', { name: /outline button/i });
    expect(button).toHaveClass('border-primary-600');

    rerender(<Button variant="ghost">Ghost Button</Button>);
    button = screen.getByRole('button', { name: /ghost button/i });
    expect(button).toHaveClass('hover:bg-primary-50');

    rerender(<Button variant="link">Link Button</Button>);
    button = screen.getByRole('button', { name: /link button/i });
    expect(button).toHaveClass('text-primary-600');
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small Button</Button>);
    let button = screen.getByRole('button', { name: /small button/i });
    expect(button).toHaveClass('h-9');

    rerender(<Button size="lg">Large Button</Button>);
    button = screen.getByRole('button', { name: /large button/i });
    expect(button).toHaveClass('h-12');
  });

  it('passes additional props to the button element', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByRole('button', { name: /disabled button/i });
    expect(button).toBeDisabled();
  });
});
