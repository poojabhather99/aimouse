import pytest

from aimouse.gestures import (
    Config,
    camera_to_screen,
    classify,
    distance,
    fingers_up,
    pinch_to_volume_percent,
    smooth,
)


def make_hand(raised=(0, 0, 0, 0, 0)):
    """Build 21 landmarks; a raised finger has its tip above (smaller y than) its PIP joint."""
    lm = [[i, 100, 200] for i in range(21)]
    tips = (4, 8, 12, 16, 20)
    for finger, tip in enumerate(tips):
        if finger == 0:  # thumb compares x of tip vs the joint before it
            lm[tip][1] = 150 if raised[0] else 50
        else:
            lm[tip][2] = 100 if raised[finger] else 300
    return lm


@pytest.mark.parametrize("state", [(0, 0, 0, 0, 0), (1, 1, 1, 1, 1), (0, 1, 0, 0, 0), (0, 1, 1, 0, 0)])
def test_fingers_up_round_trip(state):
    assert fingers_up(make_hand(state)) == list(state)


@pytest.mark.parametrize(
    "state,mode",
    [
        ([0, 1, 0, 0, 0], "move"),
        ([1, 1, 0, 0, 0], "move_pinch_volume"),
        ([0, 1, 1, 0, 0], "click"),
        ([1, 0, 0, 0, 0], "scroll_up"),
        ([0, 0, 0, 0, 1], "scroll_down"),
        ([0, 0, 0, 0, 0], "idle"),
    ],
)
def test_classify(state, mode):
    assert classify(state) == mode


def test_distance():
    lm = [[0, 0, 0], [1, 3, 4]]
    assert distance(lm, 0, 1) == 5.0


def test_camera_to_screen_corners_and_clamping():
    cfg = Config()
    assert camera_to_screen(cfg.frame_margin, cfg.frame_margin, cfg, (1920, 1080)) == (0.0, 0.0)
    far = camera_to_screen(cfg.cam_width, cfg.cam_height, cfg, (1920, 1080))
    assert far == (1920.0, 1080.0)  # values beyond the margin are clamped to the screen


def test_smooth_moves_a_fraction_toward_target():
    assert smooth((0.0, 0.0), (70.0, 14.0), 7.0) == (10.0, 2.0)
    assert smooth((5.0, 5.0), (5.0, 5.0), 7.0) == (5.0, 5.0)


def test_pinch_to_volume_percent_bounds():
    cfg = Config()
    assert pinch_to_volume_percent(0, cfg) == 0
    assert pinch_to_volume_percent(10_000, cfg) == 100
    assert pinch_to_volume_percent(125, cfg) == pytest.approx(50.0)
