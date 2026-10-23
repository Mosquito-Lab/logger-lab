"""The composition rules: what attaches where, what can't mix, options, profiles and the suggestion warning."""

import inspect
import logging
import warnings

import pytest

from logger_lab import BuilderError, CompositionError, Output, ProfileSuggestionWarning, ProfileType, lab
from logger_lab.logging_kernel import LabFileHandler
from logger_lab.outputs import LabRichHandler


################
# The profiles #
################

@pytest.mark.parametrize(("profile", "expected"), [
    ("investigator", {"CONSOLE": {"format": "RICH", "features": []},
                      "FILE": {"format": "TEXT", "features": []}, "catalysts": []}),
    ("observer", {"CONSOLE": {"format": "RICH", "features": ["MINIMAL"]}, "catalysts": []}),
    ("conspiracy_theorist", {"CONSOLE": {"format": "RICH", "features": ["VERBOSE"]},
                             "FILE": {"format": "TEXT", "features": ["ROTATING", "VERBOSE"]}, "catalysts": []}),
    ("ai_agent", {"CONSOLE": {"format": "JSON", "features": []}, "catalysts": []}),
    ("gui", {"FILE": {"format": "TEXT", "features": ["ROTATING"]},
             "RELAY": {"format": None, "features": []}, "catalysts": ["ASYNC"]}),
])
def test_each_profile_is_its_documented_composition(profile, expected):
    """Profiles are recipes of builder calls. Their plans are exactly the documented compositions."""

    assert lab().with_profile(profile).plan().names() == expected


def test_one_profile_per_builder():
    """A second profile is a `CompositionError`. Add to the first one instead."""

    with pytest.raises(CompositionError, match="already uses the 'OBSERVER' profile"):
        lab().with_profile("observer").with_profile("investigator")


def test_a_profile_keeps_its_features_on_its_own_outputs():
    """A file added to ai_agent or observer is a plain text file. Their JSON and MINIMAL stay on the console."""

    for profile in ("ai_agent", "observer"):
        names = lab().with_profile(profile).with_output("file").plan().names()

        assert names["FILE"] == {"format": "TEXT", "features": []}


#######################################
# Features and formats: where they go #
#######################################

def test_a_feature_or_format_goes_on_every_output_it_fits():
    """VERBOSE fits console and file, ROTATING only the file. RICH fits only the console, so the file stays TEXT."""

    names = (
        lab().with_profile("investigator").with_feature("VERBOSE").with_feature("ROTATING").with_format("RICH")
        .plan().names()
    )

    assert names["CONSOLE"] == {"format": "RICH", "features": ["VERBOSE"]}
    assert names["FILE"] == {"format": "TEXT", "features": ["ROTATING", "VERBOSE"]}


def test_on_narrows_a_feature_or_format_to_one_output():
    """A minimal console beside a verbose JSON file."""

    names = (
        lab().with_profile("investigator")
        .with_feature("MINIMAL", on="console").with_feature("ROTATING", on="file").with_format("JSON", on="file")
        .plan().names()
    )

    assert names["CONSOLE"] == {"format": "RICH", "features": ["MINIMAL"]}
    assert names["FILE"] == {"format": "JSON", "features": ["ROTATING"]}


@pytest.mark.parametrize(("call", "match"), [
    (lambda: lab().with_profile("observer").with_feature("ROTATING"),
     r"'ROTATING' needs a file output: add \.with_output\('file'\), or start from a profile such as 'investigator'"),
    (lambda: lab().with_subscriber(print).with_format("JSON"), "'JSON' needs a console or file output"),
    (lambda: lab().with_catalyst("ASYNC"), "'ASYNC' needs an output to work on"),
    (lambda: lab().with_profile("investigator").with_feature("ROTATING", on="console"),
     "'ROTATING' works on file outputs, not console"),
    (lambda: lab().with_profile("investigator").with_format("RICH", on="file"),
     "'RICH' works on console outputs, not file"),
    (lambda: lab().with_profile("observer").with_format("JSON", on="file"), "on='file', but no file output is queued"),
], ids=["feature without its output", "format without an output", "catalyst without an output",
        "on= an output it doesn't fit", "RICH on a file", "on= an output not queued"])
def test_nothing_brings_an_output_and_on_must_fit(call, match):
    """A building block never adds an output behind the user's back. The error names the fix."""

    with pytest.raises(CompositionError, match=match):
        call().plan()


@pytest.mark.parametrize(("call", "match"), [
    (lambda: lab().with_profile("observer").with_feature("VERBOSE"),
     "'MINIMAL' and 'VERBOSE' both set the detail of the console output"),
    (lambda: lab().with_profile("ai_agent").with_format("TEXT"), "already has format 'JSON'; one format per output"),
    (lambda: lab().with_profile("ai_agent").with_feature("MINIMAL"), "'MINIMAL' has no effect on the JSON format"),
], ids=["two detail features", "two formats", "detail on JSON"])
def test_what_cannot_mix_on_one_output(call, match):
    """One detail feature and one format per output, and only where they work."""

    with pytest.raises(CompositionError, match=match):
        call().plan()


def test_different_detail_on_different_outputs_is_fine():
    """The detail group is per output."""

    lab().with_profile("investigator").with_feature("MINIMAL", on="console").with_feature("VERBOSE", on="file").plan()


###########
# Options #
###########

def test_with_output_configures_a_profile_output_and_repeats_merge():
    """with_output() on a profile's output configures it. Each call merges per key, later values win."""

    composition = (
        lab().with_profile("investigator").with_output("file", log_dir="a", filename="x.log")
        .with_output("file", log_dir="b").with_feature("ROTATING", max_bytes=10).with_feature("ROTATING", max_bytes=20)
        .plan()
    )
    (file,) = [planned for planned in composition.outputs if planned.output is Output.FILE]

    assert len(composition.outputs) == 2 and file.origin == "from profile 'INVESTIGATOR'"
    assert file.options == {"log_dir": "b", "filename": "x.log", "encoding": "utf-8", "backup_count": 3}
    assert list(file.features.values()) == [{"max_bytes": 20}]


def test_a_repeated_catalyst_is_one_catalyst():
    """ASYNC twice configures the first. Still one dispatcher."""

    assert lab().with_profile("gui").with_catalyst("ASYNC").plan().names()["catalysts"] == ["ASYNC"]


@pytest.mark.parametrize(("call", "match"), [
    (lambda: lab().with_output("file", colour="red"),
     "'FILE' has no option 'colour'; its options: log_dir, filename, encoding, backup_count"),
    (lambda: lab().with_profile("investigator").with_output("file", max_bytes=10), "'FILE' has no option 'max_bytes'"),
    (lambda: lab().with_output("console").with_catalyst("ASYNC", workers=2),
     "'ASYNC' has no option 'workers'; its options: none"),
    (lambda: lab().with_output("console", stream="printer"), "console stream='printer'"),
    (lambda: lab().with_output("file", backup_count=-1), "backup_count=-1"),
    (lambda: lab().with_output("file", backup_count=0).with_feature("ROTATING"),
     "'ROTATING' need backup_count of 1 or more"),
    (lambda: lab().with_output("file").with_feature("ROTATING", max_bytes=0), "max_bytes=0"),
], ids=["unknown option", "another block's option", "a block with no options", "stream", "negative backups",
        "rotation with no backups", "max_bytes"])
def test_bad_options_are_errors(call, match):
    """
    An undeclared option is a typo, not something to ignore, and each spec checks its values.

    (TIMED's options: test_rotation.)
    """

    with pytest.raises(CompositionError, match=match):
        call().plan()


def test_a_plain_file_may_keep_no_backups():
    """backup_count=0 is fine without rotation."""

    lab().with_output("file", backup_count=0).plan()


##########################
# The profile suggestion #
##########################

def test_hand_queued_console_and_file_suggests_investigator_at_the_callers_line():
    """console + file by hand is investigator. Say so, but build anyway, and point at the build() call."""

    with pytest.warns(ProfileSuggestionWarning, match=r"console \+ file is the 'INVESTIGATOR' profile") as caught:
        logger = lab().with_output("console").with_output("file").build("suggest.inv")

    assert [type(h) for h in logger.handlers] == [LabRichHandler, LabFileHandler]
    assert caught[0].filename == __file__


def test_the_suggestion_points_at_the_callers_line_through_plan_too():
    """CR-16: through plan() the fixed stacklevel pointed one frame past the caller."""

    with pytest.warns(ProfileSuggestionWarning) as caught:
        lab().with_output("console").with_output("file").plan()  # this line

    assert caught[0].filename == __file__
    assert caught[0].lineno == inspect.currentframe().f_lineno - 3  # pyrefly: ignore[missing-attribute]


def test_the_most_specific_working_profile_is_suggested():
    """console + file + VERBOSE + ROTATING is conspiracy_theorist, not just investigator."""

    with pytest.warns(ProfileSuggestionWarning, match="'CONSPIRACY_THEORIST'"):
        lab().with_output("console").with_output("file").with_feature("VERBOSE").with_feature("ROTATING").plan()


def test_a_suggestion_never_adds_anything_or_clashes():
    """
    A profile is only suggested if following the advice gives the same logger.

    file + relay isn't gui, which would add ROTATING and ASYNC. A minimal console beside a
    verbose file isn't conspiracy_theorist, whose VERBOSE would clash with MINIMAL on the
    console, so it falls back to investigator. One output, or a profile, never warns.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        lab().with_output("file").with_subscriber(print).plan()
        lab().with_output("console").with_feature("MINIMAL").plan()

        for profile in ProfileType:
            lab().with_profile(profile).plan()

    with pytest.warns(ProfileSuggestionWarning, match="'INVESTIGATOR'"):
        (lab().with_output("console").with_output("file").with_feature("VERBOSE", on="file")
         .with_feature("ROTATING").with_feature("MINIMAL", on="console").plan())

    # conspiracy_theorist would also put VERBOSE on the console, which wasn't asked for.
    with pytest.warns(ProfileSuggestionWarning, match="'INVESTIGATOR'"):
        (lab().with_output("console").with_output("file").with_feature("VERBOSE", on="file")
         .with_feature("ROTATING").plan())


######################
# Planning and build #
######################

def test_an_empty_builder_raises():
    """Nothing queued is a `BuilderError`."""

    with pytest.raises(BuilderError, match="nothing is queued"):
        lab().build("empty")


def test_a_rejected_composition_leaves_an_existing_logger_untouched():
    """plan() raises before the old handlers are cleared, and plan() alone builds nothing."""

    logger = lab().with_profile("observer").build("keep")
    handler = logger.handlers[0]

    with pytest.raises(CompositionError):
        lab().with_profile("observer").with_feature("VERBOSE").build("keep")

    lab().with_profile("investigator").plan()

    assert logger.handlers == [handler]
    assert not logging.getLogger("never.built").handlers


def test_outputs_build_in_queue_order_and_never_propagate():
    """Handlers come out in queue order. with_output() on an existing output keeps its place."""

    with pytest.warns(ProfileSuggestionWarning):
        logger = lab().with_output("file").with_output("console").with_output("file", filename="b.log").build("order")

    assert [type(h) for h in logger.handlers] == [LabFileHandler, LabRichHandler]
    assert logger.propagate is False
