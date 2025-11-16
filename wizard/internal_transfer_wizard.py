from odoo import models, fields, api
from odoo.exceptions import UserError


from odoo import models, fields, api
from odoo.exceptions import UserError

class BankInternalTransferWizard(models.TransientModel):
    _name = 'bank.internal.transfer.wizard'
    _description = 'Bank Internal Transfer Wizard'

    source_journal_id = fields.Many2one('account.journal', string='Source Bank', required=True, domain=[('type', 'in', ("bank","cash"))])
    destination_journal_id = fields.Many2one('account.journal', string='Destination Bank', required=True, domain=[('type', 'in', ["bank","cash"])])
    source_partner_id = fields.Many2one('res.partner', string='Paid By', required=True, default=lambda self: self.env.ref('bank_internal_transfer.default_transfer_partner').id)
    destination_partner_id = fields.Many2one('res.partner', string='Paid To', required=True, default=lambda self: self.env.ref('bank_internal_transfer.default_transfer_partner').id)
    transfer_account_id = fields.Many2one(
        'account.account',
        string='Liquidity Transfer Account',
        required=True,
        domain=[('account_type', '=', 'asset_current')],
        default=lambda self: self.env.company.transfer_account_id.id,
    )
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    note = fields.Char(string='Memo')

    def action_confirm(self):
        self.ensure_one()

        if self.source_journal_id == self.destination_journal_id:
            raise UserError("Source and destination bank accounts must be different.")

        if not self.transfer_account_id:
            raise UserError("Please select a Liquidity Transfer Account.")
        media=self.env.ref('bank_internal_transfer.default_transfer_partner').id
        ref= f'Transfer from {self.source_journal_id.name} to {self.destination_journal_id.name}'
        if self.source_partner_id.id != media or self.destination_partner_id.id !=media:
            ref= f'{ref},from {self.source_partner_id.name} to {self.destination_partner_id.name}'
        if self.note:
            ref=f'{ref},{self.note}'
        debit_partner=self.source_partner_id.id
        credit_partner=self.destination_partner_id.id

        outbound=self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_id':debit_partner,
            'amount':self.amount,
            'memo':ref,
            'journal_id': self.source_journal_id.id,
            'date':self.date
        })
        outbound.action_post()
        inbound=self.env['account.payment'].create({
            'payment_type':'inbound',
            'partner_id':credit_partner,
            'amount':self.amount,
            'memo':ref,
            'journal_id': self.destination_journal_id.id,
            'date':self.date
        })
        inbound.action_post()
        # # --- OUTGOING MOVE ---
        # out_move = self.env['account.move'].create({
        #     'ref': ref,
        #     'date': self.date,
        #     # 'journal_id': self.source_journal_id.id,
        #     'line_ids': [
        #         (0, 0, {
        #             'name': ref,
        #             'account_id': self.transfer_account_id.id,
        #             'debit': self.amount,
        #             'credit': 0.0,
        #         }),
        #         (0, 0, {
        #             'name': ref,
        #             'account_id': self.source_journal_id.default_account_id.id,
        #             'debit': 0.0,
        #             'credit': self.amount,
        #         }),
        #     ]
        # })
        # out_move.action_post()

        # --- INCOMING MOVE ---
        # in_move = self.env['account.move'].create({
        #     'ref': ref,
        #     'date': self.date,
        #     # 'journal_id': self.destination_journal_id.id,
        #     'line_ids': [
        #         (0, 0, {
        #             'name': ref,
        #             'account_id': self.destination_journal_id.default_account_id.id,
        #             'debit': self.amount,
        #             'credit': 0.0,
        #         }),
        #         (0, 0, {
        #             'name': ref,
        #             'account_id': self.transfer_account_id.id,
        #             'debit': 0.0,
        #             'credit': self.amount,
        #         }),
        #     ]
        # })
        # in_move.action_post()
        #
        # # reconcile transfer Accounts entries
        # lines_to_reconcile = (out_move.line_ids + in_move.line_ids).filtered(
        #     lambda l: l.account_id == self.transfer_account_id
        # )
        # if len(lines_to_reconcile) == 2:
        #     lines_to_reconcile.reconcile()
        #
        # # reconcile debit-credit entry
        # lines_to_reconcile = (out_move.line_ids + in_move.line_ids).filtered(
        #     lambda l: l.account_id != self.transfer_account_id
        # )
        # if len(lines_to_reconcile) == 2:
        #     lines_to_reconcile.reconcile()

        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Journal Entries',
        #     'res_model': 'account.move',
        #     'view_mode': 'form',
        #     'domain': [('id', 'in', [out_move.id, in_move.id])],
        #     'target': 'new',
        # }

    def action_cancel(self):
        """Simply close the wizard."""
        return {'type': 'ir.actions.act_window_close'}