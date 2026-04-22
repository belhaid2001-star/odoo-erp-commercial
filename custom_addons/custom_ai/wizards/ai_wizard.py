# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIWizard(models.TransientModel):
    _name = 'ai.wizard'
    _description = 'Assistant IA'

    # Context fields
    res_model = fields.Char(string='Modèle source', required=True)
    res_id = fields.Integer(string='ID enregistrement')
    module_name = fields.Char(string='Module')

    # ──────────────── Commande vocale ────────────────
    voice_transcript = fields.Text(
        string='Commande vocale (transcription)',
        help="Collez ici la transcription de votre commande vocale. "
             "L'IA interprétera le contenu et créera les activités correspondantes.",
        placeholder="Ex : Appelle Mohamed demain matin pour discuter de l'offre BTP. "
                    "Puis envoie-lui un email de suivi dans 3 jours.",
    )
    use_voice_mode = fields.Boolean(
        string='Mode commande vocale',
        default=False,
        help="Activez pour créer des activités à partir d'une commande vocale.",
    )

    # Input
    action_type = fields.Selection([
        ('generate_description', '📝 Générer une description'),
        ('analyze', '📊 Analyser les données'),
        ('suggest_price', '💰 Suggestion de prix/remise'),
        ('suggest_action', '🎯 Prochaine action recommandée'),
        ('generate_email', '📧 Générer un email'),
        ('evaluate', '📋 Synthèse d\'évaluation'),
        ('predict', '🔮 Prédiction'),
        ('btp_conseil', '🏗️ Mohasib — Conseil fiscal/comptable'),
        ('btp_saisie', '📒 Mohasib — Écriture comptable PCM'),
        ('btp_analyse', '📊 Mohasib — Analyse financière chantier'),
        ('create_activity', '📌 Créer activités depuis commande vocale'),
        ('custom', '✏️ Requête personnalisée'),
    ], string='Action IA', required=True, default='analyze')

    custom_prompt = fields.Text(string='Requête personnalisée',
                                help="Décrivez ce que vous souhaitez que l'IA fasse")

    # Output
    ai_result = fields.Html(string='Résultat IA', readonly=True)
    ai_provider = fields.Char(string='Source', readonly=True)

    # Activités créées
    created_activity_ids = fields.Many2many(
        'mail.activity',
        string='Activités créées',
        readonly=True,
    )
    activity_count = fields.Integer(
        string='Activités créées',
        compute='_compute_activity_count',
    )

    def _compute_activity_count(self):
        for rec in self:
            rec.activity_count = len(rec.created_activity_ids)

    @api.onchange('use_voice_mode')
    def _onchange_use_voice_mode(self):
        if self.use_voice_mode:
            self.action_type = 'create_activity'

    @api.onchange('action_type')
    def _onchange_action_type(self):
        if self.action_type == 'custom':
            self.custom_prompt = ''
        elif self.action_type in ('btp_conseil', 'btp_saisie'):
            self.custom_prompt = ''
        elif self.action_type == 'create_activity':
            self.use_voice_mode = True

    def action_generate(self):
        """Execute the AI action and display results."""
        self.ensure_one()

        if self.action_type == 'create_activity':
            return self._action_create_activities_from_voice()

        mixin = self.env['ai.mixin']

        # Gather context data from the source record
        ctx = self._get_record_context()

        # Build prompt based on action type
        prompts = {
            'generate_description': f"Génère une description commerciale pour : {ctx.get('name', '')}",
            'analyze': f"Analyse complète de cet enregistrement",
            'suggest_price': f"Suggestion de prix et remise pour cette commande",
            'suggest_action': f"Quelle est la prochaine action recommandée ?",
            'generate_email': f"Génère un email de relance professionnel",
            'evaluate': f"Génère une synthèse d'évaluation",
            'predict': f"Fais une prédiction basée sur les données disponibles",
            'btp_conseil': self.custom_prompt or "Comment fonctionne la TVA BTP au Maroc ?",
            'btp_saisie': self.custom_prompt or "Comptabilise la situation de travaux",
            'btp_analyse': f"Analyse financière complète du chantier {ctx.get('name', '')}",
            'custom': self.custom_prompt or "Analyse cette situation",
        }
        prompt = prompts.get(self.action_type, self.custom_prompt)
        # Force module to 'btp' for Mohasib action types
        if self.action_type in ('btp_conseil', 'btp_saisie', 'btp_analyse'):
            module = 'btp'
        else:
            module = self.module_name or 'general'

        # Call AI
        result = mixin.ai_generate(prompt, ctx, module)

        # Format result as HTML
        text = result.get('result', 'Aucun résultat')
        html_result = self._format_result_html(text, result.get('provider', 'builtin'))

        self.write({
            'ai_result': html_result,
            'ai_provider': result.get('provider', 'builtin'),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'name': '🤖 Résultat IA',
        }

    def _action_create_activities_from_voice(self):
        """Parse la commande vocale et crée des activités Odoo automatiquement."""
        self.ensure_one()
        transcript = self.voice_transcript or self.custom_prompt
        if not transcript:
            raise UserError(_("Veuillez saisir ou coller une commande vocale dans le champ prévu."))

        if not self.res_model or not self.res_id:
            raise UserError(_("Aucun enregistrement source trouvé pour créer des activités."))

        # Use AI to parse the voice command and extract activities
        mixin = self.env['ai.mixin']
        ctx = self._get_record_context()
        ctx['voice_command'] = transcript

        ai_prompt = (
            f"À partir de cette commande vocale : « {transcript} »\n"
            f"Enregistrement concerné : {ctx.get('display_name', '')} ({self.res_model})\n\n"
            "Identifie et liste toutes les tâches/activités à créer au format :\n"
            "ACTIVITÉ: [type] | [titre] | [date] | [responsable]\n"
            "Types disponibles : Appel téléphonique, WhatsApp, Email, Réunion, Tâche, Rappel\n"
            "Date relative acceptée : 'demain', 'dans 3 jours', 'lundi prochain'\n"
            "Si aucune date : 'aujourd\\'hui'"
        )

        result = mixin.ai_generate(ai_prompt, ctx, 'crm')
        raw_text = result.get('result', '')

        # Parse activities from AI output
        activities_created = self._parse_and_create_activities(raw_text, transcript)

        html_result = self._format_activities_html(activities_created, raw_text)

        self.write({
            'ai_result': html_result,
            'ai_provider': result.get('provider', 'builtin'),
            'created_activity_ids': [(6, 0, [a.id for a in activities_created])],
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'name': '📌 Activités créées',
        }

    def _parse_and_create_activities(self, ai_text, original_transcript):
        """Parse AI output and create mail.activity records."""
        from datetime import date, timedelta
        import re

        activities = []
        today = date.today()

        # Activity type mapping
        type_map = {
            'appel': 'call',
            'téléphone': 'call',
            'whatsapp': 'whatsapp',
            'email': 'email',
            'réunion': 'meeting',
            'rdv': 'meeting',
            'tâche': 'todo',
            'rappel': 'todo',
        }

        # Date parsing
        def parse_date(text):
            text_lower = text.lower() if text else ''
            if 'demain' in text_lower:
                return today + timedelta(days=1)
            elif 'dans 3 jours' in text_lower:
                return today + timedelta(days=3)
            elif 'dans 7 jours' in text_lower or 'semaine' in text_lower:
                return today + timedelta(days=7)
            elif 'lundi' in text_lower:
                days_ahead = 0 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            return today

        # Try to parse structured output from AI
        lines = ai_text.split('\n') if ai_text else []
        parsed_activities = []

        for line in lines:
            if 'ACTIVITÉ:' in line or 'ACTIVITE:' in line:
                parts = re.split(r'\|', line.replace('ACTIVITÉ:', '').replace('ACTIVITE:', ''))
                if len(parts) >= 2:
                    act_type_str = parts[0].strip().lower()
                    act_summary = parts[1].strip() if len(parts) > 1 else 'Activité IA'
                    act_date_str = parts[2].strip() if len(parts) > 2 else ''
                    act_date = parse_date(act_date_str)
                    parsed_activities.append({
                        'type_str': act_type_str,
                        'summary': act_summary,
                        'date': act_date,
                    })

        # Fallback: create a single activity if no structured output
        if not parsed_activities:
            parsed_activities.append({
                'type_str': 'tâche',
                'summary': _('Action depuis commande vocale : %s') % original_transcript[:100],
                'date': today + timedelta(days=1),
            })

        # Create activities in Odoo
        ActivityType = self.env['mail.activity.type']
        for act_data in parsed_activities:
            # Find or match activity type
            act_type = None
            for keyword, act_code in type_map.items():
                if keyword in act_data['type_str']:
                    act_type = ActivityType.search([
                        ('summary', 'ilike', keyword),
                    ], limit=1) or ActivityType.search([], limit=1)
                    break
            if not act_type:
                # Default to first available activity type
                act_type = ActivityType.search([], limit=1)
            if not act_type:
                continue

            try:
                activity = self.env['mail.activity'].create({
                    'res_model': self.res_model,
                    'res_id': self.res_id,
                    'activity_type_id': act_type.id,
                    'summary': act_data['summary'][:250],
                    'date_deadline': act_data['date'],
                    'note': _('<p>Activité créée automatiquement depuis commande vocale IA :</p>'
                              '<blockquote>%s</blockquote>') % original_transcript,
                    'user_id': self.env.user.id,
                })
                activities.append(activity)
            except Exception as e:
                _logger.warning("Failed to create activity from voice command: %s", e)

        return activities

    def _format_activities_html(self, activities, raw_ai_text):
        """Format created activities as HTML for display."""
        if not activities:
            return '<p class="text-warning">⚠️ Aucune activité n\'a pu être créée. Vérifiez la commande vocale.</p>'

        html = f'<div class="alert alert-success"><strong>✅ {len(activities)} activité(s) créée(s)</strong></div>'
        html += '<ul class="list-group">'
        for act in activities:
            html += (
                f'<li class="list-group-item">'
                f'<strong>{act.activity_type_id.name}</strong> : {act.summary} '
                f'— Échéance : <strong>{act.date_deadline}</strong>'
                f'</li>'
            )
        html += '</ul>'
        if raw_ai_text:
            html += f'<details><summary>Analyse IA brute</summary><pre>{raw_ai_text}</pre></details>'
        return html

    def _get_record_context(self):
        """Extract context data from the source record."""
        ctx = {}
        if not self.res_model or not self.res_id:
            return ctx

        try:
            record = self.env[self.res_model].browse(self.res_id)
            if not record.exists():
                return ctx

            # Common fields
            for f in ['name', 'display_name']:
                if hasattr(record, f):
                    ctx[f] = getattr(record, f) or ''

            # Sale order fields
            if self.res_model == 'sale.order':
                ctx.update({
                    'partner_name': record.partner_id.name if record.partner_id else '',
                    'amount_total': record.amount_total or 0,
                    'state': record.state or '',
                })
                if hasattr(record, 'margin_percent'):
                    ctx['margin_percent'] = record.margin_percent or 0
                if hasattr(record, 'sale_type'):
                    ctx['sale_type'] = record.sale_type or ''
        except Exception as e:
            _logger.warning("Could not extract context from record %s %s: %s",
                            self.res_model, self.res_id, e)
        return ctx

    def _format_result_html(self, text, provider='builtin'):
        """Format AI result as HTML."""
        lines = text.split('\n') if text else []
        html_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                html_lines.append('<br/>')
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                html_lines.append(f'<li>{line[1:].strip()}</li>')
            elif line.endswith(':') and len(line) < 50:
                html_lines.append(f'<strong>{line}</strong><br/>')
            else:
                html_lines.append(f'<p>{line}</p>')

        provider_badge = (
            '<span class="badge badge-primary">IA Externe</span>'
            if provider != 'builtin'
            else '<span class="badge badge-secondary">IA Intégrée</span>'
        )
        return f'<div>{provider_badge}<hr/>{"".join(html_lines)}</div>'

    # Input
    action_type = fields.Selection([
        ('generate_description', '📝 Générer une description'),
        ('analyze', '📊 Analyser les données'),
        ('suggest_price', '💰 Suggestion de prix/remise'),
        ('suggest_action', '🎯 Prochaine action recommandée'),
        ('generate_email', '📧 Générer un email'),
        ('evaluate', '📋 Synthèse d\'évaluation'),
        ('predict', '🔮 Prédiction'),
        ('btp_conseil', '🏗️ Mohasib — Conseil fiscal/comptable'),
        ('btp_saisie', '📒 Mohasib — Écriture comptable PCM'),
        ('btp_analyse', '📊 Mohasib — Analyse financière chantier'),
        ('custom', '✏️ Requête personnalisée'),
    ], string='Action IA', required=True, default='analyze')

    custom_prompt = fields.Text(string='Requête personnalisée',
                                help="Décrivez ce que vous souhaitez que l'IA fasse")

    # Output
    ai_result = fields.Html(string='Résultat IA', readonly=True)
    ai_provider = fields.Char(string='Source', readonly=True)

    @api.onchange('action_type')
    def _onchange_action_type(self):
        if self.action_type == 'custom':
            self.custom_prompt = ''
        elif self.action_type in ('btp_conseil', 'btp_saisie'):
            self.custom_prompt = ''

    def action_generate(self):
        """Execute the AI action and display results."""
        self.ensure_one()
        mixin = self.env['ai.mixin']

        # Gather context data from the source record
        ctx = self._get_record_context()

        # Build prompt based on action type
        prompts = {
            'generate_description': f"Génère une description commerciale pour : {ctx.get('name', '')}",
            'analyze': f"Analyse complète de cet enregistrement",
            'suggest_price': f"Suggestion de prix et remise pour cette commande",
            'suggest_action': f"Quelle est la prochaine action recommandée ?",
            'generate_email': f"Génère un email de relance professionnel",
            'evaluate': f"Génère une synthèse d'évaluation",
            'predict': f"Fais une prédiction basée sur les données disponibles",
            'btp_conseil': self.custom_prompt or "Comment fonctionne la TVA BTP au Maroc ?",
            'btp_saisie': self.custom_prompt or "Comptabilise la situation de travaux",
            'btp_analyse': f"Analyse financière complète du chantier {ctx.get('name', '')}",
            'custom': self.custom_prompt or "Analyse cette situation",
        }
        prompt = prompts.get(self.action_type, self.custom_prompt)
        # Force module to 'btp' for Mohasib action types
        if self.action_type in ('btp_conseil', 'btp_saisie', 'btp_analyse'):
            module = 'btp'
        else:
            module = self.module_name or 'general'

        # Call AI
        result = mixin.ai_generate(prompt, ctx, module)

        # Format result as HTML
        text = result.get('result', 'Aucun résultat')
        html_result = self._format_result_html(text, result.get('provider', 'builtin'))

        self.write({
            'ai_result': html_result,
            'ai_provider': result.get('provider', 'builtin'),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'name': '🤖 Résultat IA',
        }

    def _get_record_context(self):
        """Extract context data from the source record."""
        ctx = {}
        if not self.res_model or not self.res_id:
            return ctx

        try:
            record = self.env[self.res_model].browse(self.res_id)
            if not record.exists():
                return ctx

            # Common fields
            for f in ['name', 'display_name']:
                if hasattr(record, f):
                    ctx[f] = getattr(record, f) or ''

            # Sale order fields
            if self.res_model == 'sale.order':
                ctx.update({
                    'partner_name': record.partner_id.name if record.partner_id else '',
                    'amount_total': record.amount_total or 0,
                    'state': record.state or '',
                })
                if hasattr(record, 'margin_percent'):
                    ctx['margin_percent'] = record.margin_percent or 0
                if hasattr(record, 'sale_type'):
                    ctx['sale_type'] = record.sale_type or ''
                # Check if returning customer
                prev_orders = self.env['sale.order'].search_count([
                    ('partner_id', '=', record.partner_id.id),
                    ('state', 'in', ['sale', 'done']),
                    ('id', '!=', record.id),
                ])
                ctx['is_returning_customer'] = prev_orders > 0

            # CRM lead fields
            elif self.res_model == 'crm.lead':
                ctx.update({
                    'expected_revenue': record.expected_revenue or 0,
                    'probability': record.probability or 0,
                })
                if hasattr(record, 'lead_quality'):
                    ctx['lead_quality'] = record.lead_quality or 'warm'
                if hasattr(record, 'days_since_last_contact'):
                    ctx['days_since_last_contact'] = record.days_since_last_contact or 0
                if hasattr(record, 'call_count'):
                    ctx['call_count'] = record.call_count or 0

            # HR evaluation fields
            elif self.res_model == 'hr.evaluation':
                if hasattr(record, 'employee_id'):
                    ctx['employee_name'] = record.employee_id.name or ''
                if hasattr(record, 'global_score'):
                    ctx['global_score'] = record.global_score or 0
                scores = {}
                for f in ['quality_score', 'productivity_score', 'initiative_score',
                           'teamwork_score', 'punctuality_score', 'communication_score']:
                    if hasattr(record, f):
                        label = f.replace('_score', '').capitalize()
                        scores[label] = getattr(record, f) or 0
                ctx['scores'] = scores

            # Account move fields
            elif self.res_model == 'account.move':
                ctx.update({
                    'partner_name': record.partner_id.name if record.partner_id else '',
                    'amount_residual': record.amount_residual or 0,
                })
                if hasattr(record, 'days_overdue'):
                    ctx['days_overdue'] = record.days_overdue or 0
                if hasattr(record, 'risk_level'):
                    ctx['risk_level'] = record.risk_level or 'low'

            # Purchase order fields
            elif self.res_model == 'purchase.order':
                ctx.update({
                    'partner_name': record.partner_id.name if record.partner_id else '',
                    'amount_total': record.amount_total or 0,
                    'state': record.state or '',
                })

            # BTP Chantier fields
            elif self.res_model == 'btp.chantier':
                ctx.update({
                    'chantier_name': record.name or '',
                    'reference': record.reference or '',
                    'montant_total': record.montant_total or 0,
                    'montant_contrat': record.montant_contrat or 0,
                    'montant_avenant': record.montant_avenant or 0,
                    'taux_avancement': record.taux_avancement or 0,
                    'retard_jours': record.retard_jours or 0,
                    'penalite_retard': record.penalite_retard or 0,
                    'state': record.state or '',
                    'type_marche': record.type_marche or '',
                    'taux_retenue_garantie': record.taux_retenue_garantie or '',
                    'montant_retenue': record.montant_retenue or 0,
                    'caution_provisoire': record.caution_provisoire or 0,
                    'caution_definitive': record.caution_definitive or 0,
                    'partner_name': record.maitre_ouvrage_id.name if record.maitre_ouvrage_id else '',
                    'client': record.maitre_ouvrage_id.name if record.maitre_ouvrage_id else '',
                    'ville': record.ville or '',
                    'situation_count': record.situation_count or 0,
                })

            # BTP Situation fields
            elif self.res_model == 'btp.situation':
                ctx.update({
                    'amount_total': getattr(record, 'montant_ht', 0) or 0,
                    'montant': getattr(record, 'montant_ht', 0) or 0,
                    'state': record.state if hasattr(record, 'state') else '',
                    'partner_name': record.chantier_id.maitre_ouvrage_id.name if hasattr(record, 'chantier_id') and record.chantier_id and record.chantier_id.maitre_ouvrage_id else '',
                    'chantier_name': record.chantier_id.name if hasattr(record, 'chantier_id') and record.chantier_id else '',
                })

            # BTP Approvisionnement fields
            elif self.res_model == 'btp.approvisionnement':
                ctx.update({
                    'amount_total': getattr(record, 'cout_total', 0) or 0,
                    'montant': getattr(record, 'cout_total', 0) or 0,
                    'state': record.state if hasattr(record, 'state') else '',
                    'partner_name': record.fournisseur_id.name if hasattr(record, 'fournisseur_id') and record.fournisseur_id else '',
                    'chantier_name': record.chantier_id.name if hasattr(record, 'chantier_id') and record.chantier_id else '',
                })

        except Exception:
            pass
        return ctx

    def _format_result_html(self, text, provider):
        """Convert plain text AI result to styled HTML."""
        # Escape HTML
        text = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Convert markdown-like formatting
        lines = text.split('\n')
        html_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                html_lines.append('<br/>')
            elif stripped.startswith('•') or stripped.startswith('-'):
                html_lines.append(f'<li style="margin-left:20px;">{stripped[1:].strip()}</li>')
            elif stripped.startswith('🔴') or stripped.startswith('⚠️'):
                html_lines.append(
                    f'<div style="padding:8px 12px;background:#fff5f5;border-left:4px solid #e74a3b;'
                    f'margin:4px 0;border-radius:4px;">{stripped}</div>')
            elif stripped.startswith('🟢') or stripped.startswith('✅'):
                html_lines.append(
                    f'<div style="padding:8px 12px;background:#f0fff4;border-left:4px solid #1cc88a;'
                    f'margin:4px 0;border-radius:4px;">{stripped}</div>')
            elif stripped.startswith('🟠') or stripped.startswith('🟡'):
                html_lines.append(
                    f'<div style="padding:8px 12px;background:#fffbeb;border-left:4px solid #f6c23e;'
                    f'margin:4px 0;border-radius:4px;">{stripped}</div>')
            elif any(stripped.startswith(e) for e in ['📊', '📈', '🎯', '📋', '💰', '📧', '📦', '💳', '📄', '📌']):
                html_lines.append(f'<h4 style="margin:12px 0 6px;color:#2c3e50;">{stripped}</h4>')
            elif stripped.startswith('🏗️'):
                html_lines.append(
                    f'<div style="padding:10px 14px;background:linear-gradient(135deg,#1e3a5f,#2c5f8a);'
                    f'color:white;border-radius:6px;margin:8px 0;font-weight:bold;font-size:14px;">'
                    f'{stripped}</div>')
            elif stripped.startswith('┌') or stripped.startswith('├') or stripped.startswith('└') or stripped.startswith('│'):
                html_lines.append(f'<pre style="margin:0;padding:0 4px;font-size:11px;'
                                  f'line-height:1.6;background:#f8f9fc;font-family:Consolas,monospace;">'
                                  f'{stripped}</pre>')
            else:
                html_lines.append(f'<p style="margin:2px 0;">{stripped}</p>')

        provider_label = '🤖 Intelligence intégrée' if provider == 'builtin' else '🌐 API IA'
        badge_color = '#36b9cc' if provider == 'builtin' else '#4e73df'

        return (
            f'<div style="font-family:Segoe UI,sans-serif;padding:16px;background:#f8f9fc;'
            f'border-radius:8px;">'
            f'<div style="display:inline-block;padding:2px 10px;background:{badge_color};'
            f'color:white;border-radius:12px;font-size:11px;margin-bottom:12px;">'
            f'{provider_label}</div>'
            f'<div style="margin-top:8px;">{"".join(html_lines)}</div>'
            f'</div>'
        )

    def action_apply(self):
        """Apply the AI suggestion to the source record (placeholder for extensions)."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
