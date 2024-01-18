from enum import Enum
from typing import Any, Optional, Tuple

import cv2  # type: ignore
import numpy as np
import numpy.typing as npt

from project_otto.geometry import Point, Rectangle


class COLORS(Enum):
    """
    BGR color codes.
    """

    RED = (0, 0, 255)
    BLUE = (255, 0, 0)
    CYAN = (255, 255, 0)
    GREEN = (0, 255, 0)
    ORANGE = (0, 165, 255)
    MAGENTA = (128, 128, 255)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


def draw_point(
    image: npt.NDArray[np.uint8],
    point: Point[Any],
    radius: float = 3,
    color: COLORS = COLORS.BLACK,
    thickness: int = 3,
    linetype: int = cv2.LINE_8,
):
    """
    Draws a point on an image.

    Args:
        image: the image as a uint8 numpy array
        point: the Point to draw
        radius: the size of the point
        color: a BGR tuple color
        thickness: the thickness of the point
    """
    cv2.circle(image, (round(point.x), round(point.y)), radius, color.value, thickness, linetype)


def draw_rectangle(
    image: npt.NDArray[np.uint8],
    rect: Rectangle[Any],
    color: COLORS = COLORS.BLACK,
    thickness: int = 3,
    linetype: int = cv2.LINE_8,
):
    """
    Draws a rectangle on an image.

    Args:
        image: the image as a uint8 numpy array
        point: the Rectangle to draw
        color: a BGR tuple color
        thickness: the thickness of the rectangle
    """
    cv2.rectangle(
        image,
        (round(rect.x0), round(rect.y0)),
        (round(rect.x1), round(rect.y1)),
        color.value,
        thickness,
        linetype,
    )


def draw_line(
    image: npt.NDArray[np.uint8],
    p1: Point[Any],
    p2: Point[Any],
    color: COLORS = COLORS.BLACK,
    thickness: int = 3,
    arrowhead: bool = False,
):
    """
    Draws a line on an image.

    Args:
        image: the image as a uint8 numpy array
        point: the Point to draw
        color: a BGR tuple color
        thickness: the thickness of the point
        arrowhead: whether or not to draw the arrowhead
    """
    if arrowhead:
        cv2.arrowedLine(
            image, (round(p1.x), round(p1.y)), (round(p2.x), round(p2.y)), color.value, thickness
        )
    else:
        cv2.line(
            image, (round(p1.x), round(p1.y)), (round(p2.x), round(p2.y)), color.value, thickness
        )


def draw_text(
    image: npt.NDArray[np.uint8],
    text: str,
    p: Point[Any],
    offset: Tuple[int, int] = (0, 0),
    font_scale: float = 1.0,
    color: COLORS = COLORS.BLACK,
    thickness: int = 3,
    outline_color: Optional[COLORS] = None,
    outline_thickness: int = 1,
):
    """
    Draws text on an image.

    Args:
        image: the image as a uint8 numpy array
        text: the text
        point: the location of the text
        offset: an optional offset from the point
        font_scale: font size
        color: a BGR tuple color
        thickness: the thickness of the characters
        outline_color: color of an outline, or None
    """
    if outline_color is not None:
        draw_text(
            image,
            text,
            p,
            offset,
            font_scale,
            outline_color,
            thickness=thickness + outline_thickness,
        )

    cv2.putText(
        image,
        text,
        (round(p.x + offset[0]), round(p.y + offset[1])),
        cv2.FONT_HERSHEY_PLAIN,
        font_scale,
        color.value,
        thickness,
    )
