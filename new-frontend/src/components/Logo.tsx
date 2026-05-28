export function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <div className="logo" onClick={onClick}>
      <span className="logo-mark">
        <span>c</span>
      </span>
      <span>souschat</span>
    </div>
  );
}
