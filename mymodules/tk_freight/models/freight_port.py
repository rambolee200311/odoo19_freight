from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
class FreightPort(models.Model):
    """Freight Port"""
    _name = 'freight.port'
    _description = __doc__

    code = fields.Char(translate=True)
    name = fields.Char(translate=True)
    air = fields.Boolean()
    ocean = fields.Boolean()
    land = fields.Boolean()
    active = fields.Boolean(default=True)
    # Address
    zip = fields.Char()
    street = fields.Char(string='Street1', translate=True)
    street2 = fields.Char(translate=True)
    city = fields.Char(translate=True)
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one("res.country.state", readonly=False, store=True,
                               domain="[('country_id', '=?', country_id)]")

    @api.constrains('code')
    def _check_code(self):
        """check code"""
        for rec in self:
            codes = self.search([('id', '!=', rec.id)])
            for code in codes:
                if rec.code == code.code:
                    raise ValidationError(
                        _("This code has already been assigned to another port/location."))

    @api.constrains('air', 'ocean', 'land')
    def _check_air_ocean_land(self):
        """check air ocean land"""
        for rec in self:
            if not rec.air and not rec.ocean and not rec.land:
                raise ValidationError(_("Please select any one service in the service details."))
