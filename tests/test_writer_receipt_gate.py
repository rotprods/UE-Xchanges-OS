"""Integration gate tests: no adapter or broker doubles."""
from dataclasses import replace
from datetime import timedelta
import unittest
import test_writer_receipt_integration as integration
from uexchanges.writer_authorization import WriteIntent
from uexchanges.writer_receipt_gate import (
    WriterPreparationDenied, prepare_writer_authorization, verify_prepared_acquisition,
)


class WriterGateTests(unittest.TestCase):
    def setUp(self):
        fixture=integration.RealReceiptIntegrationTests();fixture.setUp()
        self.values={name:getattr(fixture,name) for name in ('policy','session','ack','prelease','health','now')}
        self.values.update(proposed_lease=fixture.lease,overlapping_unexpired_lease_ids=())
        self.prepared=prepare_writer_authorization(**self.values)

    def acquire(self, **changes):
        values=dict(self.values);values['lease']=values.pop('proposed_lease');values.update(changes)
        return verify_prepared_acquisition(prepared=self.prepared,**values)

    def test_prepare_uses_real_broker_and_verifier(self):
        self.assertTrue(self.prepared.decision.coordination_allowed)
        self.assertTrue(self.prepared.verification.allowed)
        self.assertTrue(self.acquire().allowed)

    def test_serialized_payload_has_no_extra_metadata(self):
        payload=self.prepared.authorization_event_payload()
        self.assertEqual(payload,self.prepared.receipt.as_dict())
        self.assertNotIn('health',payload)
        self.assertIs(payload['domain_authority'],False)
        self.assertIs(payload['external_capability'],False)

    def test_acquisition_refs_are_exact_and_not_a_lease(self):
        refs=self.prepared.acquisition_event_refs()
        self.assertEqual(set(refs),{'authorization_receipt_id','authorization_decision_digest','writer_authorization_receipt_version'})
        self.assertEqual(refs['authorization_receipt_id'],self.prepared.receipt.receipt_id)

    def test_overlap_inventory_cannot_be_omitted(self):
        values=dict(self.values);del values['overlapping_unexpired_lease_ids']
        with self.assertRaises(TypeError):prepare_writer_authorization(**values)

    def test_prepare_denies_overlap(self):
        values=dict(self.values,overlapping_unexpired_lease_ids=('LSE-OTHER',))
        with self.assertRaises(WriterPreparationDenied):prepare_writer_authorization(**values)

    def test_prepare_denies_read_only_session(self):
        values=dict(self.values,session=replace(self.values['session'],status='ACTIVE_READ_ONLY'))
        with self.assertRaises(WriterPreparationDenied):prepare_writer_authorization(**values)

    def test_prepare_denies_external_intent(self):
        with self.assertRaises(WriterPreparationDenied):prepare_writer_authorization(**self.values,intent=WriteIntent.EXTERNAL_SIDE_EFFECT)

    def test_prepare_denies_repair_without_plan(self):
        with self.assertRaises(WriterPreparationDenied):prepare_writer_authorization(**self.values,intent=WriteIntent.CONTROL_PLANE_REPAIR)

    def test_boundary_rejects_new_overlap(self):
        with self.assertRaises(WriterPreparationDenied):self.acquire(overlapping_unexpired_lease_ids=('LSE-OTHER',))

    def test_boundary_rejects_changed_main(self):
        policy=replace(self.values['policy'],bootstrap=replace(self.values['policy'].bootstrap,current_main_sha='b'*40))
        with self.assertRaises(WriterPreparationDenied):self.acquire(policy=policy)

    def test_boundary_rejects_changed_watermark(self):
        with self.assertRaises(WriterPreparationDenied):self.acquire(prelease=replace(self.values['prelease'],private_event_watermark='EVT-NEW'))

    def test_boundary_rejects_changed_scope(self):
        with self.assertRaises(WriterPreparationDenied):self.acquire(lease=replace(self.values['proposed_lease'],scope='github:other'))

    def test_boundary_rejects_changed_health(self):
        health=replace(self.values['health'],metrics={**self.values['health'].metrics,'extra':1})
        with self.assertRaises(WriterPreparationDenied):self.acquire(health=health)

    def test_boundary_rejects_expired_receipt(self):
        with self.assertRaises(WriterPreparationDenied):self.acquire(now=self.values['now']+timedelta(seconds=121))

    def test_boundary_rejects_expired_lease(self):
        lease=replace(self.values['proposed_lease'],expires_at=self.values['now']+timedelta(seconds=1))
        with self.assertRaises(WriterPreparationDenied):self.acquire(lease=lease,now=self.values['now']+timedelta(seconds=2))

    def test_boundary_rejects_future_acquisition(self):
        lease=replace(self.values['proposed_lease'],acquired_at=self.values['now']+timedelta(seconds=1))
        with self.assertRaises(WriterPreparationDenied):self.acquire(lease=lease)

    def test_boundary_rejects_released_lease(self):
        with self.assertRaises(WriterPreparationDenied):self.acquire(lease=replace(self.values['proposed_lease'],status='RELEASED'))

    def test_no_independent_lease_state_is_created(self):
        self.assertFalse(hasattr(self.prepared,'lock'))
        self.assertEqual(self.prepared.authorization_event_payload(),self.prepared.authorization_event_payload())
