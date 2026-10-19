"""Run with: python -m aimouse"""
from __future__ import annotations

import argparse
import time

import cv2

from aimouse.controller import MouseController, VolumeController
from aimouse.gestures import (
    INDEX_TIP,
    MIDDLE_TIP,
    THUMB_TIP,
    Config,
    camera_to_screen,
    classify,
    distance,
    fingers_up,
    pinch_to_volume_percent,
    smooth,
)
from aimouse.hand_tracker import HandDetector


def run(camera: int, cfg: Config) -> None:
    cap = cv2.VideoCapture(camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.cam_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.cam_height)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {camera}")

    detector = HandDetector(max_hands=1)
    mouse, volume = MouseController(), VolumeController()
    prev = (0.0, 0.0)
    prev_time = time.time()

    try:
        while True:
            ok, img = cap.read()
            if not ok:
                break
            img = detector.find_hands(img)
            lm, _ = detector.find_position(img)

            if lm:
                mode = classify(fingers_up(lm))
                cv2.rectangle(img, (cfg.frame_margin,) * 2,
                              (cfg.cam_width - cfg.frame_margin, cfg.cam_height - cfg.frame_margin),
                              (255, 0, 255), 2)

                if mode.startswith("move"):
                    target = camera_to_screen(lm[INDEX_TIP][1], lm[INDEX_TIP][2], cfg, mouse.screen)
                    prev = smooth(prev, target, cfg.smoothing)
                    # camera image is mirrored, so flip x
                    mouse.move(mouse.screen[0] - prev[0], prev[1])
                if mode == "move_pinch_volume":
                    pct = pinch_to_volume_percent(distance(lm, THUMB_TIP, INDEX_TIP), cfg)
                    volume.set_percent(pct)
                    cv2.putText(img, f"{int(pct)}%", (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9,
                                (209, 206, 0), 3)
                if mode == "click" and distance(lm, INDEX_TIP, MIDDLE_TIP) < cfg.click_distance:
                    mouse.click()
                if mode == "scroll_up":
                    mouse.scroll(cfg.scroll_amount)
                if mode == "scroll_down":
                    mouse.scroll(-cfg.scroll_amount)

            now = time.time()
            fps = 1 / max(now - prev_time, 1e-6)
            prev_time = now
            cv2.putText(img, str(int(fps)), (28, 58), cv2.FONT_HERSHEY_PLAIN, 3, (255, 8, 8), 3)
            cv2.imshow("aimouse (press q to quit)", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Control the mouse with hand gestures.")
    parser.add_argument("--camera", type=int, default=0, help="camera index (default 0)")
    parser.add_argument("--smoothing", type=float, default=Config.smoothing)
    args = parser.parse_args()
    run(args.camera, Config(smoothing=args.smoothing))


if __name__ == "__main__":
    main()
