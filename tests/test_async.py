import asyncio

from pytest_lambda import lambda_fixture


sync_value = lambda_fixture(lambda: 'apple')
async_value = lambda_fixture(lambda: 'apple', async_=True)
awaitable_value = lambda_fixture(lambda: asyncio.sleep(0, 'apple'), async_=True)


def it_awaits_async_lambda_fixtures(sync_value, async_value, awaitable_value):
    assert sync_value == async_value == awaitable_value == 'apple'
