/** A microgravity flame: round and ball-like, orange body, hot core, blue rim on the upwind side. */
export function Flame({ size = 28 }: { size?: number }) {
  return (
    <svg className="flame" width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <defs>
        <radialGradient id="fl-body" cx="60%" cy="46%" r="64%">
          <stop offset="0" stopColor="#fff1a8" /><stop offset=".36" stopColor="#ffc247" /><stop offset=".74" stopColor="#f2711c" /><stop offset="1" stopColor="#b8360f" />
        </radialGradient>
        <linearGradient id="fl-rim" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#59b8ff" /><stop offset="1" stopColor="#59b8ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <g className="fl-sway">
        <ellipse className="fl-halo" cx="17" cy="17" rx="13" ry="13.5" fill="#ff8a1f" opacity=".22" />
        <path d="M18 3 C25.5 6.6 29 13.2 27.6 19.4 C26.2 25.6 20.9 29.2 15.2 28.4 C8.5 27.4 4 22.2 5 15.8 C6 9.4 11.4 4.2 18 3 Z" fill="url(#fl-body)" />
        <path d="M18 3 C11.4 4.2 6 9.4 5 15.8 C4.6 18.8 5.4 21.5 7 23.6 C6.5 18.6 8.4 11.2 14.2 7 C15.6 6 16.8 4.8 18 3 Z" fill="url(#fl-rim)" />
        <ellipse className="fl-core" cx="17.2" cy="19" rx="5.4" ry="6.6" fill="#fff7cf" opacity=".88" />
      </g>
    </svg>
  );
}
