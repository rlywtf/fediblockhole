"""Various mergeplan tests
"""

from fediblockhole import apply_mergeplan, merge_blocklists, merge_comments
from fediblockhole.blocklists import parse_blocklist
from fediblockhole.const import DomainBlock, SeverityLevel

import_fields = [
    "domain",
    "severity",
    "public_comment",
    "private_comment",
    "reject_media",
    "reject_reports",
    "obfuscate",
]


def load_test_blocklist_data(datafiles):

    blocklists = []

    for data in datafiles:
        bl = parse_blocklist(data, "pytest", "csv", import_fields)
        blocklists.append(bl)

    return blocklists


def test_mergeplan_max(data_suspends_01, data_silences_01):
    """Test 'max' mergeplan"""
    blocklists = load_test_blocklist_data([data_suspends_01, data_silences_01])
    bl = merge_blocklists(blocklists, "max")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.SUSPEND


def test_mergeplan_min(data_suspends_01, data_silences_01):
    """Test 'max' mergeplan"""
    blocklists = load_test_blocklist_data([data_suspends_01, data_silences_01])

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.SILENCE


def test_mergeplan_default(data_suspends_01, data_silences_01):
    """Default mergeplan is max, so see if it's chosen"""
    blocklists = load_test_blocklist_data([data_suspends_01, data_silences_01])

    bl = merge_blocklists(blocklists)
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.SUSPEND


def test_mergeplan_3_max(data_suspends_01, data_silences_01, data_noop_01):
    """3 datafiles and mergeplan of 'max'"""
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "max")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.SUSPEND
        assert bl[key].reject_media is True
        assert bl[key].reject_reports is True
        assert bl[key].obfuscate is True


def test_mergeplan_3_min(data_suspends_01, data_silences_01, data_noop_01):
    """3 datafiles and mergeplan of 'min'"""
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.NONE
        assert bl[key].reject_media is False
        assert bl[key].reject_reports is False
        assert bl[key].obfuscate is False


def test_mergeplan_noop_v_silence_max(data_silences_01, data_noop_01):
    """Mergeplan of max should choose silence over noop"""
    blocklists = load_test_blocklist_data([data_silences_01, data_noop_01])

    bl = merge_blocklists(blocklists, "max")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.SILENCE


def test_mergeplan_noop_v_silence_min(data_silences_01, data_noop_01):
    """Mergeplan of min should choose noop over silence"""
    blocklists = load_test_blocklist_data([data_silences_01, data_noop_01])

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    for key in bl:
        assert bl[key].severity.level == SeverityLevel.NONE


def test_merge_public_comment(data_suspends_01, data_silences_01, data_noop_01):
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    assert bl["public-comment.example.org"].public_comment == "This is a public comment"


def test_merge_private_comment(data_suspends_01, data_silences_01, data_noop_01):
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    assert (
        bl["private-comment.example.org"].private_comment == "This is a private comment"
    )


def test_merge_public_comments(data_suspends_01, data_silences_01, data_noop_01):
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13

    assert (
        bl["diff-comment.example.org"].public_comment
        == "Suspend public comment, Silence public comment, Noop public comment"
    )


def test_merge_duplicate_comments(data_suspends_01, data_silences_01, data_noop_01):
    """The same comment on multiple sources shouldn't get added"""
    blocklists = load_test_blocklist_data(
        [data_suspends_01, data_silences_01, data_noop_01]
    )

    bl = merge_blocklists(blocklists, "min")
    assert len(bl) == 13


def test_merge_comments_none():

    a = None
    b = None

    r = merge_comments(a, b)

    assert r == ""


def test_merge_comments_empty():

    a = ""
    b = ""

    r = merge_comments(a, b)

    assert r == ""


def test_merge_comments_left():

    a = "comment to merge"
    b = ""

    r = merge_comments(a, b)

    assert r == "comment to merge"


def test_merge_comments_right():

    a = ""
    b = "comment to merge"

    r = merge_comments(a, b)

    assert r == "comment to merge"


def test_merge_comments_same():

    a = "comment to merge"
    b = "comment to merge"

    r = merge_comments(a, b)

    assert r == "comment to merge"


def test_merge_comments_diff():

    a = "comment A"
    b = "comment B"

    r = merge_comments(a, b)

    assert r == "comment A, comment B"


def test_merge_comments_dups():

    a = "boring, nazis, lack of moderation, flagged, special"
    b = "spoon, nazis, flagged, lack of moderation, happy, fork"

    r = merge_comments(a, b)

    assert (
        r == "boring, nazis, lack of moderation, flagged, special, spoon, happy, fork"
    )


def test_mergeplan_same_min_bools_false():
    """Test merging with mergeplan 'max' and False values doesn't change them"""
    a = DomainBlock("example.org", "noop", "", "", False, False, False)
    b = DomainBlock("example.org", "noop", "", "", False, False, False)

    r = apply_mergeplan(a, b, "max")

    assert r.reject_media is False
    assert r.reject_reports is False
    assert r.obfuscate is False


def test_mergeplan_same_min_bools_true():
    """Test merging with mergeplan 'max' and True values doesn't change them"""
    a = DomainBlock("example.org", "noop", "", "", True, False, True)
    b = DomainBlock("example.org", "noop", "", "", True, False, True)

    r = apply_mergeplan(a, b, "max")

    assert r.reject_media is True
    assert r.reject_reports is False
    assert r.obfuscate is True


def test_mergeplan_max_bools():
    a = DomainBlock("example.org", "suspend", "", "", True, True, True)
    b = DomainBlock("example.org", "noop", "", "", False, False, False)

    r = apply_mergeplan(a, b, "max")

    assert r.reject_media is True
    assert r.reject_reports is True
    assert r.obfuscate is True
