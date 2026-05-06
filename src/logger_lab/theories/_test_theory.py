from logger_lab import get_logger
from logger_lab.core.enums import TheoryType

# THEORIES (single handler factories):
theory_logger = get_logger(name="doom", theory=TheoryType.TIMED_FILE)

######################################
# PLEASE DON'T ACTUALLY RUN THIS YET #
######################################
