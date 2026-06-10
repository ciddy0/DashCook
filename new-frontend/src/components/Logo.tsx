import { SouschatLogoIcon } from "./SouschatLogoIcon";

export function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <div className="logo" onClick={onClick}>
      <SouschatLogoIcon className="logo-mark" />
      <span>souschat</span>
    </div>
  );
}
