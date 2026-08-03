from __future__ import annotations

import json
import unittest

from anonymizing_proxy.anonymizer import Anonymizer, TokenMapper
from anonymizing_proxy.anonymizer.patterns import looks_like_uuid


class UuidPreservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = TokenMapper(tokenmap_max=1000)
        self.anonymizer = Anonymizer(self.mapper)
        self.session = "test-session"

    def test_looks_like_uuid(self) -> None:
        uid = "a95815c1-8e7b-11f1-9a43-20f17c75566c"
        self.assertTrue(looks_like_uuid(uid))
        self.assertTrue(looks_like_uuid("{" + uid + "}"))
        self.assertFalse(looks_like_uuid("not-a-uuid"))
        self.assertFalse(looks_like_uuid("1234567890"))

    def test_uuid_value_not_anonymized(self) -> None:
        uid = "00001413-8001-7777-0001-00000000c845"
        out = self.anonymizer.anonymize_string(self.session, uid, key_hint=None)
        self.assertEqual(out, uid)

    def test_unique_id_key_preserved(self) -> None:
        # Digit-heavy GUID that CARD/INN patterns would otherwise eat.
        uid = "12345678-8001-1234-5678-901234567890"
        obj = {
            "_objectRef": True,
            "УникальныйИдентификатор": uid,
            "ТипОбъекта": "СправочникСсылка.Склады",
            "Представление": "ООО Тест",
        }
        anon = self.anonymizer.anonymize_obj(self.session, obj)
        self.assertEqual(anon["УникальныйИдентификатор"], uid)
        self.assertNotEqual(anon["Представление"], "ООО Тест")
        self.assertTrue(anon["Представление"].startswith("[ORG-"))

    def test_uuid_inside_json_text_payload(self) -> None:
        uid = "a95815c1-8e7b-11f1-9a43-20f17c75566c"
        payload = {
            "success": True,
            "rows": [
                {
                    "Склад": {
                        "_objectRef": True,
                        "УникальныйИдентификатор": uid,
                        "ТипОбъекта": "СправочникСсылка.Склады",
                        "Представление": "Склад ТЦ Рига Молл GWE Москва",
                    }
                }
            ],
        }
        text = json.dumps(payload, ensure_ascii=False)
        anon_text = self.anonymizer.anonymize_string(self.session, text, key_hint=None)
        anon = json.loads(anon_text)
        self.assertEqual(
            anon["rows"][0]["Склад"]["УникальныйИдентификатор"],
            uid,
        )

    def test_inn_still_anonymized(self) -> None:
        out = self.anonymizer.anonymize_string(self.session, "7707083893", key_hint="ИНН")
        self.assertTrue(out.startswith("[INN-"))

    def test_uuid_embedded_in_plain_text(self) -> None:
        uid = "a95815c1-8e7b-11f1-9a43-20f17c75566c"
        text = f"Ссылка {uid} и ИНН 7707083893"
        out = self.anonymizer.anonymize_plain_text(self.session, text)
        self.assertIn(uid, out)
        self.assertNotIn("7707083893", out)
        self.assertIn("[INN-", out)


if __name__ == "__main__":
    unittest.main()
