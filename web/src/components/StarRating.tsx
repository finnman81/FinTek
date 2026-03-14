'use client';

import { useState } from 'react';

type Props = {
  value?: number;
  onChange: (rating: number) => void;
  disabled?: boolean;
  error?: boolean;
};

function StarIcon({ filled, half }: { filled: boolean; half?: boolean }) {
  if (half) {
    return (
      <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <linearGradient id="half">
            <stop offset="50%" stopColor="currentColor" />
            <stop offset="50%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path
          fill="url(#half)"
          stroke="currentColor"
          strokeWidth={1.5}
          d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z"
        />
      </svg>
    );
  }
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth={1.5}
        d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z"
      />
    </svg>
  );
}

const LABELS = ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'];

export default function StarRating({ value, onChange, disabled, error }: Props) {
  const [hover, setHover] = useState<number | null>(null);

  if (value != null) {
    return (
      <div className="flex items-center gap-1" role="status" aria-label={`Rated ${value} out of 5`}>
        <div className="flex text-amber-400">
          {[1, 2, 3, 4, 5].map((n) => (
            <StarIcon key={n} filled={n <= value} />
          ))}
        </div>
        <span className="ml-1 text-xs text-anchor-green">{value}/5 · Saved</span>
      </div>
    );
  }

  const display = hover ?? 0;

  return (
    <div className="flex items-center gap-1">
      <div
        className="flex"
        role="radiogroup"
        aria-label="Rate this response"
        onMouseLeave={() => setHover(null)}
      >
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={false}
            aria-label={`${n} star${n > 1 ? 's' : ''} — ${LABELS[n - 1]}`}
            onClick={() => onChange(n)}
            onMouseEnter={() => setHover(n)}
            onFocus={() => setHover(n)}
            onBlur={() => setHover(null)}
            disabled={disabled}
            className={`p-0.5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan/50 focus-visible:rounded disabled:opacity-40 ${
              n <= display ? 'text-amber-400' : 'text-gray-300'
            } hover:text-amber-400`}
          >
            <StarIcon filled={n <= display} />
          </button>
        ))}
      </div>
      {hover && (
        <span className="text-xs text-anchor-dark/50 ml-1 tabular-nums">{LABELS[hover - 1]}</span>
      )}
      {error && <span className="text-xs text-red-500 ml-1">Failed — retry</span>}
    </div>
  );
}
