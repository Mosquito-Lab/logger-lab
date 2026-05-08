"""
main.py just highlights how to use this thing in a testable environment.
Use these examples to guide you in your own project
"""

import logging
from logger_lab import lab, get_logger, log_event, ExperimentType, ProfileType

# Profiles (prebuilt combinations):
profile_logger = get_logger(name="profile_test", profile="conspiracy_theorist")

# Experiments (single handler factories):
experiment_logger = get_logger(name="experiment_test", experiment=ExperimentType.MINIMALIST)

# Fluent builder (custom composition):
built_logger = (
    lab()
    .with_experiment('STANDARD')
    .with_experiment(ExperimentType.FILE)
    .with_level(logging.DEBUG)
    .build(__name__)
)

# Structured events (AI / machine-readable output):
ai_logger = get_logger(name="AI test", profile=ProfileType.AGENT)


if __name__ == "__main__":
    profile_logger.info("PROFILE IS A SUCCESS")
    experiment_logger.info("EXPERIMENT IS ALSO A SUCCESS")
    built_logger.debug("THE BUILDER WORKS!")
    log_event(
        ai_logger, logging.INFO, "Inference complete",
        event="inference_done",
        context={"tokens": 512},
    )

