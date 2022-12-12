from unittest import mock

from imhotep.reporters.github import (
    CommitReporter,
    GitHubReporter,
    PRReporter,
    PRReviewReporter,
)
from imhotep.reporters.printing import PrintingReporter
from imhotep.testing_utils import Requester


def test_commit_url():
    requester = Requester("")
    cr = CommitReporter(requester, "github.com", "foo/bar")
    cr.report_line(commit="sha", file_name="setup.py", position=0, message="test")

    assert requester.url == "https://api.github.com/repos/foo/bar/commits/sha/comments"


def test_pr_url():
    requester = Requester("")
    pr = PRReporter(requester, "github.com", "justinabrahms/imhotep", 10)
    pr.report_line(commit="sha", file_name="setup.py", position=0, message="test")

    assert (
        requester.url
        == "https://api.github.com/repos/justinabrahms/imhotep/pulls/10/comments"
    )


def test_pr_review_reporter_should_add_comments():
    requester = mock.MagicMock()
    pr = PRReviewReporter(requester, "github.com", "justinabrahms/imhotep", 10)
    pr.report_line(commit="sha", file_name="script.py", position=0, message="lorem")
    assert pr.comments == [{"body": "* lorem\n", "path": "script.py", "position": 0}]
    pr.report_line(commit="sha", file_name="script.py", position=1, message="ipsum")
    assert pr.comments == [
        {"body": "* lorem\n", "path": "script.py", "position": 0},
        {"body": "* ipsum\n", "path": "script.py", "position": 1},
    ]
    assert not requester.post.called


def test_pr_review_reporter_should_post_review():
    requester = mock.MagicMock()
    requester.username = "magicmock"
    requester.post.return_value.status_code = 200
    pr = PRReviewReporter(requester, "api.github.com", "justinabrahms/imhotep", 10)
    pr.comments = [
        {"body": "* lorem\n", "path": "script.py", "position": 0},
    ]
    pr.submit_review()
    assert requester.post.called


def test_pr_already_reported():
    requester = mock.MagicMock()
    requester.username = "magicmock"
    comments = [
        {
            "path": "foo.py",
            "position": 2,
            "body": "Get that out",
            "user": {"login": "magicmock"},
        }
    ]

    pr = PRReporter(requester, "api.github.com", "justinabrahms/imhotep", 10)
    pr._comments = comments
    result = pr.report_line(
        commit="sha",
        file_name="foo.py",
        position=2,
        message="Get that out",
    )
    assert result is None


def test_get_comments_no_cache():
    return_data = {"foo": "bar"}
    requester = mock.MagicMock()
    requester.get.return_value.json = lambda: return_data
    requester.get.return_value.status_code = 200
    pr = GitHubReporter(requester, "api.github.com", "repo-name")
    result = pr.get_comments("example.com")
    assert result == return_data
    assert pr._comments == return_data
    requester.get.assert_called_with("example.com")


def test_get_comments_cache():
    return_data = {"foo": "bar"}
    requester = mock.MagicMock()
    pr = GitHubReporter(requester, "api.github.com", "test-repo")
    pr._comments = return_data
    result = pr.get_comments("example.com")
    assert result == return_data
    assert not requester.get.called


def test_get_comments_error():
    requester = mock.MagicMock()
    requester.get.return_value.status_code = 400
    pr = GitHubReporter(requester, "api.github.com", "test-repo")
    result = pr.get_comments("example.com")
    assert len(result) == 0


def test_clean_already_reported():
    requester = mock.MagicMock()
    requester.username = "magicmock"
    pr = GitHubReporter(requester, "api.github.com", "test-repo")
    comments = [
        {
            "path": "foo.py",
            "position": 2,
            "body": "Get that out",
            "user": {"login": "magicmock"},
        },
        {
            "path": "foo.py",
            "position": 2,
            "body": "Different comment",
            "user": {"login": "magicmock"},
        },
    ]
    message = ["Get that out", "New message"]
    result = pr.clean_already_reported(comments, "foo.py", 2, message)
    assert result == ["New message"]


def test_convert_message_to_string():
    message = ["foo", "bar"]
    requester = mock.MagicMock()
    requester.username = "magicmock"
    pr = GitHubReporter(requester, "api.github.com", "test-repo")
    result = pr.convert_message_to_string(message)
    assert result == "* foo\n* bar\n"


def test_pr__post_comment():
    requester = mock.MagicMock()
    requester.username = "magicmock"
    requester.post.return_value.status_code = 200
    pr = PRReporter(requester, "api.github.com", "justinabrahms/imhotep", 10)
    pr.post_comment("my-message")

    assert requester.post.called


def test_printing_reporter_report_line():
    # smoke test to make sure the string interpolation doesn't explode
    PrintingReporter().report_line(
        commit="commit",
        file_name="file.py",
        position=1,
        message="message",
    )
