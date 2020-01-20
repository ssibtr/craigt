# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class Contact(models.Model):
    _inherit = 'res.partner'

    customer = fields.Boolean(string='Is a Customer', default=False,
                               help="Check this box if this contact is a customer. It can be selected in sales orders.")
    project_manager_id = fields.Many2one('res.users', string='Project Manager', help='Project Manager from user table.')
    fax = fields.Char(string='Fax')
    opened_date = fields.Date(string='Opened Date')
    vendor_1099 = fields.Boolean(string='Vendor 1099')
    ach_email = fields.Char(string='ACH Email')
    ach_email_alt = fields.Char(string='ACH Email Alt')
    coi_expiration_date = fields.Date(string='COI Expiration')
    exemption_certificate_date = fields.Date(string='Exemption Certificate Date', help='Date exemption certificate expires.')
    customer_category = fields.Selection(
        [('Top Account', 'Top Account'), ('Key Account', 'Key Account'), ('Account', 'Account'), ('House Account', 'House Account')], string='Customer Category')

    # I) CONTACTS
    # 1 FOCUS
    c_contact_fits_our_ideal_customer_group = fields.Boolean(string='Contact Fits Our Ideal Customer Group')
    c_contact_has_critical_or_urgent_need = fields.Boolean(string='Contact Has Critical or Urgent Need')
    c_solving_this_need_is_in_their_budget = fields.Boolean(string='Solving This Need is in Their budget')
    c_we_have_solution_to_satisfy_the_need = fields.Boolean(string='We Have Solution to Satisfy The Need')

    # 2 RESEARCH
    c_department = fields.Char(string='Department')
    c_reports_to = fields.Char(string='Reports to')
    c_description = fields.Char(string='Description')
    c_contact_linkedin = fields.Char(string='Contact LinkedIn')
    c_buyer_role = fields.Selection(
        [('User', 'User'), ('Technical/System', 'Technical/System'), ('Economic/Strategic', 'Economic/Strategic')], string='Buyer Role')

    # 3 COACHES AND PERSONALITIES
    c_this_prospect_will_be = fields.Boolean(help="80 percent chance of making the sale when you have a coach vs. 20 percent when you don’t", string='This Prospect Will Be')
    c_personality_type = fields.Selection([('Driver', 'Driver'), ('Motivator', 'Motivator'), ('Thinker', 'Thinker'), ('Supporter', 'Supporter')], 
        help="When you match or mirror a personality type you have an 80 percent chance of making the sale vs. 20 percent if you don’t",
        string='Personality Type')

    # 4 REFERRALS
    c_who = fields.Char('Who?')
    c_introduce_us = fields.Selection(
        [('Yes', 'Yes'), ('No', 'No')], string='Introduce Us?')
    c_referal_pursued = fields.Selection([('Yes', 'Yes'), ('No', 'No')], help="Business that results from referrals from existing clients have a 92 percent retention rate, and 54 percent of all referrals eventually buy. But 87 percent of referrals are never pursued",
        string='Referal Pursued?')
    c_referal_type = fields.Selection(
        [('Existing Customer', 'Existing Customer'), ('Vendor', 'Vendor'), ('Supplier', 'Supplier'), ('Partner', 'Partner'), ('Consultant', 'Consultant'), ('Business Associate', 'Business Associate'), ('Friend/Family', 'Friend/Family'), ('Other', 'Other')], string='Referal Type')


    # II) ACCOUNTS
    # 1 RESEARCH
    a_annual_revenue = fields.Integer(string='Annual Revenue')
    a_employees = fields.Integer(string='Employees')
    a_website = fields.Char(string='Website')
    a_industry = fields.Char(string='Industry')
    a_description = fields.Text(string='Description')
    a_linkedin_company = fields.Char(string='LinkedIn Company')
    a_products_they_sell = fields.Char(string='Products They Sell')
    a_markets_they_serve = fields.Text(string='Markets They Serve')
    a_our_competition = fields.Text(string='Our Competition')

    # 2 CUSTOMERS
    a_company_goals = fields.Char(string='Company Goals')
    a_what_do_we_do_well = fields.Char(string='What Do We Do Well?')
    a_what_can_we_do_better = fields.Char(string='What Can We Do Better?')
    a_what_are_your_current_needs = fields.Char(string='What Are Your Current Needs?')
    a_what_are_your_future_requirements = fields.Char(string='What Are Your Future Requirements?')
    a_net_promoter_score = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')], 
        help="On a scale of one to ten, ten being the highest, how likely is it that you would recommend us to your friends or colleagues?",
        string='Net Promoter Score')
