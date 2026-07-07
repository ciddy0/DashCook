import { useEffect } from "react";

const SOUND_URL = "/sounds/button_click.mp3";
const POOL_SIZE = 4;
const SELECTOR = "button, .btn, .icon-btn, .explore-shelf";

export function useClickSound() {
  useEffect(() => {
    const pool: HTMLAudioElement[] = [];
    let index = 0;

    for (let i = 0; i < POOL_SIZE; i++) {
      const a = new Audio(SOUND_URL);
      a.preload = "auto";
      a.load();
      pool.push(a);
    }

    function playSound() {
      const audio = pool[index % POOL_SIZE];
      index++;
      audio.currentTime = 0;
      audio.play().catch(() => {});
    }

    function handleMouseDown(e: MouseEvent) {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      if (target.closest(SELECTOR)) {
        playSound();
      }
    }

    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, []);

}
