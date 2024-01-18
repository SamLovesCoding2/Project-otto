from dataclasses import dataclass

from lightning_models.config_reader import RunConfig


@dataclass
class DetectorConfiguration(RunConfig):
    """
    Config class for Lightning detector.

    Args:
        model_architecture_name: the name of the lightning model architecture to load.
        weights_path: path to weights checkpoint.
        gpus: number of GPUs to use.
        precision: string representing float precision to use (half, float, or double).
        time_size: number of time steps to iterate over.
        image_height: height of image used by model.
        image_width: width of image used by model.
        channel_count: number of color channels, i.e., 3.
        confidence_threshold: minimum confidence for plate detection.
        iou_threshold: maximum permitted iou between any two detected target regions.
    """

    model_architecture_name: str
    weights_path: str

    gpus: int
    precision: str

    time_size: int
    image_height: int
    image_width: int
    channel_count: int

    confidence_threshold: float
    duplicate_target_iou_threshold: float
