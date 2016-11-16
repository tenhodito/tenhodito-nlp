import pytest
import tenhodito_nlp


def test_project_defines_author_and_version():
    assert hasattr(tenhodito_nlp, '__author__')
    assert hasattr(tenhodito_nlp, '__version__')
