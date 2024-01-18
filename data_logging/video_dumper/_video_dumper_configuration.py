from dataclasses import dataclass


@dataclass
class VideoDumperConfiguration:
    """
    Configuration for VideoDumper.

    Args:
        num_frames_per_video_chunk: Number of frames to be saved in each video chunk
        frame_rate: FPS of input frames and output video
        minimum_index_digits: Number of zeroes to pad the index of each video. For example,
            minimum_index_digits = 4 will yield videos titled "videoname0001", "videoname 0002",
            etc. If the video index exceeds minimum_index, the index width will increase
            accordingly, for example "videoname123456."
    """

    # Seconds x Frame rate
    num_frames_per_video_chunk: int
    frame_rate: int
    minimum_index_digits: int
