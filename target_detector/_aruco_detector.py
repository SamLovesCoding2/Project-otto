from typing import Any, List, Tuple, TypeVar

import numpy as np
import numpy.typing as npt
from cv2 import cv2  # type: ignore

from project_otto.geometry import IntPoint, Rectangle
from project_otto.image import Frameset
from project_otto.robomaster import TeamColor
from project_otto.spatial import Frame
from project_otto.time import Timestamp

from ._target import DetectedTargetRegion
from ._target_detector import TargetDetector
from ._target_set import ImageDetectedTargetSet

InFrame = TypeVar("InFrame", bound="Frame")
TimeType = TypeVar("TimeType", bound="Timestamp[Any]")
TensorFloat = npt.NDArray[np.float32]


def detect_markers(
    grey_frame: npt.NDArray[np.uint8], dictionary: Any, parameters: Any
) -> Tuple[Tuple[TensorFloat, ...], npt.NDArray[np.intc], Tuple[TensorFloat]]:
    """Wrapper method to contain type ignores. Returns corners, ids, and rejected points."""
    return cv2.aruco.detectMarkers(grey_frame, dictionary, parameters=parameters)  # type: ignore


class ArucoDetector(TargetDetector):
    """
    Detects ArUco square targets for post-detection debugging purposes.

    ArUco targets are relatively easy to identify and locate with high precision and at great
    distances using classical CV. This class can therefore be used in tests as an ideal detector
    with negligible noise and chance of misdetection.

    Targets can be obtained at https://chev.me/arucogen/. Make sure that the markers are of the
    correct pixel sizes and that the marker IDs chosen are within the size of the dictionary (e.g.,
    0-250 for DICT_6x6_250).

    Args:
        team_color: Expected team color of robot. Targets are assigned opposite color.
    """

    def __init__(self, team_color: TeamColor):
        self.team_color = team_color

    def detect_targets(
        self, framesets: List[Frameset[InFrame, TimeType]]
    ) -> List[ImageDetectedTargetSet]:
        """
        Detects members of the first 250 ArUco 6x6 markers.

        Args:
            framesets: List of framesets to extract targets from.
        Returns:
            Rectangle with 0 area; all four corners are at a specific corner of the ArUco target.
        """
        dictionary: Any = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

        parameters: Any = cv2.aruco.DetectorParameters_create()
        parameters.adaptiveThreshConstant = 10

        detected_target_sets: List[ImageDetectedTargetSet] = []
        for frameset in framesets:

            grey_frame: npt.NDArray[np.uint8] = cv2.cvtColor(frameset.color, cv2.COLOR_BGR2GRAY)

            aruco_corners, aruco_ids, _rejected_img_points = detect_markers(
                grey_frame, dictionary, parameters=parameters
            )

            # estimate_pose_single_markers will throw error if list is empty
            if aruco_ids is None:
                detected_target_sets.append(ImageDetectedTargetSet(set()))
                continue

            detected_target_regions: List[DetectedTargetRegion] = []
            for corner in aruco_corners:
                # ul = IntPoint(int(corner[0, 0, 0]), int(corner[0, 0, 1]))
                # ur = IntPoint(int(corner[0, 1, 0]), int(corner[0, 1, 1]))
                # br = IntPoint(int(corner[0, 2, 0]), int(corner[0, 2, 1]))
                # bl = IntPoint(int(corner[0, 3, 0]), int(corner[0, 3, 1]))

                mean_x = np.mean(corner[0, :, 0])
                mean_y = np.mean(corner[0, :, 1])

                width: float = np.max(corner[0, :, 0]) - np.min(corner[0, :, 0])
                height: float = np.max(corner[0, :, 1]) - np.min(corner[0, :, 1])

                half_width = width / 2
                half_height = height / 2

                rectangle = Rectangle.from_point(
                    IntPoint(int(mean_x - half_width), int(mean_y - half_height)),
                    int(width),
                    int(height),
                )
                detected_target_regions.append(
                    DetectedTargetRegion(1.0, TeamColor.flip(self.team_color), rectangle)
                )

            detected_target_sets.append(ImageDetectedTargetSet(set(detected_target_regions)))

        return detected_target_sets
