# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

# FIX TEXT FIELD

class Lead(models.Model):
    _inherit = 'crm.lead'

    project_manager = fields.Many2one('res.users', string='Project Manager')
    customer_category = fields.Selection(
        [('Top Account', 'Top Account'), ('Key Account', 'Key Account'), ('Account', 'Account'), ('New Account', 'New Account'), ('House Account', 'House Account')], string='Customer Category')
        
    # I) LEADS
    # 1 LEAD - FOCUS
    l_prospect_fits_our_ideal_customer_group = fields.Boolean(string='Prospect Fits Our Ideal Customer Group')
    l_prospect_has_critical_or_urgent_need = fields.Boolean(string='Prospect Has Critical or Urgent Need')
    l_we_have_solution_to_satisfy_the_need = fields.Boolean(string='We Have Solution to Satisfy The Need')
    l_we_have_a_coach_in_or_close_to_company = fields.Boolean(string='We Have a Coach in or Close to Company')
    l_solving_this_need_is_in_their_budget = fields.Boolean(string='Solving This Need is in Their Budget')
    l_revenues_and_margins_are_sufficient = fields.Boolean(string='Revenues And Margins Are Sufficient')

    # 2 LEAD - RESEARCH
    l_annual_revenue = fields.Integer(string='Annual Revenue')
    l_no_of_employees = fields.Integer(string='No. of Employees')
    l_industry = fields.Char(string='Industry')
    l_website = fields.Char(string='Website')
    l_buyer_role = fields.Selection(
        [('User', 'User'), ('Technical/System', 'Technical/System'), ('Economic/Strategic', 'Economic/Strategic')], string='Buyer Role')
    l_description = fields.Text(string='Description')
    l_prospect_linkedin = fields.Char(string='Prospect LinkedIn')
    l_linkedin_company = fields.Char(string='LinkedIn Company')
    l_products_they_sell = fields.Char(string='Products They Sell')
    l_markets_they_serve = fields.Text(string='Markets They Serve')
    l_competitors = fields.Text(string='Competitors')

    # 3 LEAD - COACHES AND PERSONALITIES
    l_this_prospect_will_be_our_coach = fields.Boolean(help="80 percent chance of making the sale when you have a coach vs. 20 percent when you don’t", string='This Prospect Will Be Our coach')
    l_personality_type = fields.Char(help="When you match or mirror a personality type you have an 80 percent chance of making the sale vs. 20 percent if you don’t", string='Personality Type')
    l_personality_type_matched_mirrored = fields.Boolean(help="Drivers - high goal orientation, low empathy (goal driven). Motivators high goal orientation, high empathy(relationship driven). Thinkers low goal orientation, low empathy (task driven). Supports low goal orientation, high empathy (people driven)", string='Personality Type Matched/Mirrored')

    # II) OPPORTUNITIES
    # 1 OPPORTUNITY - FOCUS
    o_prospect_fits_our_ideal_customer_group = fields.Boolean(string='Prospect Fits Our Ideal Customer Group')
    o_prospect_has_critical_or_urgent_need = fields.Boolean(string='Prospect Has Critical or Urgent Need')
    o_we_have_solution_to_satisfy_the_need = fields.Boolean(string='We Have Solution to Satisfy The Need')
    o_we_have_a_coach_in_or_close_to_company = fields.Boolean(string='We Have a Coach in or Close to Company')
    o_solving_this_need_is_in_their_budget = fields.Boolean(string='Solving This Need is in Their Budget')
    o_revenues_and_margins_are_sufficient = fields.Boolean(string='Revenues And Margins Are Sufficient')

    # 2 OPPORTUNITY - COACHES AND PERSONALITIES
    o_this_prospect_will_be_our_coach = fields.Boolean(help="80 percent chance of making the sale when you have a coach vs. 20 percent when you don’t", string='This Prospect Will Be Our coach')
    o_personality_type = fields.Char(help="When you match or mirror a personality type you have an 80 percent chance of making the sale vs. 20 percent if you don’t", string='Personality Type')
    o_key_buyers_researched = fields.Boolean(string='Key Buyers Researched')
    o_personality_type_matched_mirrored = fields.Boolean(string='Personality Type Matched/Mirrored')

    # 3 OPPORTUNITY - RAPPORT
    o_bought_me = fields.Boolean(string='Bought Me')
    o_bought_our_company = fields.Boolean(string='Bought Our Company')
    o_bought_our_price = fields.Boolean(string='Bought Our Price')
    o_bought_this_opportunity = fields.Boolean(string='Bought This Opportunity')
    o_bought_a_timeframe = fields.Boolean(string='Bought a Timeframe')

    # 4 OPPORTUNITY - MARKETING MESSAGES
    o_killer_argument_delivered = fields.Boolean(help="Answers the question - Can we do this?", string='Killer Argument Delivered')
    o_key_discriminators_delivered = fields.Boolean(help="Answers the question – Why choose us?", string='Key Discriminators Delivered')
    o_ghosting_discriminators_delivered = fields.Boolean(help="Answers the question – Why not choose the competition (without directly naming them)", string='Ghosting Discriminators Delivered')
    o_roi_type_determined = fields.Boolean(help="Check this box if the ROI type (hard, soft, what-if) has been determined for this opportunity", string='ROI Type Determined')
    o_roi_story_delivered = fields.Boolean(help="Answers the question – why do this at all?", string='ROI Story Delivered')
    o_testimonials_delivered = fields.Boolean(help="Answers the question – have you done it for others", string='Testimonials Delivered')

    # 5 OPPORTUNITY - BUSINESS CONSULTANT
    o_highest_needs_determined = fields.Boolean(string='Highest Needs Determined')
    o_buyers_understand_value_of_offering = fields.Boolean(string='Buyers Understand Value of Offering')
    o_buyer_requirements_summarized = fields.Boolean(string='Buyer Requirement Summarized')
    o_cited_the_gain = fields.Boolean(string='Cited The Gains')
    o_cited_three_offerings_or_less = fields.Boolean(string='Cited Three Offerings or Less')
    o_objections_addressed = fields.Boolean(string='Objections Addressed')

    # 6 OPPORTUNITY - CLOSING
    o_recognized_buyers_shift = fields.Boolean(string='Recognized Buyers Shift')
    o_asked_for_the_sale = fields.Boolean(string='Asked For The Sale')
    o_closing_approach_used = fields.Char(string='Closing Approach Used')
    o_confirmed_the_sale = fields.Boolean(string='Confirmed The Sale')
