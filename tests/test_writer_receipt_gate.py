"""Integration gate tests: no adapter or broker doubles."""
from dataclasses import replace
from datetime import timedelta
import unittest
import test_writer_receipt_integration as integration
from uexchanges.global_barrier import BarrierRecord, BarrierState, resolve_global_barriers
from uexchanges.writer_authorization import WriteIntent
from uexchanges.writer_receipt_gate import (
    WriterPreparationDenied, prepare_writer_authorization, verify_prepared_acquisition,
    verify_prepared_effect_boundary,
)


class WriterGateTests(unittest.TestCase):
    def setUp(self):
        fixture=integration.RealReceiptIntegrationTests();fixture.setUp()
        self.values={name:getattr(fixture,name) for name in ('policy','session','ack','prelease','health','now')}
        self.values.update(proposed_lease=fixture.lease,global_barrier=fixture.barrier,overlapping_unexpired_lease_ids=())
        self.prepared=prepare_writer_authorization(**self.values)

    def acquire(self, **changes):
        values=dict(self.values);values['lease']=values.pop('proposed_lease');values.update(changes)
        return verify_prepared_acquisition(prepared=self.prepared,**values)

    def barrier(self, *, state=None, revision=1, watermark=None, observed_at=None):
        records=()
        if state is not None:
            records=(BarrierRecord(
                barrier_id='BAR-C0', revision=revision, event_id=f'EVT-BAR-{revision}-{state.value}',
                project_id='UE-Xchanges-OS', context_id=self.values['session'].context_id,
                state=state, blocked_intents=(WriteIntent.VERSIONED_CODE.value,),
                updated_at=self.values['now'],
            ),)
        return resolve_global_barriers(
            records=records, project_id='UE-Xchanges-OS', context_id=self.values['session'].context_id,
            intent=WriteIntent.VERSIONED_CODE.value, scope=self.values['proposed_lease'].scope,
            observed_at=observed_at or self.values['now'],
            event_watermark=watermark or self.values['prelease'].private_event_watermark,
            source_complete=True,
        )

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

    def test_prepare_denies_missing_barrier_snapshot(self):
        values=dict(self.values);values['global_barrier']=None
        with self.assertRaises(WriterPreparationDenied) as caught:
            prepare_writer_authorization(**values)
        self.assertIn('GLOBAL_BARRIER_UNKNOWN',caught.exception.codes)

    def test_boundary_rejects_active_barrier_created_after_waz(self):
        active=self.barrier(state=BarrierState.ACTIVE)
        with self.assertRaises(WriterPreparationDenied) as caught:
            self.acquire(global_barrier=active)
        self.assertIn('GLOBAL_BARRIER_ACTIVE',caught.exception.codes)

    def test_boundary_rejects_released_revision_change_and_requires_fresh_waz(self):
        released=self.barrier(state=BarrierState.RELEASED,revision=2)
        with self.assertRaises(WriterPreparationDenied) as caught:
            self.acquire(global_barrier=released)
        self.assertIn('GLOBAL_BARRIER_CHANGED',caught.exception.codes)

    def test_effect_boundary_allows_same_clear_revision_after_receipt_ttl(self):
        later=self.values['now']+timedelta(seconds=180)
        lease=replace(self.values['proposed_lease'],expires_at=later+timedelta(minutes=5))
        fresh=self.barrier(observed_at=later,watermark='EVT-LATER')
        verify_prepared_effect_boundary(
            prepared=self.prepared,policy=self.values['policy'],lease=lease,
            global_barrier=fresh,now=later,
        )

    def test_effect_boundary_rejects_new_active_barrier(self):
        later=self.values['now']+timedelta(seconds=10)
        active=self.barrier(state=BarrierState.ACTIVE,observed_at=later,watermark='EVT-BLOCK')
        with self.assertRaises(WriterPreparationDenied) as caught:
            verify_prepared_effect_boundary(
                prepared=self.prepared,policy=self.values['policy'],
                lease=self.values['proposed_lease'],global_barrier=active,now=later,
            )
        self.assertIn('GLOBAL_BARRIER_ACTIVE',caught.exception.codes)

    def test_effect_boundary_rejects_clear_but_changed_revision(self):
        later=self.values['now']+timedelta(seconds=10)
        released=self.barrier(state=BarrierState.RELEASED,revision=2,observed_at=later,watermark='EVT-REL')
        with self.assertRaises(WriterPreparationDenied) as caught:
            verify_prepared_effect_boundary(
                prepared=self.prepared,policy=self.values['policy'],
                lease=self.values['proposed_lease'],global_barrier=released,now=later,
            )
        self.assertIn('GLOBAL_BARRIER_CHANGED',caught.exception.codes)

    def test_no_independent_lease_state_is_created(self):
        self.assertFalse(hasattr(self.prepared,'lock'))
        self.assertEqual(self.prepared.authorization_event_payload(),self.prepared.authorization_event_payload())
