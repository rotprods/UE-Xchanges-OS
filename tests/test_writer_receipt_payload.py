import copy
import json
import unittest
from datetime import datetime
from writer_receipt_test_fixtures import valid_receipt
from uexchanges.writer_receipt_payload import (
    REQUIRED_FIELDS, DATE_FIELDS, IDENTITY_FIELDS, PATTERNS,
    ReceiptPayloadError, inspect_receipt_payload,
    require_valid_receipt_payload, load_receipt_json, load_strict_json,
)


class ReceiptPayloadTests(unittest.TestCase):
    def test_canonical_shape_passes(self):
        self.assertEqual(inspect_receipt_payload(valid_receipt()), ())

    def test_all_required_fields_are_required(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                raw = valid_receipt(); del raw[field]
                self.assertTrue(any(i.field == field and i.code == "REQUIRED_FIELD_MISSING"
                                    for i in inspect_receipt_payload(raw)))

    def test_unknown_fields_rejected(self):
        raw = valid_receipt(); raw["decision"] = "ALLOWED"
        with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_aliases_never_repaired(self):
        for canonical, alias in [("observed_main_sha", "main_sha"),
                                 ("authorization_decision_digest", "decision_digest"),
                                 ("prelease_lease_scan_at", "lease_scan_time")]:
            with self.subTest(alias=alias):
                raw = valid_receipt(); raw[alias] = raw.pop(canonical)
                with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_ids_never_coerced(self):
        for field in IDENTITY_FIELDS:
            for value in [None, 0, 123, False, [], {}, ""]:
                with self.subTest(field=field, value_type=type(value).__name__):
                    raw = valid_receipt(); raw[field] = value
                    with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_boolean_constants_strict(self):
        for field in ["coordination_allowed", "domain_authority", "external_capability"]:
            for value in [0, 1, "false", "true", None, [], "NONE"]:
                with self.subTest(field=field, type=type(value).__name__):
                    raw = valid_receipt(); raw[field] = value
                    with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_authority_cannot_be_asserted(self):
        for field in ["domain_authority", "external_capability"]:
            raw = valid_receipt(); raw[field] = True
            with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_wrong_contract_and_version(self):
        for field in ["contract", "version"]:
            raw = valid_receipt(); raw[field] = "other"
            with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_hash_patterns(self):
        for field in PATTERNS:
            for value in [1, "g"*64, "a"*39, "a"*64+"\n"]:
                raw = valid_receipt(); raw[field] = value
                with self.subTest(field=field, value_type=type(value).__name__):
                    with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_dates_reject_naive_invalid_and_objects(self):
        for field in DATE_FIELDS:
            for value in ["2026-01-01T12:00:00", "2026-02-30T12:00:00Z",
                          "2026-01-01", 1, datetime.now(), "2026-01-01T12:00:00+25:00", "2026-01-01T12:00:00+00:99"]:
                raw = valid_receipt(); raw[field] = value
                with self.subTest(field=field, type=type(value).__name__):
                    with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_utc_and_fractional_dates(self):
        for value in ["2026-01-01T12:00:00Z", "2026-01-01t12:00:00z",
                      "2026-01-01T12:00:00.123456+02:00"]:
            raw = valid_receipt(); raw["issued_at"] = value
            self.assertEqual(inspect_receipt_payload(raw), ())

    def test_intent_is_enum_not_authority(self):
        raw = valid_receipt(); raw["intent"] = "EXTERNAL_SIDE_EFFECT"
        # This is shape-valid but the existing broker must deny execution.
        self.assertEqual(inspect_receipt_payload(raw), ())
        raw["intent"] = "SUBMIT_NOW"
        with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_overlap_array_and_uniqueness(self):
        for value in [None, (), "LSE", [0], [""], ["LSE", "LSE"]]:
            raw = valid_receipt(); raw["overlapping_lease_ids"] = value
            with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_repair_reference(self):
        for value in [None, "RPL-"+"a"*16]:
            raw = valid_receipt(); raw["repair_plan_id"] = value
            self.assertEqual(inspect_receipt_payload(raw), ())
        for value in ["UEX-PLAN", "", 1, False, "RPL-"+"a"*17]:
            raw = valid_receipt(); raw["repair_plan_id"] = value
            with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_no_mutation(self):
        raw = valid_receipt(); original = copy.deepcopy(raw)
        require_valid_receipt_payload(raw)
        self.assertEqual(raw, original)

    def test_errors_are_value_safe(self):
        secret = "PRIVATE_VALUE_DO_NOT_LOG"
        raw = valid_receipt(); raw[secret] = secret; raw["receipt_id"] = secret
        with self.assertRaises(ReceiptPayloadError) as caught: require_valid_receipt_payload(raw)
        self.assertNotIn(secret, str(caught.exception))

    def test_nonobject_rejected(self):
        for raw in [None, [], "{}", 0, True]:
            with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_nonstring_key_rejected(self):
        raw = valid_receipt(); raw[1] = "field"
        with self.assertRaises(ReceiptPayloadError): require_valid_receipt_payload(raw)

    def test_json_roundtrip(self):
        raw = valid_receipt(); self.assertEqual(load_receipt_json(json.dumps(raw)), raw)

    def test_duplicate_json_key_rejected(self):
        text = json.dumps(valid_receipt())[:-1] + ', "domain_authority": false}'
        with self.assertRaises(ReceiptPayloadError): load_receipt_json(text)

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ReceiptPayloadError): load_receipt_json('{"x":NaN}')

    def test_invalid_json_rejected(self):
        with self.assertRaises(ReceiptPayloadError): load_receipt_json('{')

    def test_json_input_type(self):
        with self.assertRaises(ReceiptPayloadError): load_receipt_json(None)

    def test_historical_expiry_not_a_shape_failure(self):
        raw = valid_receipt()
        self.assertEqual(inspect_receipt_payload(raw), ())
        # No now() lookup: historical receipts must not be retroactively invalidated.

    def test_deterministic_issue_order(self):
        raw = {"bad": True}
        self.assertEqual(inspect_receipt_payload(raw), inspect_receipt_payload(dict(reversed(list(raw.items())))))


class StrictSnapshotJsonTests(unittest.TestCase):
    def test_nested_duplicates_rejected(self):
        with self.assertRaises(ReceiptPayloadError):
            load_strict_json('{"receipts":[{"domain_authority":true,"domain_authority":false}]}')

    def test_snapshot_object_passes_without_receipt_root_assumption(self):
        value = {"receipts":[valid_receipt()],"leases":[]}
        self.assertEqual(load_strict_json(json.dumps(value)), value)
