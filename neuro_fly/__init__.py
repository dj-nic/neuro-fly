"""Hardware-independent building blocks for the FlyBrain Reflex demonstrator."""

from .interfaces import Brain, DistanceSample, DistanceSensor, Output
from .sensor import ApproachConfig, ApproachEncoder, MockDistanceSensor
from .output import MockOutput, PulseController, SafetyConfig
from .brain import BrainSetupError, BrainStepError, NeuroHexBrainAdapter
from .pipeline import CycleResult, Pipeline, run_pipeline

__all__ = [
    "ApproachConfig", "ApproachEncoder", "Brain", "BrainSetupError",
    "BrainStepError", "CycleResult", "DistanceSample", "DistanceSensor",
    "MockDistanceSensor", "MockOutput", "NeuroHexBrainAdapter", "Output",
    "Pipeline", "PulseController", "SafetyConfig", "run_pipeline",
]
