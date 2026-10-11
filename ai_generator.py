import json
import re
import requests
from config import Config, TEMPLATES_DIR

class AIEmailGenerator:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL or "gemini-2.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate(self, company_data: dict) -> dict:
        """
        Generates a personalized cold email (subject & body) for a given company.
        Returns dict: {"subject": str, "body": str, "used_ai": bool}
        """
        company_name = company_data.get("company_name", "your company")
        contact_name = company_data.get("contact_name", "Hiring Team")
        role = company_data.get("role", "Software Engineer")
        notes = company_data.get("company_notes", "")

        # If Gemini API key is missing, use standard template fallback
        if not self.api_key or self.api_key.strip() == "":
            return self._fallback_template(company_data, reason="Gemini API Key not set")

        try:
            return self._call_gemini(company_name, contact_name, role, notes)
        except Exception as e:
            # Fallback smoothly if network/quota issue occurs
            return self._fallback_template(company_data, reason=f"AI generation fallback: {str(e)}")

    def _call_gemini(self, company_name: str, contact_name: str, role: str, notes: str) -> dict:
        prompt = f"""
You are an expert career advisor and cold outreach specialist.
Write a highly compelling, polite, concise, and professional job application email.

Candidate Information:
- Name: {Config.SENDER_NAME}
- Contact Email: {Config.SENDER_EMAIL}
- Phone: {Config.SENDER_PHONE}
- LinkedIn: {Config.SENDER_LINKEDIN}
- Background Summary: {Config.CANDIDATE_SUMMARY}

Target Recipient Information:
- Company Name: {company_name}
- Contact / Recipient Name: {contact_name}
- Target Role / Position: {role}
- Specific Notes / Company Details: {notes}

Guidelines:
1. Language: Moroccan market context. If the role or company notes are in French (e.g. 'Développeur', 'Ingénieur', etc.), write the email in natural, elegant, and professional French! If English, write in professional English.
2. Length: Short and impactful (between 120 and 160 words).
3. Structure:
   - Polite greeting (e.g. "Bonjour {contact_name}," or "Dear {contact_name},").
   - Clear hook indicating the target role ({role}) and appreciation for {company_name}.
   - Value pitch highlighting relevant technical skills and motivation.
   - Mention the attached resume (CV ci-joint) and a clear call to action proposing a brief 10-15 minute discussion.
   - Professional sign-off including the candidate's name, email, phone, and LinkedIn.
4. Output Format: Reply with ONLY a raw JSON object with keys: "subject" and "body".
Example:
{{
  "subject": "Candidature au poste de Développeur Fullstack - Hamza Zaidi",
  "body": "Bonjour Équipe Recrutement,\\n\\n..."
}}
"""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2500,
                "responseMimeType": "application/json"
            }
        }

        response = requests.post(
            self.api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=45
        )

        if response.status_code != 200:
            raise RuntimeError(f"Gemini API returned status {response.status_code}: {response.text}")

        res_json = response.json()
        candidates = res_json.get("candidates", [])
        if not candidates:
            raise RuntimeError("No generation candidates returned from Gemini.")

        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Clean text if wrapped in markdown code fence
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed = json.loads(clean_text, strict=False)
        except Exception:
            # Fallback regex extraction if model didn't escape quotes or newlines
            import re
            subject_match = re.search(r'"subject"\s*:\s*"([^"]+)"', clean_text)
            body_match = re.search(r'"body"\s*:\s*"(.*)"', clean_text, re.DOTALL)
            parsed = {
                "subject": subject_match.group(1) if subject_match else f"Candidature au poste de {role} - {Config.SENDER_NAME}",
                "body": body_match.group(1) if body_match else clean_text
            }

        return {
            "subject": parsed.get("subject", f"Candidature au poste de {role} - {Config.SENDER_NAME}"),
            "body": parsed.get("body", "").strip(),
            "used_ai": True
        }

    def _fallback_template(self, company_data: dict, reason: str = "") -> dict:
        company_name = company_data.get("company_name", "votre entreprise")
        contact_name = company_data.get("contact_name", "Équipe Recrutement")
        role = company_data.get("role", "Développeur Full Stack")
        notes = company_data.get("company_notes", "")

        is_french = any(w in (role + " " + notes).lower() for w in ["développeur", "ingénieur", "équipe", "maroc", "rabat", "solution", "projet"])

        if is_french:
            custom_pitch = f"Je suis particulièrement intéressé par les projets et l'expertise de {company_name}."
            if notes:
                custom_pitch = f"Votre positionnement ({notes}) correspond particulièrement à mes aspirations professionnelles et à mes compétences techniques."

            subject = f"Candidature au poste de {role} - {Config.SENDER_NAME}"
            body = f"""Bonjour {contact_name},

Je me permets de vous contacter pour vous présenter ma candidature au poste de {role} au sein de {company_name}.

Fort de mon profil ({Config.CANDIDATE_SUMMARY}), je suis avec grand intérêt le développement de {company_name}.

{custom_pitch}

Vous trouverez ci-joint mon CV détaillant mon parcours technique et mes réalisations. Je serais ravi d'échanger avec vous lors d'un bref entretien pour vous exposer ma motivation et discuter de la manière dont je pourrais contribuer à vos projets.

En vous remerciant pour l'attention portée à ma démarche, je vous prie d'agréer mes salutations distinguées.

Bien cordialement,

{Config.SENDER_NAME}
{Config.SENDER_EMAIL}
{Config.SENDER_PHONE}
{Config.SENDER_LINKEDIN}"""
        else:
            custom_pitch = f"I am particularly drawn to {company_name}'s recent initiatives and team culture."
            if notes:
                custom_pitch = f"Specifically, {notes} resonates strongly with my background and career goals."

            subject = f"Application for {role} - {Config.SENDER_NAME}"
            body = f"""Hi {contact_name},

I hope this email finds you well.

I am reaching out to express my keen interest in the {role} position at {company_name}. With my background in {Config.CANDIDATE_SUMMARY}, I have followed {company_name}'s work with great admiration.

{custom_pitch}

I have attached my resume for your review and would welcome the opportunity to speak with you briefly about how my skill set and enthusiasm can contribute to {company_name}'s team.

Thank you very much for your time and consideration.

Best regards,

{Config.SENDER_NAME}
{Config.SENDER_EMAIL}
{Config.SENDER_PHONE}
{Config.SENDER_LINKEDIN}"""

        return {
            "subject": subject,
            "body": body.strip(),
            "used_ai": False,
            "fallback_reason": reason
        }
