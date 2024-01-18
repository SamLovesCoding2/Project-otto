from abc import ABC, abstractmethod
from typing import Any, List, Sequence, Set, Tuple, TypeVar

import cv2  # type: ignore
import numpy as np
import numpy.typing as npt
import pytorch_lightning as pl
import torch
from lightning_models import losses
from lightning_models.models import get_model_by_name
from lightning_models.models.model_base import ModelBase
from torch.nn.functional import max_pool2d  # pyright: ignore[reportUnknownVariableType]

from project_otto.geometry import IntRectangle
from project_otto.image import Frameset
from project_otto.robomaster import TeamColor
from project_otto.spatial import Frame
from project_otto.time import Timestamp

from ._config import DetectorConfiguration
from ._target import DetectedTargetRegion
from ._target_set import ImageDetectedTargetSet

InFrame = TypeVar("InFrame", bound="Frame")
TimeType = TypeVar("TimeType", bound="Timestamp[Any]")


torch_dtypes = {"half": torch.half, "float": torch.float, "double": torch.double}


class TargetDetector(ABC):
    """
    Class that takes in a Frameset and outputs a set of targets.
    """

    @abstractmethod
    def detect_targets(
        self, framesets: List[Frameset[InFrame, TimeType]]
    ) -> List[ImageDetectedTargetSet]:
        """
        Given a set of frames, detect targets and return a set of the targets that were detected.

        Args:
            framesets: A List of Frameset containing image color and depth frames.
        """
        pass


class LightningTargetDetector(TargetDetector):
    """
    The implemented form of the abstract class above using PyTorch models.

    Args:
        config: path to config yaml file.
    """

    def __init__(self, config: DetectorConfiguration, model: pl.LightningModule):

        self._config = config
        self._model = model.type(torch_dtypes[config.precision]).eval()

        if config.gpus > 0:
            _ = self._model.cuda()

    def detect_targets(
        self, framesets: Sequence[Frameset[InFrame, TimeType]]
    ) -> List[ImageDetectedTargetSet]:
        """
        Takes color frame of frameset, runs it through ML model, draws rectangles around targets.

        Args:
            framesets: Framesets to extract targets from. Color frame should have dim (h, w, 3).
        Returns:
            ImageDetectedTargetSet containing targets of both colors.
        """
        # TODO: This enforcer may be eating a significant amount of time
        # Context enforcer
        if (0.0 * torch.empty(1, requires_grad=True)).requires_grad:
            raise RuntimeError("Expected method to be run within torch.no_grad() context.")

        osizes = []
        rsize = (self._config.image_height, self._config.image_width)
        data: torch.Tensor = torch.empty(
            (len(framesets), 3, self._config.image_width, self._config.image_height)
        )

        for i, frameset in enumerate(framesets):
            if len(frameset.color.shape) != 3:
                raise ValueError(
                    f"Expected color frame array with 3 dimensions, got {len(frameset.color.shape)}"
                    + " dimensions."
                )
            if frameset.color.shape[2] != 3:
                raise ValueError(
                    "Expected color frame array shape with 3 channels in index 2, got "
                    + f"{frameset.color.shape[2]}."
                )

            osizes.append(frameset.color.shape)

            # TODO: Evaluate best compromise between interpolation quality and speed
            color = frameset.color
            color: npt.NDArray[np.uint8] = cv2.resize(
                color, dsize=rsize, interpolation=cv2.INTER_NEAREST
            )

            color: npt.NDArray[np.uint8] = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
            # H,W,C -> C,H,W
            color = np.swapaxes(color, 0, 2)
            color = np.swapaxes(color, 1, 2)

            data[i] = torch.from_numpy(color)

        if self._config.gpus > 0:
            data = data.cuda()

        data = data.to(torch_dtypes[self._config.precision])

        data = data / 255

        prediction: torch.Tensor = self._model(data, infer=True)
        prediction = prediction.to(torch.float).cpu()

        # Looks for both red and blue plates
        target_heatmap = prediction[:, :2, :, :]
        offset_map = prediction[:, 2 : 2 + 2, :, :]
        size_map = prediction[:, 4 : 4 + 2, :, :]

        plate_sets_red, plate_sets_blue = self._create_plate_set(
            target_heatmap, offset_map, size_map, osizes
        )

        image_detected_target_sets: List[ImageDetectedTargetSet] = []
        for plate_set_red, plate_set_blue in zip(plate_sets_red, plate_sets_blue):
            image_detected_target_sets.append(
                ImageDetectedTargetSet(set.union(plate_set_blue, plate_set_red)).non_max_suppressed(
                    iou_threshold=self._config.duplicate_target_iou_threshold
                )
            )
        return image_detected_target_sets

    # TODO: Consider
    #       1. Return union of red and blue sets
    #       2. Return list of tuple rather than tuple of list

    def _create_plate_set(
        self,
        heatmap: torch.Tensor,
        offset_map: torch.Tensor,
        size_map: torch.Tensor,
        scale_dims: Sequence[Tuple[int, int]],
    ) -> Tuple[Sequence[Set[DetectedTargetRegion]], Sequence[Set[DetectedTargetRegion]]]:
        """
        Generates set of detected plates from pixel heatmap, offset map, and size map.

        Synthesizes the information spat out by the detector model.
        Args:
            heatmap: (b, 2, h, w) Tensor containing confidence of plate detection at point (y, x).
            offset_map: (b, 2, h, w) Tensor containing y and x offsets of plate center from point,
                in index-units (e.g., offset_map[:, 3, 4] == [-1, 1] means add -1 to the y index and
                1 to the x index of the peak to get its actual position).
            size_map: (b, 2, h, w) Tensor containing y and x sizes of plate occupying that point, in
                in image-dim-units (i.e., a value 0.5 means half the width/height of the heatmap).
            scale_dims: Final image (height, width) to scale to.
        Returns:
            A b-length sequence of sets of DetectedPlateRegions.

        """
        # List comprehension necessary to create unique instances rather than copies
        plate_sets_red: List[Set[DetectedTargetRegion]] = [set() for _ in range(heatmap.shape[0])]
        plate_sets_blue: List[Set[DetectedTargetRegion]] = [set() for _ in range(heatmap.shape[0])]

        # Get discrete local maxima to extract cohesive "blobs" from heatmap
        peaks = (
            heatmap
            * torch.gt(heatmap, self._config.confidence_threshold)
            * torch.eq(heatmap, max_pool2d(heatmap, (3, 3), stride=1, padding=1))
        )
        peak_indices = torch.nonzero(peaks)

        def clamp_to_height(y: int, b: int) -> int:
            return min(max(y, 0), scale_dims[b][0])

        def clamp_to_width(x: int, b: int) -> int:
            return min(max(x, 0), scale_dims[b][1])

        # Terrible idx_idx to satiate typechecker
        for idx_idx in range(peak_indices.size()[0]):
            b_idx = int(peak_indices[idx_idx, 0].item())
            c_idx = int(peak_indices[idx_idx, 1].item())
            y_idx = peak_indices[idx_idx, 2].item()
            x_idx = peak_indices[idx_idx, 3].item()
            confidence = float(heatmap[b_idx, c_idx, y_idx, x_idx].float().item())
            y_c = (float(y_idx) + float(offset_map[b_idx, 0, y_idx, x_idx].item())) / float(
                heatmap.shape[2]
            )
            x_c = (float(x_idx) + float(offset_map[b_idx, 1, y_idx, x_idx].item())) / float(
                heatmap.shape[3]
            )
            h = float(size_map[b_idx, 0, y_idx, x_idx].item())
            w = float(size_map[b_idx, 1, y_idx, x_idx].item())

            x0 = int((x_c - 0.5 * w) * scale_dims[b_idx][1])
            y0 = int((y_c - 0.5 * h) * scale_dims[b_idx][0])
            x1 = int((x_c + 0.5 * w) * scale_dims[b_idx][1])
            y1 = int((y_c + 0.5 * h) * scale_dims[b_idx][0])

            x0 = clamp_to_width(x0, b_idx)
            y0 = clamp_to_height(y0, b_idx)
            x1 = clamp_to_width(x1, b_idx)
            y1 = clamp_to_height(y1, b_idx)

            if c_idx == 0:
                plate_sets_red[b_idx].add(
                    DetectedTargetRegion(confidence, TeamColor.RED, IntRectangle(x0, y0, x1, y1))
                )
            else:
                plate_sets_blue[b_idx].add(
                    DetectedTargetRegion(confidence, TeamColor.BLUE, IntRectangle(x0, y0, x1, y1))
                )

        return plate_sets_red, plate_sets_blue

    @classmethod
    def from_weights_checkpoint(cls, config: DetectorConfiguration) -> "LightningTargetDetector":
        """
        Utility function which generates model using config file.
        """
        # One image at a time, hence batch size 1
        batch_size = 1
        # Red and blue
        class_count = 2
        input_dim = (
            config.time_size,
            batch_size,
            config.channel_count,
            config.image_height,
            config.image_width,
        )

        if config.gpus > 0:
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")

        model: ModelBase = get_model_by_name(config.model_architecture_name).load_from_checkpoint(
            config.weights_path,
            input_dim=input_dim,
            classes=class_count,
            loss_function=losses.centernet_loss,
            config=config,
            map_location=device,
        )

        return cls(config, model)
