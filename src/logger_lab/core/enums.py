from enum import Enum


class ExperimentType(Enum):
     """ enums for experiment types """

     AI            = "AI"
     FILE          = "FILE"
     VERBOSE       = "VERBOSE"
     STANDARD      = "STANDARD"
     MINIMALIST    = "MINIMALIST"
     ROTATING_FILE = "ROTATING"


class ProfileType(Enum):
     """ enums for profile types """

     AGENT        = "AI_AGENT"
     OBSERVER     = "OBSERVER"
     INVESTIGATOR = "INVESTIGATOR"
     CONSPIRATOR  = "CONSPIRACY_THEORIST"


class Channel(Enum):
     """ the output an experiment owns — a logger holds at most one experiment per channel """

     CONSOLE = "CONSOLE"
     FILE    = "FILE"
     JSON    = "JSON"


class TheoryType(Enum):
     """ enums for undiscovered theory types """

     ASYNC       = "ASYNC"
     DB          = "DB"
     HTTP        = "HTTP"
     PERFORMANCE = "PERFORMANCE"
     SEC         = "SEC"
     TIMED_FILE  = "TIMED_FILE"
     TRACE       = "TRACE"
