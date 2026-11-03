import { useEffect, useRef } from "react";

/** Reveal below-the-fold sections once per view during this app session. */
export default function useScrollReveal(view: string, ready: boolean) {
  const contentRef = useRef<HTMLDivElement>(null);
  const seen = useRef(new Set<string>());

  useEffect(() => {
    const root = contentRef.current;
    if (!root || !ready || !("IntersectionObserver" in window)) return;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const keys = new Map<Element, string>();
    const reveal = (element: Element) => {
      const key = keys.get(element);
      if (key) seen.current.add(key);
      element.classList.remove("reveal-pending");
      observer.unobserve(element);
    };
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) reveal(entry.target);
        });
      },
      { threshold: 0, rootMargin: "0px 0px -24px 0px" },
    );
    const register = () => {
      root
        .querySelectorAll(".panel, .stats-grid, footer")
        .forEach((element, index) => {
          if (keys.has(element)) return;
          const key = `${view}:${index}`;
          keys.set(element, key);
          // Keep the initial viewport immediately readable.
          if (
            motion.matches ||
            seen.current.has(key) ||
            element.getBoundingClientRect().top < window.innerHeight
          ) {
            reveal(element);
            return;
          }
          element.classList.add("scroll-reveal", "reveal-pending");
          observer.observe(element);
        });
    };
    const onFocus = (event: FocusEvent) => {
      if (event.target instanceof Element) {
        const panel = event.target.closest(".reveal-pending");
        if (panel) reveal(panel);
      }
    };
    const onMotionChange = () => {
      if (motion.matches) keys.forEach((_, element) => reveal(element));
    };
    register();
    // Some views load their panels independently of the dashboard data.
    const mutations = new MutationObserver(register);
    mutations.observe(root, { childList: true, subtree: true });
    root.addEventListener("focusin", onFocus);
    motion.addEventListener("change", onMotionChange);
    return () => {
      observer.disconnect();
      mutations.disconnect();
      root.removeEventListener("focusin", onFocus);
      motion.removeEventListener("change", onMotionChange);
      keys.forEach((_, element) => element.classList.remove("reveal-pending"));
    };
  }, [view, ready]);

  return contentRef;
}
