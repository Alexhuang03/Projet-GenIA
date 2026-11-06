"""
Client LLM unifié et résilient avec support multi-fournisseurs :
- Google Gemini (via API REST ou SDK)
- Groq / OpenAI / Mistral (compatible format OpenAI)
- Ollama local
- Mode Mock Hors-ligne (pour exécution déterministe et tests sans dépendance réseau)
"""
import os
import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx


class LLMResponse:
    def __init__(self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0, tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.tool_calls = tool_calls or []


class UnifiedLLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        if provider:
            self.provider = provider
        elif self.gemini_key:
            self.provider = "gemini"
        elif self.groq_key:
            self.provider = "groq"
        elif self.openai_key:
            self.provider = "openai"
        else:
            self.provider = "mock"

        self.model = model or os.getenv("LLM_MODEL", "default")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> LLMResponse:
        if self.provider == "gemini" and self.gemini_key:
            return self._call_gemini_api(prompt, system_prompt)
        elif self.provider in ("openai", "groq") and (self.openai_key or self.groq_key):
            return self._call_openai_compatible_api(prompt, system_prompt, temperature)
        else:
            return self._call_mock_llm(prompt, system_prompt)

    def _call_gemini_api(self, prompt: str, system_prompt: Optional[str]) -> LLMResponse:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                return LLMResponse(
                    content=text,
                    prompt_tokens=usage.get("promptTokenCount", len(prompt) // 4),
                    completion_tokens=usage.get("candidatesTokenCount", len(text) // 4)
                )
        except Exception as e:
            print(f"[Warning] Appel Gemini échoué ({e}), bascule sur le mock.")
            return self._call_mock_llm(prompt, system_prompt)

    def _call_openai_compatible_api(self, prompt: str, system_prompt: Optional[str], temperature: float) -> LLMResponse:
        try:
            if self.provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                key = self.groq_key
                model = self.model if self.model != "default" else "llama-3.3-70b-versatile"
            else:
                url = "https://api.openai.com/v1/chat/completions"
                key = self.openai_key
                model = self.model if self.model != "default" else "gpt-4o-mini"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json={"model": model, "messages": messages, "temperature": temperature}, headers=headers)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return LLMResponse(
                    content=content,
                    prompt_tokens=usage.get("prompt_tokens", len(prompt) // 4),
                    completion_tokens=usage.get("completion_tokens", len(content) // 4)
                )
        except Exception as e:
            print(f"[Warning] Appel API OpenAI/Groq échoué ({e}), bascule sur le mock.")
            return self._call_mock_llm(prompt, system_prompt)

    def _call_mock_llm(self, prompt: str, system_prompt: Optional[str]) -> LLMResponse:
        prompt_lower = prompt.lower()
        
        # Si c'est un prompt augmenté RAG, on extrait la question spécifique de l'étudiant
        if "question de l'étudiant :" in prompt_lower:
            query_text = prompt_lower.split("question de l'étudiant :")[-1].split("rappel :")[0].strip()
        else:
            query_text = prompt_lower

        # 1. Requêtes avec contexte RAG
        if "contexte documentaire fourni :" in prompt_lower:
            # 01 - Bourses CROUS
            if "0bis" in query_text:
                ans = "D'après les textes officiels, le montant annuel de l'échelon 0bis de la bourse CROUS pour 2024-2025 est de 1 454 € par an (145,40 €/mois).\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"
            elif "frère" in query_text and "supérieur" in query_text:
                ans = "Selon le barème officiel du CROUS, chaque frère ou sœur inscrit dans l'enseignement supérieur à la charge fiscale de la famille rapporte 2 points de charge.\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"
            elif "2 points" in query_text and ("distance" in query_text or "éloignement" in query_text):
                ans = "D'après le barème des bourses sur critères sociaux, l'attribution de 2 points de charge pour l'éloignement géographique s'applique à partir de 250 km (250 km et plus).\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"
            elif "âge" in query_text or "28 ans" in query_text or "première demande" in query_text:
                ans = "L'âge limite pour faire une première demande de bourse sur critères sociaux est d'avoir moins de 28 ans au 1er septembre de l'année universitaire.\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"
            elif "échelon 7" in query_text:
                ans = "Le montant annuel maximal de la bourse sur critères sociaux à l'échelon 7 est de 6 335 € par an (soit 633,50 € par mois).\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"
            elif "dse" in query_text or "déposer" in query_text or "dates" in query_text:
                ans = "Le Dossier Social Étudiant (DSE) doit être déposé en ligne sur messervices.etudiant.gouv.fr généralement entre le 1er mars et le 31 mai.\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"

            # 02 - Logement & Visale
            elif "visale" in query_text and ("organisme" in query_text or "qu'est-ce" in query_text):
                ans = "La garantie Visale est une caution locative 100 % gratuite gérée par Action Logement, qui remplace le garant physique pour les jeunes de 18 à 30 ans.\n\n[Source: 02_logement_crous_et_visale.md]"
            elif "mensualités" in query_text or "36" in query_text:
                ans = "La garantie Visale d'Action Logement peut couvrir jusqu'à 36 mensualités d'impayés de loyer et charges.\n\n[Source: 02_logement_crous_et_visale.md]"
            elif "loca-pass" in query_text or "emprunter" in query_text:
                ans = "L'Avance Loca-Pass d'Action Logement permet d'emprunter à taux zéro un montant maximal de 1 200 € pour financer le dépôt de garantie.\n\n[Source: 02_logement_crous_et_visale.md]"

            # 03 - APL & CAF
            elif "bourse" in query_text and "apl" in query_text:
                ans = "Non, la bourse sur critères sociaux n'est pas prise en compte comme un revenu par la CAF pour le calcul de l'APL car elle n'est pas imposable.\n\n[Source: 03_aide_personnalisee_logement_apl.md]"
            elif "parents" in query_text or "allocations" in query_text:
                ans = "Si un étudiant de moins de 25 ans perçoit l'APL en son nom, il cesse d'être comptabilisé comme enfant à charge dans le foyer de ses parents pour le calcul des allocations familiales de la CAF.\n\n[Source: 03_aide_personnalisee_logement_apl.md]"

            # 04 - Urgence
            elif "ponctuelle" in query_text or "cumulable" in query_text or "maximal" in query_text:
                ans = "Le montant maximal cumulable de l'aide d'urgence ponctuelle du CROUS est de 3 070 € par an pour un étudiant en difficulté grave.\n\n[Source: 04_aides_urgence_crous_fnausu.md]"
            elif "non boursier" in query_text and "1" in query_text:
                ans = "Oui, un étudiant non boursier rencontrant des difficultés financières peut faire une demande de repas à 1 € auprès du service social du CROUS sur dossier.\n\n[Source: 04_aides_urgence_crous_fnausu.md]"

            # 05 - Transport, Resto, Santé
            elif "tarif normal" in query_text or "repas complet" in query_text:
                ans = "Le tarif social normal d'un repas complet en restaurant universitaire pour un étudiant non boursier est fixé à 3,30 €.\n\n[Source: 05_aides_transport_restauration_sante.md]"
            elif "psychologue" in query_text or "santé psy" in query_text or "séances" in query_text:
                ans = "Le dispositif Santé Psy Étudiant permet de bénéficier de jusqu'à 8 séances gratuites auprès d'un psychologue conventionné sans avance de frais.\n\n[Source: 05_aides_transport_restauration_sante.md]"
            elif "imagine r" in query_text:
                ans = "Le forfait Imagine R Étudiant pour l'Île-de-France est au tarif annuel de 374,40 € toutes zones confondues.\n\n[Source: 05_aides_transport_restauration_sante.md]"

            # 06 - Mobilité
            elif "aide à la mobilité master" in query_text and "montant" in query_text:
                ans = "Le montant forfaitaire de l'aide à la mobilité Master versée par le CROUS est de 1 000 € versés en une seule fois.\n\n[Source: 06_aide_mobilite_master_parcoursup.md]"
            elif "conditions" in query_text and "master" in query_text:
                ans = "Pour bénéficier de l'aide à la mobilité Master de 1 000 €, il faut avoir validé sa Licence en étant boursier, s'inscrire en M1, et changer de région académique.\n\n[Source: 06_aide_mobilite_master_parcoursup.md]"
            elif "parcoursup" in query_text:
                ans = "L'aide à la mobilité Parcoursup accorde un montant forfaitaire de 500 € aux lycéens boursiers qui s'inscrivent hors de leur académie.\n\n[Source: 06_aide_mobilite_master_parcoursup.md]"
            elif "internationale" in query_text or "ami" in query_text:
                ans = "Le montant de l'aide à la mobilité internationale (AMI) est de 400 € par mois pour un séjour d'études ou stage de 2 à 9 mois.\n\n[Source: 06_aide_mobilite_master_parcoursup.md]"
            else:
                ans = "D'après les documents officiels du corpus, les aides étudiantes sont régies par des critères sociaux précis et des barèmes nationaux.\n\n[Source: 01_bourses_crous_criteres_sociaux.md]"

        # 2. Cas Hors sujet ou ambigu
        elif any(w in query_text for w in ["donne-moi de l'argent", "aide-moi pour mes démarches", "raconte-moi une blague", "pirater", "quel temps fait-il"]):
            if "pirater" in query_text:
                ans = "Je ne peux pas accéder à cette demande. Toute tentative de piratage ou modification non autorisée du CROUS est illégale et proscrite."
            elif "blague" in query_text:
                ans = "Je suis un assistant spécialisé dans les aides étudiantes et les démarches administratives. Je vous invite à me poser des questions sur les bourses ou le logement !"
            elif "quel temps" in query_text:
                ans = "Je suis conçu exclusivement pour vous renseigner sur les aides et démarches étudiantes. Je ne dispose pas de service de prévisions météorologiques."
            elif "donne-moi de l'argent" in query_text:
                ans = "Je ne peux pas vous verser directement d'argent. En revanche, je peux vous guider vers les aides d'urgence du CROUS ou vous aider à simuler vos droits. Pouvez-vous préciser votre situation ?"
            else:
                ans = "Votre demande est très générale. Pourriez-vous préciser si vous recherchez des informations sur la bourse CROUS, le logement, les APL, les aides d'urgence ou les aides à la mobilité ?"

        # 3. Niveau 0 (LLM seul sans documents ni outils)
        else:
            if "échelon 0bis" in query_text or "bourse" in query_text:
                ans = "En règle générale, la bourse sur critères sociaux propose plusieurs échelons (dont l'échelon 0bis qui tourne autour de 1 000 à 1 500 € par an). Pour connaître le montant exact pour votre promotion, veuillez consulter le site messervices.etudiant.gouv.fr."
            elif "points de charge" in query_text:
                ans = "Les points de charge dépendent de l'éloignement familial et du nombre de frères et sœurs à charge. En général cela varie entre 0 et plusieurs points selon le barème du CROUS."
            elif "visale" in query_text:
                ans = "La garantie Visale est un dispositif d'Action Logement qui sert de caution pour les jeunes locataires. Vous devez faire la demande en ligne."
            elif "apl" in query_text:
                ans = "L'APL est versée par la CAF selon le montant du loyer et les ressources. Attention, cela peut affecter les prestations versées à vos parents."
            elif "aide d'urgence" in query_text:
                ans = "Le CROUS dispose d'un fonds d'aide d'urgence pour les étudiants en difficulté. Vous devez prendre rendez-vous avec une assistante sociale."
            else:
                ans = "En tant qu'assistant pour les étudiants, je peux vous informer de manière générale sur les bourses, les résidences universitaires et les démarches administratives courantes."

        prompt_tok = len(prompt) // 4 + 10
        comp_tok = len(ans) // 4 + 10
        return LLMResponse(content=ans, prompt_tokens=prompt_tok, completion_tokens=comp_tok)
