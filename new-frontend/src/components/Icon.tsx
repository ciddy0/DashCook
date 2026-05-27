import {
  ClockIcon,
  UsersIcon,
  FireIcon,
  BookmarkSimpleIcon,
  PrinterIcon,
  PlayIcon,
  PauseIcon,
  CaretLeftIcon,
  CaretRightIcon,
  XIcon,
  LinkIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  SparkleIcon,
  TimerIcon,
  CatIcon,
  PaletteIcon,
} from "@phosphor-icons/react";

const icons = {
  clock: ClockIcon,
  users: UsersIcon,
  fire: FireIcon,
  bookmark: BookmarkSimpleIcon,
  "bookmark-fill": BookmarkSimpleIcon,
  print: PrinterIcon,
  play: PlayIcon,
  pause: PauseIcon,
  "arrow-l": CaretLeftIcon,
  "arrow-r": CaretRightIcon,
  x: XIcon,
  link: LinkIcon,
  search: MagnifyingGlassIcon,
  check: CheckIcon,
  sparkle: SparkleIcon,
  timer: TimerIcon,
  cat: CatIcon,
  palette: PaletteIcon,
} as const;

const fillIcons = new Set(["bookmark-fill", "play", "pause"]);

export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const Component = icons[name as keyof typeof icons];
  if (!Component) return null;
  return <Component size={size} weight={fillIcons.has(name) ? "fill" : "regular"} />;
}
