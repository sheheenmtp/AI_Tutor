export default function LoadingSpinner({ message = "Loading..." }) {
  return (
    <div className="loading-wrap" role="status" aria-live="polite">
      <div className="loading-card">
        <div className="spinner" aria-hidden="true" />
        <p>{message}</p>
      </div>
    </div>
  );
}
