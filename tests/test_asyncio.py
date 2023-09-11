import pytest

from webscraper.asyncio import TooManyRetries, make_requests


@pytest.fixture
def mock_table_handler():
    class MockClass:
        def insert_into(self, data):
            pass

    return MockClass()


@pytest.fixture
def mock_coro():
    async def mock_func(session, params):
        return [{"coro_result": "success"}]

    return mock_func


@pytest.fixture(params=["success", "fail"])
def mock_retry(monkeypatch, request):
    if request.param == "success":

        async def mock(*args):
            return [{"result": "success"}]

    elif request.param == "fail":

        async def mock(*args):
            # args[0] = sessioned_coro
            # args[1] = params
            raise TooManyRetries(args[1])

    monkeypatch.setattr("webscraper.asyncio.retry", mock)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_retry, expected_succeeded, expected_failed",
    [("success", 5, 0), ("fail", 0, 5)],
    # success and fail parametrize the mock_retry fixture
    # the rest parametrize the test function
    indirect=["mock_retry"],
)
async def test_make_requests(
    mock_coro, mock_retry, mock_table_handler, expected_succeeded, expected_failed
):
    params_list = [{"url": f"http://example.com/page{i}"} for i in range(5)]
    concurrency_limit = 3
    succeeded, failed = await make_requests(
        mock_coro, params_list, concurrency_limit, mock_table_handler
    )
    assert succeeded == expected_succeeded
    assert len(failed) == expected_failed
    if expected_failed > 0:
        failed.sort(key=lambda x: x["url"])
        assert failed == params_list
