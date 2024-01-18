"""
A generic representation of image data at some point in time from a single frame of reference.

Framesets and Framesources specific to Project Otto should *not* be included in this module; see
the top-level framesets and framesources modules.
"image" is designed to be (sort-of) application-agnostic (it fixes image data to be color and depth)
"""

from ._frameset import Frameset
from ._framesource import FrameSource

__all__ = ["Frameset", "FrameSource"]
