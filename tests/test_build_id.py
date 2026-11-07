import asyncio
import unittest
from unittest.mock import AsyncMock

from api.client import StarAPI
from api.exceptions import StarAPIError
from api.utils import extract_build_id


class BuildIdTests(unittest.TestCase):
    def test_script_attribute_order_and_quotes(self):
        self.assertEqual(extract_build_id("<script nonce='x' type='application/json' id='__NEXT_DATA__'>{\"buildId\":\"abc\"}</script>"), "abc")

    def test_missing_and_malformed_data(self):
        for html in ("<html>blocked</html>", '<script id="__NEXT_DATA__">bad</script>', '<script id="__NEXT_DATA__">[]</script>'):
            with self.subTest(html=html), self.assertRaises(ValueError):
                extract_build_id(html)

    def test_fallback_and_cache(self):
        api = StarAPI("1234567890")
        api.session.get_text = AsyncMock(side_effect=["<html>blocked</html>", '<script id="__NEXT_DATA__">{"buildId":"fallback"}</script>'])

        async def run():
            self.assertEqual(await api._get_build_id(), "fallback")
            self.assertEqual(await api._get_build_id(), "fallback")
            self.assertEqual(api.session.get_text.await_count, 2)
        asyncio.run(run())

    def test_all_pages_fail_without_exposing_html(self):
        api = StarAPI("1234567890")
        api.session.get_text = AsyncMock(return_value="sensitive page content")
        with self.assertRaises(StarAPIError) as error:
            asyncio.run(api._get_build_id())
        self.assertNotIn("sensitive page content", str(error.exception))
        self.assertEqual(api.session.get_text.await_count, 3)
