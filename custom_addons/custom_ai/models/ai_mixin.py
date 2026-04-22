# -*- coding: utf-8 -*-
import json
import logging
import urllib.request
import urllib.error
from odoo import models, api, _

_logger = logging.getLogger(__name__)


class AIMixin(models.AbstractModel):
    """Mixin providing AI capabilities to any Odoo model.

    Usage: inherit this mixin in your model and call self.ai_generate() or
    self.ai_analyze() to get AI-powered results.  Works in two modes:
    - builtin: rule-based intelligence (always works, no API key needed)
    - api: calls OpenAI or Ollama for advanced results
    """
    _name = 'ai.mixin'
    _description = 'Mixin IA pour tous les modules'

    # =================================================================
    #  PUBLIC API
    # =================================================================
    @api.model
    def ai_generate(self, prompt, context_data=None, module='general'):
        """Generate text using AI.

        :param prompt: The user prompt / instruction
        :param context_data: dict with contextual information
        :param module: module name for builtin rules
        :returns: dict {'success': bool, 'result': str, 'provider': str}
        """
        provider = self.env['ir.config_parameter'].sudo().get_param(
            'custom_ai.provider', 'builtin')

        if provider == 'builtin':
            return self._ai_builtin_generate(prompt, context_data, module)
        else:
            return self._ai_api_generate(prompt, context_data)

    @api.model
    def ai_analyze(self, data, analysis_type='general', module='general'):
        """Analyze data and return insights.

        :param data: dict with data to analyze
        :param analysis_type: type of analysis (trend, prediction, scoring, etc.)
        :param module: module name for builtin rules
        :returns: dict with analysis results
        """
        provider = self.env['ir.config_parameter'].sudo().get_param(
            'custom_ai.provider', 'builtin')

        if provider == 'builtin':
            return self._ai_builtin_analyze(data, analysis_type, module)
        else:
            prompt = self._build_analysis_prompt(data, analysis_type, module)
            return self._ai_api_generate(prompt, data)

    @api.model
    def ai_suggest(self, record_data, suggestion_type='general', module='general'):
        """Get AI suggestions for a record.

        :param record_data: dict with record information
        :param suggestion_type: type of suggestions needed
        :param module: module name for builtin rules
        :returns: dict with suggestions
        """
        provider = self.env['ir.config_parameter'].sudo().get_param(
            'custom_ai.provider', 'builtin')

        if provider == 'builtin':
            return self._ai_builtin_suggest(record_data, suggestion_type, module)
        else:
            prompt = self._build_suggest_prompt(record_data, suggestion_type, module)
            return self._ai_api_generate(prompt, record_data)

    # =================================================================
    #  API-BASED GENERATION (OpenAI / Ollama)
    # =================================================================
    @api.model
    def _ai_api_generate(self, prompt, context_data=None):
        """Call external AI API."""
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('custom_ai.api_key', '')
        api_url = ICP.get_param('custom_ai.api_url', 'https://api.openai.com/v1')
        model = ICP.get_param('custom_ai.model', 'gpt-3.5-turbo')
        temperature = float(ICP.get_param('custom_ai.temperature', '0.7'))

        if not api_key:
            _logger.warning("AI API key not configured, falling back to builtin")
            return self._ai_builtin_generate(prompt, context_data, 'general')

        system_msg = (
            "Tu es un assistant IA expert intégré dans un ERP commercial marocain. "
            "Tu assistes les utilisateurs en :\n"
            "- ventes, CRM et relation client\n"
            "- achats et gestion des fournisseurs\n"
            "- comptabilité selon le PCM marocain (TVA 20%, IS, IR, retenues a la source)\n"
            "- gestion de stock et inventaire\n"
            "- ressources humaines\n"
            "- gestion de chantier BTP\n\n"
            "Regles :\n"
            "1. Reponds TOUJOURS en francais, de maniere concise et professionnelle.\n"
            "2. Adapte ta reponse au contexte fourni (module, données de l'enregistrement).\n"
            "3. Pour les montants, utilise MAD (dirham marocain).\n"
            "4. Pour les ecritures comptables, utilise le Plan Comptable Marocain (PCM classes 1 a 8).\n"
            "5. Donne des recommandations concretes et actionnables.\n"
            "6. Si peu de contexte, reste general mais utile.\n"
        )

        messages = [
            {"role": "system", "content": system_msg},
        ]
        if context_data:
            messages.append({
                "role": "user",
                "content": f"Contexte: {json.dumps(context_data, ensure_ascii=False, default=str)}"
            })
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000,
        }).encode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        url = f"{api_url.rstrip('/')}/chat/completions"

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                text = result['choices'][0]['message']['content'].strip()
                return {'success': True, 'result': text, 'provider': 'api'}
        except urllib.error.HTTPError as e:
            _logger.error("AI API HTTP error: %s", e.read().decode() if e.fp else str(e))
            return {'success': False, 'result': f"Erreur API: {e.code}", 'provider': 'api'}
        except Exception as e:
            _logger.error("AI API error: %s", str(e))
            return {'success': False, 'result': f"Erreur: {str(e)}", 'provider': 'api'}

    # =================================================================
    #  BUILTIN INTELLIGENCE (Rule-based, always works)
    # =================================================================
    @api.model
    def _ai_builtin_generate(self, prompt, context_data=None, module='general'):
        """Rule-based text generation."""
        prompt_lower = (prompt or '').lower()
        ctx = context_data or {}
        result = ''

        # --- SALE module ---
        if module == 'sale' or 'vente' in prompt_lower or 'devis' in prompt_lower:
            name = ctx.get('product_name', ctx.get('name', ''))
            amount = ctx.get('amount_total', 0)
            partner = ctx.get('partner_name', '')
            if 'description' in prompt_lower or 'produit' in prompt_lower:
                result = self._gen_product_description(name)
            elif 'prix' in prompt_lower or 'remise' in prompt_lower or 'discount' in prompt_lower:
                result = self._gen_price_suggestion(ctx)
            elif 'relance' in prompt_lower or 'email' in prompt_lower:
                result = self._gen_sale_followup(ctx)
            else:
                result = (
                    f"📊 Analyse de la commande :\n"
                    f"• Client : {partner}\n"
                    f"• Montant : {amount:,.2f} MAD\n"
                    f"• Recommandation : "
                )
                if amount > 50000:
                    result += "Commande importante - proposer des conditions de paiement avantageuses."
                elif amount > 10000:
                    result += "Commande significative - vérifier la disponibilité stock."
                else:
                    result += "Commande standard - traitement priorité normale."

        # --- CRM module ---
        elif module == 'crm' or 'lead' in prompt_lower or 'prospect' in prompt_lower:
            result = self._gen_crm_analysis(ctx)

        # --- HR module ---
        elif module == 'hr' or 'évaluation' in prompt_lower or 'employé' in prompt_lower:
            result = self._gen_hr_evaluation(ctx)

        # --- Accounting ---
        elif module == 'accounting' or 'facture' in prompt_lower or 'paiement' in prompt_lower:
            result = self._gen_accounting_analysis(ctx)

        # --- Stock ---
        elif module == 'stock' or 'stock' in prompt_lower or 'inventaire' in prompt_lower:
            result = self._gen_stock_analysis(ctx)

        # --- BTP / Mohasib ---
        elif module == 'btp' or 'chantier' in prompt_lower or 'btp' in prompt_lower:
            result = self._gen_btp_mohasib(prompt, prompt_lower, ctx)

        # --- Moroccan accounting questions (Mohasib) ---
        elif any(kw in prompt_lower for kw in [
            'tva', 'is ', 'ir ', 'impôt', 'impot', 'retenue', 'pcm',
            'comptab', 'fiscal', 'taxe', 'caution', 'garantie',
            'décompte', 'decompte', 'situation', 'attachement',
            'écriture', 'ecriture', 'journal', 'compte',
        ]):
            result = self._gen_btp_mohasib(prompt, prompt_lower, ctx)

        # --- General fallback ---
        else:
            result = (
                f"🤖 Assistant IA — ERP Commercial\n\n"
                f"Module : {module} | Contexte : {ctx.get('display_name', ctx.get('name', 'N/A'))}\n\n"
                "Je suis votre assistant IA intégré. Je peux vous aider avec :\n"
                "• 📊 Analyse d'enregistrements (clients, commandes, factures...)\n"
                "• 🎯 Recommandations d'actions prioritaires\n"
                "• 💰 Suggestions de prix et conditions\n"
                "• 📧 Rédaction d'emails professionnels\n"
                "• 📒 Conseil comptable et fiscal (PCM marocain)\n"
                "• 🎙️ Création d'activités par commande vocale\n\n"
                "💡 Pour des analyses avancées avec GPT-4 ou un modèle local (Ollama),\n"
                "configurez votre clé API dans : Paramètres > Intelligence Artificielle."
            )

        return {'success': True, 'result': result, 'provider': 'builtin'}

    @api.model
    def _ai_builtin_analyze(self, data, analysis_type, module):
        """Rule-based data analysis."""
        result = {}
        if analysis_type == 'scoring' and module == 'crm':
            result = self._analyze_lead_scoring(data)
        elif analysis_type == 'prediction' and module == 'accounting':
            result = self._analyze_payment_prediction(data)
        elif analysis_type == 'forecast' and module == 'stock':
            result = self._analyze_stock_forecast(data)
        elif analysis_type == 'trend':
            result = self._analyze_trend(data)
        else:
            result = {'score': 50, 'confidence': 'medium',
                      'insight': 'Analyse basique effectuée. Configurez l\'API IA pour des analyses avancées.'}
        return {'success': True, 'result': result, 'provider': 'builtin'}

    @api.model
    def _ai_builtin_suggest(self, record_data, suggestion_type, module):
        """Rule-based suggestions."""
        suggestions = []
        if module == 'sale':
            suggestions = self._suggest_sale(record_data)
        elif module == 'crm':
            suggestions = self._suggest_crm(record_data)
        elif module == 'hr':
            suggestions = self._suggest_hr(record_data)
        elif module == 'purchase':
            suggestions = self._suggest_purchase(record_data)
        else:
            suggestions = [{'type': 'info', 'text': 'Aucune suggestion spécifique disponible.'}]
        return {'success': True, 'result': suggestions, 'provider': 'builtin'}

    # =================================================================
    #  BUILTIN GENERATORS
    # =================================================================
    @api.model
    def _gen_product_description(self, name):
        name = name or 'Produit'
        return (
            f"📝 Description générée pour « {name} » :\n\n"
            f"{name} — Solution professionnelle de qualité supérieure conçue pour "
            f"répondre aux exigences les plus élevées de votre entreprise.\n\n"
            f"✅ Caractéristiques clés :\n"
            f"• Performance et fiabilité garanties\n"
            f"• Conforme aux normes en vigueur\n"
            f"• Support technique inclus\n\n"
            f"💡 Conseil IA : Personnalisez cette description avec les "
            f"spécificités techniques de votre {name.lower()}."
        )

    @api.model
    def _gen_price_suggestion(self, ctx):
        amount = ctx.get('amount_total', 0)
        margin = ctx.get('margin_percent', 0)
        partner = ctx.get('partner_name', 'Client')
        is_returning = ctx.get('is_returning_customer', False)
        result = f"💰 Suggestion de prix pour {partner} :\n\n"
        if is_returning:
            result += "🔄 Client fidèle — remise recommandée : 5-10%\n"
        if amount > 100000:
            result += "📦 Commande volumineuse — remise volume : 3-7%\n"
        if margin and margin < 15:
            result += f"⚠️ Marge actuelle ({margin:.1f}%) faible — éviter des remises supplémentaires\n"
        elif margin and margin > 40:
            result += f"✅ Marge confortable ({margin:.1f}%) — marge de négociation disponible\n"
        result += "\n💡 Conseil : Privilégiez des avantages non-monétaires (livraison gratuite, extension garantie)."
        return result

    @api.model
    def _gen_sale_followup(self, ctx):
        partner = ctx.get('partner_name', 'Client')
        ref = ctx.get('name', 'Devis')
        amount = ctx.get('amount_total', 0)
        return (
            f"📧 Email de relance suggéré :\n\n"
            f"Objet : Suivi de votre devis {ref}\n\n"
            f"Bonjour,\n\n"
            f"Je me permets de revenir vers vous concernant le devis {ref} "
            f"d'un montant de {amount:,.2f} MAD que nous vous avons adressé.\n\n"
            f"Avez-vous eu l'occasion de l'examiner ? Je reste à votre "
            f"entière disposition pour toute question ou ajustement.\n\n"
            f"Cordialement"
        )

    @api.model
    def _gen_crm_analysis(self, ctx):
        name = ctx.get('name', 'Opportunité')
        revenue = ctx.get('expected_revenue', 0)
        prob = ctx.get('probability', 0)
        days = ctx.get('days_since_last_contact', 0)
        quality = ctx.get('lead_quality', 'warm')

        result = f"🎯 Analyse IA du lead « {name} » :\n\n"
        # Scoring
        score = 50
        if revenue > 100000:
            score += 20
            result += "✅ Potentiel élevé (> 100K MAD)\n"
        elif revenue > 20000:
            score += 10
            result += "📊 Potentiel moyen (20-100K MAD)\n"
        if prob > 50:
            score += 15
            result += f"✅ Probabilité favorable ({prob}%)\n"
        if quality == 'hot':
            score += 15
            result += "🔥 Lead chaud — action immédiate recommandée\n"
        if days > 14:
            score -= 10
            result += f"⚠️ {days} jours sans contact — risque de perte\n"
        elif days > 7:
            score -= 5
            result += f"📞 {days} jours sans contact — relance conseillée\n"

        score = max(0, min(100, score))
        result += f"\n📈 Score IA : {score}/100\n"

        # Next action
        result += "\n🎬 Prochaine action recommandée : "
        if days > 14:
            result += "APPEL URGENT - Recontacter le prospect immédiatement"
        elif quality == 'hot':
            result += "Planifier une démo / présentation commerciale"
        elif prob > 70:
            result += "Préparer une proposition commerciale"
        else:
            result += "Envoyer du contenu éducatif / cas client"

        return result

    @api.model
    def _gen_hr_evaluation(self, ctx):
        name = ctx.get('employee_name', 'Collaborateur')
        scores = ctx.get('scores', {})
        global_score = ctx.get('global_score', 0)

        result = f"📋 Synthèse d'évaluation — {name}\n\n"

        if global_score >= 8:
            result += "🌟 Performance excellente — Profil à fort potentiel\n\n"
        elif global_score >= 6:
            result += "✅ Performance satisfaisante — Progression régulière\n\n"
        elif global_score >= 4:
            result += "⚠️ Performance à améliorer — Accompagnement nécessaire\n\n"
        else:
            result += "🔴 Performance insuffisante — Plan d'action urgent\n\n"

        # Strengths & weaknesses
        if scores:
            strengths = [k for k, v in scores.items() if v >= 7]
            weaknesses = [k for k, v in scores.items() if v < 5]
            if strengths:
                result += "💪 Points forts : " + ", ".join(strengths) + "\n"
            if weaknesses:
                result += "📈 Axes d'amélioration : " + ", ".join(weaknesses) + "\n"

        result += f"\n🎯 Objectifs suggérés :\n"
        if global_score < 6:
            result += "• Formation technique ciblée sur les compétences en retrait\n"
            result += "• Mentorat avec un collaborateur senior\n"
            result += "• Point de suivi bi-mensuel\n"
        else:
            result += "• Prendre en charge un projet transversal\n"
            result += "• Mentorer un junior\n"
            result += "• Explorer une certification professionnelle\n"

        return result

    @api.model
    def _gen_accounting_analysis(self, ctx):
        partner = ctx.get('partner_name', 'Client')
        amount = ctx.get('amount_residual', 0)
        days_overdue = ctx.get('days_overdue', 0)
        risk = ctx.get('risk_level', 'low')

        result = f"💳 Analyse IA — Facture {partner}\n\n"
        result += f"• Montant restant : {amount:,.2f} MAD\n"
        result += f"• Retard : {days_overdue} jours\n"
        result += f"• Niveau de risque : {risk}\n\n"

        if days_overdue > 60:
            result += "🔴 Action : Mise en demeure recommandée\n"
            result += "Prédiction : probabilité de paiement < 40%\n"
        elif days_overdue > 30:
            result += "🟠 Action : Relance téléphonique personnalisée\n"
            result += "Prédiction : paiement probable sous 15 jours avec relance\n"
        elif days_overdue > 7:
            result += "🟡 Action : Email de rappel courtois\n"
            result += "Prédiction : paiement probable sous 7 jours\n"
        else:
            result += "🟢 Facture récente — Pas d'action nécessaire\n"

        return result

    @api.model
    def _gen_stock_analysis(self, ctx):
        product = ctx.get('product_name', 'Produit')
        qty = ctx.get('qty_available', 0)
        avg_daily = ctx.get('avg_daily_usage', 0)

        result = f"📦 Analyse Stock IA — {product}\n\n"
        result += f"• Quantité en stock : {qty}\n"

        if avg_daily > 0:
            days_remaining = qty / avg_daily if qty > 0 else 0
            result += f"• Consommation moyenne : {avg_daily:.1f}/jour\n"
            result += f"• Jours de stock restants : {days_remaining:.0f}\n\n"
            if days_remaining < 7:
                result += "🔴 ALERTE : Réapprovisionnement URGENT\n"
                result += f"• Quantité suggérée : {avg_daily * 30:.0f} unités (1 mois)\n"
            elif days_remaining < 14:
                result += "🟠 Attention : Stock bas — Commande recommandée sous 48h\n"
                result += f"• Quantité suggérée : {avg_daily * 30:.0f} unités (1 mois)\n"
            else:
                result += "🟢 Stock suffisant\n"
        else:
            result += "• Pas de données de consommation disponibles\n"
            result += "💡 Conseil : Alimentez l'historique pour de meilleures prédictions\n"

        return result

    # =================================================================
    #  BUILTIN ANALYZERS
    # =================================================================
    @api.model
    def _analyze_lead_scoring(self, data):
        score = 50
        factors = []
        revenue = data.get('expected_revenue', 0)
        prob = data.get('probability', 0)
        days = data.get('days_since_last_contact', 0)
        calls = data.get('call_count', 0)
        meetings = data.get('meeting_count', 0)

        if revenue > 100000: score += 20; factors.append('Potentiel élevé (+20)')
        elif revenue > 20000: score += 10; factors.append('Potentiel moyen (+10)')
        if prob > 70: score += 15; factors.append('Forte probabilité (+15)')
        elif prob > 40: score += 5; factors.append('Probabilité moyenne (+5)')
        if calls >= 3: score += 5; factors.append('Engagement par appels (+5)')
        if meetings >= 1: score += 10; factors.append('Réunion effectuée (+10)')
        if days > 21: score -= 15; factors.append('Inactivité prolongée (-15)')
        elif days > 7: score -= 5; factors.append('Contact récent insuffisant (-5)')

        score = max(0, min(100, score))
        return {'score': score, 'factors': factors,
                'confidence': 'high' if len(factors) >= 4 else 'medium',
                'recommendation': 'Prioriser' if score >= 70 else 'Suivre' if score >= 40 else 'Qualifier'}

    @api.model
    def _analyze_payment_prediction(self, data):
        days_overdue = data.get('days_overdue', 0)
        amount = data.get('amount_residual', 0)
        history_avg = data.get('avg_payment_delay', 0)

        if days_overdue > 90:
            prob = 20
        elif days_overdue > 60:
            prob = 40
        elif days_overdue > 30:
            prob = 60
        elif days_overdue > 0:
            prob = 80
        else:
            prob = 95

        return {
            'payment_probability': prob,
            'estimated_days': max(0, int(history_avg * 1.2)) if history_avg else days_overdue + 15,
            'risk': 'high' if prob < 50 else 'medium' if prob < 80 else 'low',
        }

    @api.model
    def _analyze_stock_forecast(self, data):
        qty = data.get('qty_available', 0)
        avg_daily = data.get('avg_daily_usage', 0)
        lead_time = data.get('lead_time_days', 7)

        days_remaining = (qty / avg_daily) if avg_daily > 0 else 999
        reorder_point = avg_daily * (lead_time + 3)  # safety stock = 3 days
        suggested_qty = avg_daily * 30  # 1 month supply

        return {
            'days_remaining': round(days_remaining),
            'reorder_point': round(reorder_point),
            'suggested_qty': round(suggested_qty),
            'urgency': 'critical' if days_remaining < lead_time else
                       'warning' if days_remaining < lead_time * 2 else 'ok',
        }

    @api.model
    def _analyze_trend(self, data):
        values = data.get('values', [])
        if len(values) < 2:
            return {'trend': 'stable', 'change': 0}
        recent = sum(values[-3:]) / min(3, len(values))
        older = sum(values[:-3]) / max(1, len(values) - 3) if len(values) > 3 else values[0]
        change = ((recent - older) / older * 100) if older else 0
        return {
            'trend': 'up' if change > 5 else 'down' if change < -5 else 'stable',
            'change_percent': round(change, 1),
        }

    # =================================================================
    #  BUILTIN SUGGESTERS
    # =================================================================
    @api.model
    def _suggest_sale(self, data):
        suggestions = []
        amount = data.get('amount_total', 0)
        margin = data.get('margin_percent', 0)
        if amount > 50000:
            suggestions.append({'type': 'success', 'icon': 'fa-handshake-o',
                                'text': 'Proposer un échéancier de paiement pour ce montant important'})
        if margin and margin < 15:
            suggestions.append({'type': 'warning', 'icon': 'fa-exclamation',
                                'text': f'Marge faible ({margin:.1f}%) - Vérifier les prix unitaires'})
        if margin and margin > 40:
            suggestions.append({'type': 'info', 'icon': 'fa-gift',
                                'text': 'Marge confortable - Possibilité d\'offrir un geste commercial'})
        suggestions.append({'type': 'info', 'icon': 'fa-cart-plus',
                            'text': 'Proposer des produits complémentaires pour augmenter le panier'})
        return suggestions

    @api.model
    def _suggest_crm(self, data):
        suggestions = []
        days = data.get('days_since_last_contact', 0)
        quality = data.get('lead_quality', 'warm')
        prob = data.get('probability', 0)
        if days > 14:
            suggestions.append({'type': 'danger', 'icon': 'fa-phone',
                                'text': 'Contact urgent — Plus de 2 semaines sans interaction'})
        if quality == 'hot':
            suggestions.append({'type': 'success', 'icon': 'fa-calendar',
                                'text': 'Lead chaud — Planifier une démo immédiatement'})
        if prob > 70:
            suggestions.append({'type': 'info', 'icon': 'fa-file-text',
                                'text': 'Forte probabilité — Préparer une proposition commerciale'})
        suggestions.append({'type': 'info', 'icon': 'fa-envelope',
                            'text': 'Envoyer un contenu personnalisé (étude de cas, témoignage)'})
        return suggestions

    @api.model
    def _suggest_hr(self, data):
        suggestions = []
        score = data.get('global_score', 0)
        scores = data.get('scores', {})
        if score >= 8:
            suggestions.append({'type': 'success', 'icon': 'fa-trophy',
                                'text': 'Excellent profil — Envisager une promotion ou augmentation'})
        elif score < 5:
            suggestions.append({'type': 'danger', 'icon': 'fa-exclamation-triangle',
                                'text': 'Performance insuffisante — Mettre en place un plan d\'amélioration'})
        for criterion, val in scores.items():
            if val < 4:
                suggestions.append({'type': 'warning', 'icon': 'fa-graduation-cap',
                                    'text': f'Formation recommandée en {criterion}'})
        return suggestions or [{'type': 'info', 'icon': 'fa-check', 'text': 'Aucune action urgente'}]

    @api.model
    def _suggest_purchase(self, data):
        suggestions = []
        amount = data.get('amount_total', 0)
        if amount > 100000:
            suggestions.append({'type': 'info', 'icon': 'fa-percent',
                                'text': 'Négocier une remise volume sur cette commande importante'})
        suggestions.append({'type': 'info', 'icon': 'fa-balance-scale',
                            'text': 'Comparer avec au moins 3 fournisseurs pour les meilleurs tarifs'})
        suggestions.append({'type': 'info', 'icon': 'fa-calendar-check-o',
                            'text': 'Vérifier les délais de livraison du fournisseur'})
        return suggestions

    # =================================================================
    #  MOHASIB — Expert-Comptable BTP Maroc (Builtin)
    # =================================================================
    @api.model
    def _gen_btp_mohasib(self, prompt, prompt_lower, ctx):
        """Mohasib: Expert-comptable marocain spécialisé BTP.
        Détecte l'intention (CONSEIL vs SAISIE COMPTABLE) et répond."""

        # --- Intent detection ---
        is_question = any(kw in prompt_lower for kw in [
            '?', 'comment', 'pourquoi', 'est-ce', 'est ce', 'quand',
            'quel', 'quelle', 'quels', 'quelles', 'combien',
            'explique', 'c\'est quoi', 'différence', 'difference',
            'obligation', 'dois-je', 'faut-il', 'peut-on',
        ])
        is_entry = any(kw in prompt_lower for kw in [
            'paiement', 'facture', 'encaissement', 'achat', 'salaire',
            'écriture', 'ecriture', 'comptabilise', 'enregistre',
            'règlement', 'reglement', 'virement', 'chèque', 'cheque',
            'décompte', 'decompte', 'situation', 'caution',
            'retenue de garantie', 'avance', 'acompte',
        ])

        if is_question and not is_entry:
            return self._mohasib_conseil(prompt_lower, ctx)
        elif is_entry and not is_question:
            return self._mohasib_saisie(prompt_lower, ctx)
        elif is_entry and is_question:
            # Both detected: question about an operation → CONSEIL
            return self._mohasib_conseil(prompt_lower, ctx)
        else:
            # Ambiguous - try BTP chantier analysis if context available
            if ctx.get('chantier_name') or ctx.get('name'):
                return self._mohasib_analyse_chantier(ctx)
            return (
                "🏗️ Mohasib — Expert-Comptable BTP\n\n"
                "Je n'ai pas bien compris votre demande. "
                "Précisez-moi :\n\n"
                "📌 S'agit-il d'une **question** sur la réglementation ?\n"
                "   → Je vous donnerai un CONSEIL clair.\n\n"
                "📌 Ou d'une **opération** à comptabiliser ?\n"
                "   → Je produirai l'ÉCRITURE COMPTABLE selon le PCM.\n\n"
                "Exemples :\n"
                "• « Comment fonctionne la retenue de garantie BTP ? »\n"
                "• « Comptabilise le paiement de la situation n°3 du chantier X, "
                "montant 500 000 MAD HT, TVA 20% »"
            )

    @api.model
    def _mohasib_conseil(self, prompt_lower, ctx):
        """Mode CONSEIL: répondre selon la réglementation marocaine."""
        result = "🏗️ Mohasib — Mode CONSEIL\n\n"

        # --- TVA BTP ---
        if 'tva' in prompt_lower:
            result += (
                "📋 TVA dans le secteur BTP au Maroc\n\n"
                "• Taux normal : 20% (travaux de construction)\n"
                "• Taux réduit 14% : travaux immobiliers pour logement social\n"
                "• Taux réduit 10% : certaines opérations de promotion immobilière\n"
                "• Exonération : exportation de services BTP\n\n"
                "📌 Cas d'application BTP :\n"
                "• Les décomptes provisoires et définitifs sont soumis à la TVA\n"
                "• La retenue de garantie (10%) est soumise à la TVA\n"
                "• Les avances sur marchés sont soumises à la TVA\n"
                "• Le maître d'ouvrage public verse la TVA à l'État "
                "(mécanisme d'autoliquidation pour les marchés publics)\n\n"
                "⚠️ Fait générateur : encaissement (régime de droit commun) "
                "ou débit (sur option)\n\n"
                "✅ Conclusion : Appliquez 20% sur vos décomptes sauf cas spécifiques. "
                "Vérifiez le cahier des charges pour le régime applicable."
            )

        # --- IS ---
        elif any(kw in prompt_lower for kw in ['is ', 'impôt sur les sociétés', 'impot sur les societes']):
            result += (
                "📋 Impôt sur les Sociétés (IS) — Entreprise BTP\n\n"
                "Barème progressif (Loi de Finances) :\n"
                "• Bénéfice ≤ 300 000 MAD → 10%\n"
                "• 300 001 à 1 000 000 MAD → 20%\n"
                "• 1 000 001 à 100 000 000 MAD → 31%\n"
                "• > 100 000 000 MAD → 35%\n\n"
                "📌 Particularités BTP :\n"
                "• Cotisation minimale : 0,50% du CA (min 3 000 MAD)\n"
                "• Provisions pour risques de chantier : déductibles si justifiées\n"
                "• Provisions pour garantie décennale : déductibles\n"
                "• Les pénalités de retard subies ne sont PAS déductibles fiscalement\n\n"
                "✅ Conclusion : Planifiez vos acomptes IS trimestriellement "
                "et provisionnez vos risques chantier."
            )

        # --- IR / Salaires ---
        elif any(kw in prompt_lower for kw in ['ir ', 'salaire', 'paie', 'revenu']):
            result += (
                "📋 IR sur salaires — Personnel BTP au Maroc\n\n"
                "Barème annuel IR :\n"
                "• 0 à 30 000 MAD → Exonéré\n"
                "• 30 001 à 50 000 → 10%\n"
                "• 50 001 à 60 000 → 20%\n"
                "• 60 001 à 80 000 → 30%\n"
                "• 80 001 à 180 000 → 34%\n"
                "• > 180 000 → 38%\n\n"
                "📌 Spécificités BTP :\n"
                "• Indemnités de déplacement chantier : exonérées (justifiées)\n"
                "• Prime de panier : exonérée jusqu'à 20 MAD/jour\n"
                "• Indemnité d'outillage : exonérée si justifiée\n"
                "• Heures supplémentaires : majoration 25% (jour), 50% (nuit/weekend)\n"
                "• CNSS employeur : 26,60% (dont AMO)\n"
                "• CNSS salarié : 6,74%\n\n"
                "✅ Conclusion : Gérez séparément les indemnités exonérées "
                "pour optimiser la charge fiscale."
            )

        # --- Retenue à la source ---
        elif any(kw in prompt_lower for kw in ['retenue à la source', 'retenue a la source', 'ras']):
            result += (
                "📋 Retenue à la Source (RAS) — BTP Maroc\n\n"
                "• Taux standard : 10% sur les honoraires et prestations\n"
                "• Marchés publics : RAS de 10% sur rémunération des non-résidents\n"
                "• Revenus fonciers : 15%\n\n"
                "📌 Application BTP :\n"
                "• Sous-traitance : vérifiez si le sous-traitant est assujetti\n"
                "• Location d'engins : RAS si le loueur est personne physique\n"
                "• Bureau d'études : RAS de 10%\n\n"
                "✅ Conclusion : Pratiquez la RAS et déclarez trimestriellement. "
                "Conservez les attestations."
            )

        # --- Retenue de garantie ---
        elif any(kw in prompt_lower for kw in ['retenue de garantie', 'garantie']):
            result += (
                "📋 Retenue de Garantie — Marchés BTP\n\n"
                "• Taux : généralement 10% du montant de chaque décompte\n"
                "• But : garantir la bonne exécution et la levée des réserves\n"
                "• Durée : retenue jusqu'à la réception définitive (1 an après réception provisoire)\n"
                "• Substitution : peut être remplacée par une caution bancaire\n\n"
                "📌 Comptabilisation (PCM) :\n"
                "• Lors de la facturation : enregistrer en 3424 « Clients, retenues de garantie »\n"
                "• Lors de la libération : solder le 3424 par la trésorerie (5141)\n\n"
                "⚠️ La retenue de garantie est soumise à la TVA au moment de la facturation, "
                "pas au moment de la libération.\n\n"
                "✅ Conclusion : Suivez chaque retenue par chantier et "
                "planifiez la caution bancaire si besoin de trésorerie."
            )

        # --- Caution ---
        elif 'caution' in prompt_lower:
            result += (
                "📋 Cautions Bancaires BTP — Maroc\n\n"
                "Types de cautions :\n"
                "• Caution provisoire : 1,5% du montant estimé du marché\n"
                "• Caution définitive : 3% du montant du marché\n"
                "• Caution de retenue de garantie : 10% (substitution)\n"
                "• Caution d'avance : 100% du montant de l'avance\n\n"
                "📌 Comptabilisation (PCM) :\n"
                "• Compte 5141 - Banque (débit des frais de dossier)\n"
                "• Compte 6147 - Services bancaires (commissions)\n"
                "• Hors bilan : engagement donné (classe 0)\n\n"
                "✅ Conclusion : Provisionnez les commissions bancaires "
                "et suivez les dates d'échéance des cautions."
            )

        # --- PCM general ---
        elif 'pcm' in prompt_lower or 'plan comptable' in prompt_lower:
            result += (
                "📋 Plan Comptable Marocain (PCM) — Comptes BTP courants\n\n"
                "Classe 1 — Financement permanent :\n"
                "• 1111 : Capital social\n"
                "• 1481 : Emprunts\n"
                "• 1511 : Provisions pour litiges chantier\n\n"
                "Classe 2 — Actif immobilisé :\n"
                "• 2332 : Matériel et outillage BTP\n"
                "• 2340 : Matériel de transport\n"
                "• 2380 : Installations de chantier\n\n"
                "Classe 3 — Actif circulant :\n"
                "• 3121 : Matières premières (ciment, acier...)\n"
                "• 3421 : Clients\n"
                "• 3424 : Clients, retenues de garantie\n"
                "• 3425 : Clients, décomptes à établir\n"
                "• 34551 : État TVA récupérable\n\n"
                "Classe 4 — Passif circulant :\n"
                "• 4411 : Fournisseurs\n"
                "• 4437 : RAS à reverser\n"
                "• 4455 : État TVA facturée\n"
                "• 4457 : État IS\n\n"
                "Classe 5 — Trésorerie :\n"
                "• 5141 : Banque\n"
                "• 5161 : Caisse\n\n"
                "Classe 6 — Charges :\n"
                "• 6121 : Achats matières premières\n"
                "• 6125 : Achats de sous-traitance\n"
                "• 6131 : Location matériel\n"
                "• 6142 : Transport\n"
                "• 6171 : Salaires personnel chantier\n\n"
                "Classe 7 — Produits :\n"
                "• 7111 : Travaux facturés\n"
                "• 7118 : Travaux en cours (production stockée)\n\n"
                "✅ Conclusion : Utilisez des sous-comptes analytiques par chantier."
            )

        # --- Décompte / Situation ---
        elif any(kw in prompt_lower for kw in ['décompte', 'decompte', 'situation']):
            result += (
                "📋 Décomptes et Situations — Gestion BTP\n\n"
                "Un décompte (ou situation) est le document de facturation progressive "
                "d'un marché BTP.\n\n"
                "📌 Types :\n"
                "• Décompte provisoire : facturation mensuelle des travaux réalisés\n"
                "• Décompte définitif : solde final après réception\n"
                "• Décompte général et définitif (DGD) : arrêt des comptes\n\n"
                "📌 Éléments d'un décompte :\n"
                "• Montant brut HT des travaux\n"
                "• - Retenue de garantie (10%)\n"
                "• - Avance remboursée (prorata)\n"
                "• + TVA (20%)\n"
                "• - Retenue à la source (si applicable)\n"
                "• = Net à payer\n\n"
                "✅ Conclusion : Chaque situation doit être rattachée au chantier "
                "et validée par le maître d'œuvre."
            )

        # --- Generic BTP question ---
        else:
            chantier = ctx.get('chantier_name', ctx.get('name', ''))
            if chantier:
                result += self._mohasib_analyse_chantier(ctx)
            else:
                result += (
                    "Je suis Mohasib, votre expert-comptable BTP.\n\n"
                    "Posez-moi une question précise sur :\n"
                    "• TVA BTP (taux, fait générateur, autoliquidation)\n"
                    "• IS (barème, cotisation minimale, provisions)\n"
                    "• IR / Salaires (barème, indemnités exonérées, CNSS)\n"
                    "• Retenues à la source\n"
                    "• Retenue de garantie (comptabilisation, libération)\n"
                    "• Cautions bancaires BTP\n"
                    "• Plan Comptable Marocain (comptes BTP)\n"
                    "• Décomptes et situations\n\n"
                    "Ou décrivez une opération à comptabiliser."
                )
        return result

    @api.model
    def _mohasib_saisie(self, prompt_lower, ctx):
        """Mode SAISIE COMPTABLE: générer des écritures PCM."""
        result = "🏗️ Mohasib — Mode SAISIE COMPTABLE (PCM)\n\n"

        amount = ctx.get('amount_total', ctx.get('montant', 0))
        partner = ctx.get('partner_name', ctx.get('client', 'Client'))

        # --- Paiement situation / décompte ---
        if any(kw in prompt_lower for kw in ['décompte', 'decompte', 'situation']):
            ht = amount if amount else 100000
            tva = ht * 0.20
            rg = ht * 0.10  # retenue de garantie
            net = ht + tva - rg
            result += (
                f"📄 Écriture : Facturation situation de travaux\n"
                f"   Montant HT : {ht:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 3421       │ Clients                      │ {net:>12,.2f} │              │\n"
                f"│ 3424       │ Clients, retenue de garantie │ {rg:>12,.2f} │              │\n"
                f"│ 7111       │ Travaux facturés             │              │ {ht:>12,.2f} │\n"
                f"│ 4455       │ État, TVA facturée           │              │ {tva:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Situation de travaux — {partner}"
            )

        # --- Encaissement ---
        elif any(kw in prompt_lower for kw in ['encaissement', 'reçu', 'versement']):
            montant = amount if amount else 50000
            result += (
                f"📄 Écriture : Encaissement client\n"
                f"   Montant : {montant:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 5141       │ Banque                       │ {montant:>12,.2f} │              │\n"
                f"│ 3421       │ Clients                      │              │ {montant:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Encaissement — {partner}"
            )

        # --- Achat matériaux ---
        elif any(kw in prompt_lower for kw in ['achat', 'fournisseur', 'matéri', 'materi']):
            ht = amount if amount else 50000
            tva = ht * 0.20
            ttc = ht + tva
            result += (
                f"📄 Écriture : Achat matériaux/fournitures chantier\n"
                f"   Montant HT : {ht:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 6121       │ Achats matières premières     │ {ht:>12,.2f} │              │\n"
                f"│ 34551      │ État, TVA récupérable         │ {tva:>12,.2f} │              │\n"
                f"│ 4411       │ Fournisseurs                 │              │ {ttc:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Achat matériaux — {partner}"
            )

        # --- Salaire ---
        elif any(kw in prompt_lower for kw in ['salaire', 'paie', 'rémunération', 'remuneration']):
            brut = amount if amount else 8000
            cnss_sal = brut * 0.0674
            ir_approx = max(0, (brut - cnss_sal - 2500) * 0.10)  # simplified
            net = brut - cnss_sal - ir_approx
            cnss_pat = brut * 0.2660
            result += (
                f"📄 Écriture : Paie mensuelle personnel chantier\n"
                f"   Salaire brut : {brut:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 6171       │ Salaires personnel chantier  │ {brut:>12,.2f} │              │\n"
                f"│ 6174       │ Charges sociales (patronales)│ {cnss_pat:>12,.2f} │              │\n"
                f"│ 4441       │ CNSS salarié                 │              │ {cnss_sal:>12,.2f} │\n"
                f"│ 4453       │ État, IR à payer             │              │ {ir_approx:>12,.2f} │\n"
                f"│ 4441       │ CNSS patronale               │              │ {cnss_pat:>12,.2f} │\n"
                f"│ 4432       │ Personnel, rémunération due  │              │ {net:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Bulletin de paie — Personnel chantier"
            )

        # --- Règlement fournisseur ---
        elif any(kw in prompt_lower for kw in ['règlement', 'reglement', 'paiement', 'virement', 'chèque', 'cheque']):
            montant = amount if amount else 50000
            result += (
                f"📄 Écriture : Règlement fournisseur\n"
                f"   Montant : {montant:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 4411       │ Fournisseurs                 │ {montant:>12,.2f} │              │\n"
                f"│ 5141       │ Banque                       │              │ {montant:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Règlement fournisseur — {partner}"
            )

        # --- Caution bancaire ---
        elif 'caution' in prompt_lower:
            montant = amount if amount else 30000
            commission = montant * 0.02
            result += (
                f"📄 Écriture : Caution bancaire chantier\n"
                f"   Montant de la caution : {montant:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 6147       │ Services bancaires           │ {commission:>12,.2f} │              │\n"
                f"│ 5141       │ Banque                       │              │ {commission:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Engagement hors bilan : Caution de {montant:,.2f} MAD\n"
                f"Libellé : Commission caution bancaire"
            )

        # --- Retenue de garantie libération ---
        elif 'retenue de garantie' in prompt_lower or 'libération' in prompt_lower:
            montant = amount if amount else 100000
            result += (
                f"📄 Écriture : Libération retenue de garantie\n"
                f"   Montant : {montant:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 5141       │ Banque                       │ {montant:>12,.2f} │              │\n"
                f"│ 3424       │ Clients, retenue de garantie │              │ {montant:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Libération retenue de garantie — {partner}"
            )

        # --- Avance chantier ---
        elif any(kw in prompt_lower for kw in ['avance', 'acompte']):
            montant = amount if amount else 200000
            result += (
                f"📄 Écriture : Avance sur marché\n"
                f"   Montant : {montant:,.2f} MAD\n\n"
                f"┌────────────┬──────────────────────────────┬──────────────┬──────────────┐\n"
                f"│ Compte     │ Intitulé                     │ Débit (MAD)  │ Crédit (MAD) │\n"
                f"├────────────┼──────────────────────────────┼──────────────┼──────────────┤\n"
                f"│ 5141       │ Banque                       │ {montant:>12,.2f} │              │\n"
                f"│ 4421       │ Avances reçues clients       │              │ {montant:>12,.2f} │\n"
                f"└────────────┴──────────────────────────────┴──────────────┴──────────────┘\n\n"
                f"Libellé : Avance sur marché — {partner}"
            )

        # --- Generic entry ---
        else:
            result += (
                "Précisez le type d'opération à comptabiliser :\n"
                "• Facturation de situation/décompte\n"
                "• Encaissement client\n"
                "• Achat matériaux\n"
                "• Salaire personnel chantier\n"
                "• Règlement fournisseur\n"
                "• Caution bancaire\n"
                "• Libération retenue de garantie\n"
                "• Avance sur marché\n\n"
                "Indiquez aussi le montant et le nom du tiers."
            )
        return result

    @api.model
    def _mohasib_analyse_chantier(self, ctx):
        """Analyse financière d'un chantier BTP."""
        name = ctx.get('chantier_name', ctx.get('name', 'Chantier'))
        montant = ctx.get('montant_total', ctx.get('amount_total', 0))
        avancement = ctx.get('taux_avancement', 0)
        retard = ctx.get('retard_jours', 0)
        penalite = ctx.get('penalite_retard', 0)
        state = ctx.get('state', '')

        result = f"🏗️ Mohasib — Analyse Financière Chantier\n\n"
        result += f"📋 Chantier : {name}\n"
        if montant:
            result += f"• Montant du marché : {montant:,.2f} MAD\n"
        result += f"• Avancement : {avancement}%\n"
        result += f"• État : {state}\n\n"

        if retard > 0:
            result += f"⚠️ ALERTE : Retard de {retard} jours\n"
            if penalite:
                result += f"• Pénalité estimée : {penalite:,.2f} MAD\n"
            taux_penalite = montant * 0.001 if montant else 0
            result += f"• Pénalité journalière (1‰) : {taux_penalite:,.2f} MAD/jour\n"
            result += (
                "\n📌 Recommandations :\n"
                "• Provisionner les pénalités (PCM 6195)\n"
                "• Documenter les causes du retard (ordres de service)\n"
                "• Vérifier les clauses contractuelles de prolongation\n"
            )

        if montant and avancement:
            facture_prevu = montant * avancement / 100
            result += f"\n💰 Montant à facturer (théorique) : {facture_prevu:,.2f} MAD HT\n"
            result += f"• TVA 20% : {facture_prevu * 0.20:,.2f} MAD\n"
            result += f"• Retenue garantie 10% : {facture_prevu * 0.10:,.2f} MAD\n"
            net = facture_prevu * 1.20 - facture_prevu * 0.10
            result += f"• Net à percevoir : {net:,.2f} MAD\n"

        result += (
            "\n✅ Conseil Mohasib : Tenez une comptabilité analytique "
            "par chantier pour un suivi précis des marges."
        )
        return result

    @api.model
    def _suggest_btp(self, data):
        """Suggestions BTP."""
        suggestions = []
        retard = data.get('retard_jours', 0)
        avancement = data.get('taux_avancement', 0)
        montant = data.get('montant_total', 0)

        if retard > 0:
            suggestions.append({
                'type': 'danger', 'icon': 'fa-exclamation-triangle',
                'text': f'Chantier en retard de {retard} jours — Provisionner les pénalités'
            })
        if avancement > 80 and retard == 0:
            suggestions.append({
                'type': 'success', 'icon': 'fa-check-circle',
                'text': 'Chantier bientôt terminé — Préparer le décompte définitif'
            })
        if montant > 1000000:
            suggestions.append({
                'type': 'info', 'icon': 'fa-university',
                'text': 'Marché important — Vérifier les cautions bancaires en cours'
            })
        suggestions.append({
            'type': 'info', 'icon': 'fa-calculator',
            'text': 'Vérifier la marge réelle vs marge prévisionnelle du chantier'
        })
        suggestions.append({
            'type': 'info', 'icon': 'fa-file-text',
            'text': 'Émettre les situations de travaux mensuelles à jour'
        })
        return suggestions

    # =================================================================
    #  PROMPT BUILDERS (for API mode)
    # =================================================================
    @api.model
    def _build_analysis_prompt(self, data, analysis_type, module):
        return (
            f"Analyse de type '{analysis_type}' pour le module '{module}'.\n"
            f"Données : {json.dumps(data, ensure_ascii=False, default=str)}\n"
            f"Fournis une analyse structurée avec un score, des facteurs clés "
            f"et des recommandations concrètes."
        )

    @api.model
    def _build_suggest_prompt(self, record_data, suggestion_type, module):
        return (
            f"Suggestions de type '{suggestion_type}' pour le module '{module}'.\n"
            f"Données de l'enregistrement : {json.dumps(record_data, ensure_ascii=False, default=str)}\n"
            f"Propose 3 à 5 actions concrètes et priorisées."
        )
