// Evidence oracle for CRM-Scale natural gaps. Copied into a disposable copy of the suite
// only during key validation; never part of the suite agents assess. Each test must pass
// on the clean app and fail under the fault that proves its criterion is a gap.
import { test, expect } from '../fixtures/crm.fixture';

test.describe('oracle: natural gaps', () => {
  test('CON-SEARCH contact search matches names', async ({ apiAs }) => {
    const found = await (await (await apiAs('viewer')).get('/api/contacts?q=Lovelace')).json();
    expect(found.total).toBe(1);
  });

  test('INV-DUE-DATE new invoices are due 30 days after issue', async ({ apiAs }) => {
    const invoice = await (await (await apiAs('admin')).post('/api/invoices', { data: { quoteId: 'q1' } })).json();
    expect([invoice.issuedOn, invoice.dueOn]).toEqual(['2026-11-15', '2026-12-15']);
  });

  test('OPP-LOST-RECORDED the lost reason is stored', async ({ apiAs }) => {
    const api = await apiAs('sales');
    expect((await api.post('/api/opportunities/o2/stage', { data: { stage: 'lost', lostReason: 'Chose a competitor' } })).status()).toBe(200);
    const list = await (await api.get('/api/opportunities')).json();
    expect(list.items.find((o: { id: string }) => o.id === 'o2').lostReason).toBe('Chose a competitor');
  });

  test('USR-INVITE-ROLE invited users get the chosen role', async ({ apiAs }) => {
    const user = await (await (await apiAs('admin')).post('/api/users', { data: { email: 'oracle@example.com', role: 'support' } })).json();
    expect(user.role).toBe('support');
  });

  test('USR-LAST-ADMIN-DEACTIVATE the last admin cannot be deactivated', async ({ apiAs }) => {
    expect((await (await apiAs('admin')).patch('/api/users/u1', { data: { active: false } })).status()).toBe(409);
  });

  test('AUD-LEAD-DELETE lead deletion is audited', async ({ apiAs }) => {
    const api = await apiAs('admin');
    expect((await api.delete('/api/leads/l2')).status()).toBe(200);
    const log = await (await api.get('/api/audit')).json();
    expect(log.items.filter((e: { action: string; entity: string; id: string }) => e.action === 'delete' && e.entity === 'lead' && e.id === 'l2')).toHaveLength(1);
  });

  test('AUD-SETTINGS settings changes are audited', async ({ apiAs }) => {
    const api = await apiAs('admin');
    expect((await api.patch('/api/settings', { data: { approvalThresholdPct: 20 } })).status()).toBe(200);
    const log = await (await api.get('/api/audit')).json();
    expect(log.items.filter((e: { entity: string }) => e.entity === 'settings')).toHaveLength(1);
  });

  test('DASH-MY-OVERDUE the dashboard counts only the user’s own overdue tasks', async ({ signInAs, page }) => {
    await signInAs('manager');
    await expect(page.getByTestId('my-overdue')).toHaveText('1 of your tasks are overdue.');
  });
});
