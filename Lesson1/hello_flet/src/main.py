"""A low-poly pelican riding a bicycle, drawn with Flet Canvas.

Everything is generated from simple 3D primitives and projected by hand, so
there are no rendering dependencies beyond Flet itself.
"""

import asyncio
import math

import flet as ft
from flet.canvas import Canvas, Path
from flet.controls.painting import Paint, PaintingStyle

Vec = tuple[float, float, float]
Face = tuple[list[Vec], str]

WIDTH, HEIGHT = 900, 620
CX, CY = WIDTH / 2, HEIGHT - 100
CAMERA_DISTANCE = 9.0
FOCAL = 620.0
LIGHT = (0.35, 0.75, 0.56)

WHITE = "#F4F1E8"
SHADOW = "#D9D5C8"
ORANGE = "#F28C28"
POUCH = "#E8792B"
DARK = "#30343B"
FRAME = "#2E9CB8"
RUBBER = "#22242A"
SPOKE = "#AEB6BC"


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: Vec, s: float) -> Vec:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Vec) -> Vec:
    length = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / length)


def sphere(center: Vec, radii: Vec, color: str, nu: int, nv: int) -> list[Face]:
    faces: list[Face] = []
    rings = []
    for i in range(nv + 1):
        phi = math.pi * i / nv
        ring = []
        for j in range(nu):
            theta = 2 * math.pi * j / nu
            ring.append(
                add(
                    center,
                    (
                        radii[0] * math.sin(phi) * math.cos(theta),
                        radii[1] * math.cos(phi),
                        radii[2] * math.sin(phi) * math.sin(theta),
                    ),
                )
            )
        rings.append(ring)
    for i in range(nv):
        for j in range(nu):
            k = (j + 1) % nu
            faces.append(([rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]], color))
    return faces


def tube(a: Vec, b: Vec, radius: float, color: str, sides: int = 5) -> list[Face]:
    axis = norm(sub(b, a))
    helper = (0, 0, 1) if abs(axis[2]) < 0.9 else (0, 1, 0)
    u = norm(cross(axis, helper))
    v = cross(axis, u)
    ring_a, ring_b = [], []
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        offset = add(mul(u, radius * math.cos(angle)), mul(v, radius * math.sin(angle)))
        ring_a.append(add(a, offset))
        ring_b.append(add(b, offset))
    faces = []
    for i in range(sides):
        j = (i + 1) % sides
        faces.append(([ring_a[i], ring_a[j], ring_b[j], ring_b[i]], color))
    faces.append((list(reversed(ring_a)), color))
    faces.append((ring_b, color))
    return faces


def wheel(cx: float, cy: float, z: float, spin: float) -> list[Face]:
    """A rim with a hollow centre and rotating spokes."""
    faces: list[Face] = []
    outer, inner = 0.86, 0.72
    segments = 9
    front, back = z + 0.055, z - 0.055
    for i in range(segments):
        a1 = 2 * math.pi * i / segments
        a2 = 2 * math.pi * (i + 1) / segments

        def pt(radius: float, angle: float, depth: float) -> Vec:
            return (cx + radius * math.cos(angle), cy + radius * math.sin(angle), depth)

        of1, of2 = pt(outer, a1, front), pt(outer, a2, front)
        if1, if2 = pt(inner, a1, front), pt(inner, a2, front)
        ob1, ob2 = pt(outer, a1, back), pt(outer, a2, back)
        ib1, ib2 = pt(inner, a1, back), pt(inner, a2, back)
        faces.extend(
            [
                ([of1, of2, if2, if1], RUBBER),
                ([ib1, ib2, ob2, ob1], RUBBER),
                ([ob1, ob2, of2, of1], RUBBER),
                ([if1, if2, ib2, ib1], RUBBER),
            ]
        )
    for i in range(5):
        angle = spin + 2 * math.pi * i / 5
        tip = (cx + inner * math.cos(angle), cy + inner * math.sin(angle), front + 0.005)
        side_angle = angle + math.pi / 2
        offset = (0.018 * math.cos(side_angle), 0.018 * math.sin(side_angle), 0)
        faces.append(
            (
                [
                    (cx + offset[0], cy + offset[1], front + 0.005),
                    (cx - offset[0], cy - offset[1], front + 0.005),
                    tip,
                ],
                SPOKE,
            )
        )
    faces.extend(sphere((cx, cy, z), (0.11, 0.11, 0.14), DARK, 5, 3))
    return faces


def build_scene(t: float) -> list[Face]:
    spin = t * 3.2
    bob = 0.035 * math.sin(spin)
    scenes: list[Face] = []
    scenes.extend(wheel(-1.22, 0.86, -0.09, spin))
    scenes.extend(wheel(1.22, 0.86, 0.09, spin))

    rear = (-1.22, 0.86, 0)
    front = (1.22, 0.86, 0)
    crank = (0, 0.88, 0)
    saddle_base = (-0.48, 1.72, 0)
    head_bottom = (0.88, 1.26, 0)
    head_top = (0.72, 1.68, 0)
    for a, b in [
        (crank, saddle_base),
        (saddle_base, head_top),
        (head_top, head_bottom),
        (head_bottom, crank),
        (crank, rear),
        (saddle_base, rear),
        (head_bottom, front),
    ]:
        scenes.extend(tube(a, b, 0.055, FRAME))
    scenes.extend(tube((0.72, 1.68, -0.32), (0.72, 1.68, 0.32), 0.045, DARK))
    scenes.extend(tube((-0.66, 1.79, 0), (-0.28, 1.79, 0), 0.06, DARK))

    # Pelican: body, sweeping wings, S-curved neck, head, beak and pouch.
    body = (-0.42, 2.38 + bob, 0)
    scenes.extend(sphere(body, (0.88, 0.54, 0.5), WHITE, 9, 5))
    for side in (-1, 1):
        scenes.append(
            (
                [
                    (-0.55, 2.65 + bob, side * 0.45),
                    (-1.42, 2.5 + bob, side * 0.72),
                    (-1.15, 1.98 + bob, side * 0.55),
                    (-0.35, 2.06 + bob, side * 0.46),
                ],
                SHADOW if side < 0 else WHITE,
            )
        )
    neck_points = [
        (0.12, 2.62 + bob, 0),
        (0.45, 3.12 + bob, 0),
        (0.23, 3.48 + bob, 0),
        (0.66, 3.73 + bob, 0),
    ]
    for a, b in zip(neck_points, neck_points[1:]):
        scenes.extend(tube(a, b, 0.21, WHITE, 6))
    head = (0.86, 3.78 + bob, 0)
    scenes.extend(sphere(head, (0.33, 0.3, 0.29), WHITE, 7, 4))
    for side in (-1, 1):
        scenes.extend(sphere((0.98, 3.89 + bob, side * 0.24), (0.055, 0.055, 0.04), DARK, 4, 2))
    scenes.extend(tube((1.06, 3.72 + bob, 0), (1.98, 3.54 + bob, 0), 0.085, ORANGE, 5))
    scenes.extend(sphere((1.44, 3.38 + bob, 0), (0.42, 0.28, 0.24), POUCH, 7, 4))

    # Legs follow the rotating pedals.
    for side in (-1, 1):
        pedal = (
            crank[0] + 0.42 * math.cos(spin + (0 if side > 0 else math.pi)),
            crank[1] + 0.42 * math.sin(spin + (0 if side > 0 else math.pi)),
            side * 0.24,
        )
        hip = (-0.28 + side * 0.08, 2.02 + bob, side * 0.24)
        knee = ((hip[0] + pedal[0]) / 2 + 0.16, (hip[1] + pedal[1]) / 2 - 0.08, side * 0.26)
        scenes.extend(tube(hip, knee, 0.075, ORANGE, 4))
        scenes.extend(tube(knee, pedal, 0.065, ORANGE, 4))
        scenes.extend(sphere(pedal, (0.17, 0.06, 0.11), ORANGE, 5, 3))
    return scenes


def shade(color: str, brightness: float) -> str:
    r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(min(255, int(channel * brightness)) for channel in (r, g, b))


def frame_shapes(t: float) -> list[Path]:
    angle = 0.42 * math.sin(t * 0.42)
    ca, sa = math.cos(angle), math.sin(angle)
    tilt = -0.1
    ct, st = math.cos(tilt), math.sin(tilt)
    projected = []
    for vertices, color in build_scene(t):
        normal = norm(cross(sub(vertices[1], vertices[0]), sub(vertices[2], vertices[0])))
        brightness = 0.56 + 0.44 * max(0.0, dot(normal, LIGHT))
        points, depth_sum = [], 0.0
        for x, y, z in vertices:
            rx = x * ca + z * sa
            rz = -x * sa + z * ca
            ry = y * ct - rz * st
            dz = y * st + rz * ct
            scale = FOCAL / (CAMERA_DISTANCE - dz)
            points.append((CX + rx * scale, CY - ry * scale))
            depth_sum += dz
        projected.append((depth_sum / len(vertices), points, shade(color, brightness)))
    projected.sort(key=lambda item: item[0])
    return [
        Path(
            elements=[Path.MoveTo(*points[0])]
            + [Path.LineTo(*point) for point in points[1:]]
            + [Path.Close()],
            paint=Paint(color=color, style=PaintingStyle.FILL),
        )
        for _, points, color in projected
    ]


async def animate(page: ft.Page, canvas: Canvas) -> None:
    t = 0.0
    while True:
        try:
            canvas.shapes = frame_shapes(t)
            canvas.update()
        except Exception:
            return
        t += 0.1
        await asyncio.sleep(0.1)


def main(page: ft.Page) -> None:
    page.title = "Pelican on a Bicycle (3D)"
    page.padding = 0
    page.bgcolor = "#EAF4F7"
    canvas = Canvas(shapes=frame_shapes(0), width=WIDTH, height=HEIGHT)
    page.add(
        ft.Stack(
            [
                canvas,
                ft.Container(
                    content=ft.Text(
                        "Pelican on a Bicycle · low-poly 3D",
                        size=15,
                        color="#315A66",
                        weight=ft.FontWeight.W_600,
                    ),
                    left=20,
                    top=16,
                ),
            ],
            width=WIDTH,
            height=HEIGHT,
        )
    )
    page.run_task(animate, page, canvas)


if __name__ == "__main__":
    ft.run(main)
