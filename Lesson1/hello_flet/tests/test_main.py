"""Smoke tests for the procedural pelican scene (no Flutter host needed)."""

import main


def test_scene_contains_pelican_and_bicycle():
    faces = main.build_scene(0.0)
    colors = {color for _, color in faces}

    assert len(faces) > 100
    assert main.WHITE in colors  # plumage
    assert main.ORANGE in colors  # beak, pouch and legs
    assert main.FRAME in colors  # bicycle frame
    assert main.RUBBER in colors  # tyres


def test_animation_changes_pedal_and_camera_pose():
    first = main.frame_shapes(0.0)
    later = main.frame_shapes(1.7)

    assert len(first) == len(later)
    assert [shape.paint.color for shape in first] != [shape.paint.color for shape in later]
