import { useEffect, useRef, type ReactNode } from "react";

import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";
import styles from "./ParallaxLayer.module.css";

interface ParallaxLayerProps {
  /** Fraction of scroll distance the layer lags behind the page. */
  speed?: number;
  className?: string;
  children?: ReactNode;
}

/**
 * Moves a decorative background layer as it scrolls through the viewport.
 *
 * Listens for scroll only while the layer is on screen, writes the transform
 * inside a single animation frame, and does nothing at all when the visitor
 * has asked for reduced motion. Foreground text is never wrapped in this.
 */
export default function ParallaxLayer({
  speed = 0.12,
  className,
  children,
}: ParallaxLayerProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const node = ref.current;
    if (!node) {
      return;
    }

    if (prefersReducedMotion) {
      node.style.transform = "";
      return;
    }

    let frame = 0;

    const paint = () => {
      frame = 0;
      const rect = node.getBoundingClientRect();
      const offset = rect.top + rect.height / 2 - window.innerHeight / 2;
      node.style.transform = `translate3d(0, ${(-offset * speed).toFixed(2)}px, 0)`;
    };

    const schedule = () => {
      if (frame === 0) {
        frame = window.requestAnimationFrame(paint);
      }
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          window.addEventListener("scroll", schedule, { passive: true });
          window.addEventListener("resize", schedule);
          schedule();
        } else {
          window.removeEventListener("scroll", schedule);
          window.removeEventListener("resize", schedule);
        }
      },
      { rootMargin: "20% 0px" },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame !== 0) {
        window.cancelAnimationFrame(frame);
      }
      node.style.transform = "";
    };
  }, [prefersReducedMotion, speed]);

  return (
    <div
      ref={ref}
      aria-hidden="true"
      className={className ? `${styles.layer} ${className}` : styles.layer}
    >
      {children}
    </div>
  );
}
