import unittest
from unittest.mock import AsyncMock

from api.client import StarAPI
from api.exceptions import StarAPIError


class OrdersListTests(unittest.IsolatedAsyncioTestCase):
    def client(self, responses):
        api = StarAPI("test-placeholder")
        api.session.post_json = AsyncMock(side_effect=responses)
        api._get_next_data = AsyncMock(return_value={"pageProps": {"orders": []}})
        return api

    async def test_seller_filter_and_pagination(self):
        api = self.client([[{"id": str(i)} for i in range(100)], [{"id": "last"}]])
        result = await api.get_all_orders()
        self.assertEqual(len(result), 101)
        self.assertEqual(api.session.post_json.await_count, 2)
        payload = api.session.post_json.call_args.kwargs["data"]
        self.assertEqual(payload["filter"], {"userType": "seller"})
        self.assertEqual(payload["offset"], 100)
        self.assertEqual(payload["with"], {"buyer": True})

    async def test_invalid_response_and_repeated_page_fail_closed(self):
        for responses in ([{}], [[{"id": str(i)} for i in range(100)]] * 2):
            with self.subTest(responses_type=type(responses[0]).__name__):
                with self.assertRaises(StarAPIError):
                    await self.client(responses).get_all_orders()

    async def test_status_filter_and_empty_list(self):
        api = self.client([[]])
        self.assertEqual(await api.get_all_orders("CREATED"), [])
        self.assertEqual(api.session.post_json.call_args.kwargs["data"]["filter"],
                         {"userType": "seller", "status": "CREATED"})

    async def test_buyer_names_remain_enriched(self):
        api = self.client([[{"id": "one"}]])
        api._get_next_data.return_value = {"pageProps": {"orders": [
            {"id": "one", "user": {"username": "buyer"}}]}}
        self.assertEqual((await api.get_all_orders())[0]["user"]["username"], "buyer")


if __name__ == "__main__":
    unittest.main()
