export default function OfflinePage() {
  return (
    <div className="min-h-[calc(100dvh-56px)] bg-anchor-light flex flex-col items-center justify-center px-6 text-center">
      <svg
        className="w-16 h-16 text-anchor-dark/30 mb-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
        />
      </svg>
      <h1 className="text-xl font-bold text-anchor-navy mb-2">You&apos;re offline</h1>
      <p className="text-sm text-anchor-dark/70 max-w-xs leading-relaxed mb-8">
        Check your connection and try again. Anchorpoint needs a network connection to search your knowledge base.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="bg-anchor-blue text-white rounded-lg px-8 py-3 text-sm font-medium hover:bg-anchor-navy transition-colors min-h-[48px] touch-manipulation"
      >
        Try again
      </button>
    </div>
  );
}
