"""Target Containers."""
import logging
from dataclasses import dataclass
from typing import Set, TypeVar

from project_otto.geometry import IntRectangle
from project_otto.spatial import Frame

from ._target import DetectedTargetRegion

InFrame = TypeVar("InFrame", bound=Frame)


@dataclass
class ImageDetectedTargetSet:
    """
    Represents a set of detected targets.
    """

    plates: Set[DetectedTargetRegion]

    def non_max_suppressed(self, iou_threshold: float) -> "ImageDetectedTargetSet":
        """
        Returns a detected target set such that no two targets have iou greater than iou_threshold.

        The returned detected target set contains a iff a is in plates and there does not exist a
        plate b in plates such that a != b, a.confidence < b.confidence and
        iou(a, b) >= iou_threshold.
        Args:
            iou_theshold: The maximum permitted iou between two distinct detected target regions.
        Returns:
            The set of DetectedPlateRegions satisfying the aforementioned conditions.
        """
        suppressed_plate_set = set([plate for plate in self.plates])
        for plate in self.plates:
            for other in self.plates:
                if (
                    plate is not other
                    and IntRectangle.iou(plate.rectangle, other.rectangle) >= iou_threshold
                ):
                    discard_plate = min(plate, other, key=lambda x: x.detection_confidence)
                    logging.debug(f"Discarded plate during non-max suppression: {discard_plate}")
                    suppressed_plate_set.discard(discard_plate)
        return ImageDetectedTargetSet(suppressed_plate_set)
