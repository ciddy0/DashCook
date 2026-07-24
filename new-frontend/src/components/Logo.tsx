import { SouschatLogoIcon } from "./SouschatLogoIcon";
import { onActivateKey } from "../utils";

export function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <div
      className="logo"
      onClick={onClick}
      {...(onClick && {
        role: "button",
        tabIndex: 0,
        "aria-label": "Go to home",
        onKeyDown: onActivateKey(onClick),
      })}
    >
      <SouschatLogoIcon className="logo-mark" />
      <span>souschat</span>
    </div>
  );
}
