# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Désactiver les étapes CRM par défaut non adaptées au cycle BTP."""
    old_names = ['New', 'Qualified', '+Qualified', 'Proposition', 'Won', 'DVW', 'Win']
    stages = env['crm.stage'].with_context(active_test=False).search([
        ('name', 'in', old_names)
    ])
    if stages:
        stages.write({'active': False})
