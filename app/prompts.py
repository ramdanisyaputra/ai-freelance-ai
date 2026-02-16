"""
Prompt templates for professional proposal generation.
Supports English and Indonesian languages.
"""

LANGUAGE_CONFIGS = {
    "en": {
        "name": "English",
        "introduction_title": "Introduction",
        "needs_title": "Understanding Your Needs",
        "approach_title": "Proposed Approach",
        "strengths_title": "Why Work With Me",
        "timeline_title": "Project Timeline",
        "pricing_title": "Investment",
        "credentials_title": "Relevant Experience",
        "social_proof_title": "Client Testimonials",
        "terms_title": "Working Together",
    },
    "id": {
        "name": "Indonesian",
        "introduction_title": "Perkenalan",
        "needs_title": "Pemahaman Kebutuhan Anda",
        "approach_title": "Pendekatan yang Diusulkan",
        "strengths_title": "Mengapa Bekerja Dengan Saya",
        "timeline_title": "Timeline Proyek",
        "pricing_title": "Investasi",
        "credentials_title": "Pengalaman Relevan",
        "social_proof_title": "Testimoni Klien",
        "terms_title": "Cara Kerja Kami",
    }
}


def get_introduction_prompt(language: str = "id") -> str:
    """Generate prompt for introduction section."""
    if language == "en":
        return """You are writing the introduction section of a professional Upwork proposal.

Guidelines:
- Start with a warm, professional greeting
- Briefly introduce your role and years of experience
- Mention relevant industries or client types
- Keep it concise (2-3 sentences)
- Show credibility without bragging

Write ONLY the introduction section in HTML format using <p> tags."""
    else:  # Indonesian
        return """Anda menulis bagian perkenalan untuk proposal profesional.

Panduan:
- Mulai dengan sapaan yang hangat dan profesional
- Perkenalkan peran dan pengalaman Anda secara singkat
- Sebutkan industri atau jenis klien yang relevan
- Tetap ringkas (2-3 kalimat)
- Tunjukkan kredibilitas tanpa berlebihan

Tulis HANYA bagian perkenalan dalam format HTML menggunakan tag <p>."""


def get_needs_assessment_prompt(language: str = "id") -> str:
    """Generate prompt for needs assessment section."""
    if language == "en":
        return """You are writing the needs assessment section of a professional Upwork proposal.

Guidelines:
- Restate the client's main goals in your own words
- Show you've read and understood the job post carefully
- Identify 2-4 key pain points or objectives
- Build trust by demonstrating understanding
- Keep it focused and specific

Write ONLY the needs assessment section in HTML format using <h3> for title and <p> or <ul> for content."""
    else:  # Indonesian
        return """Anda menulis bagian pemahaman kebutuhan untuk proposal profesional.

Panduan:
- Nyatakan kembali tujuan utama klien dengan kata-kata Anda sendiri
- Tunjukkan bahwa Anda telah membaca dan memahami brief dengan seksama
- Identifikasi 2-4 poin utama atau objektif
- Bangun kepercayaan dengan menunjukkan pemahaman
- Tetap fokus dan spesifik

Tulis HANYA bagian pemahaman kebutuhan dalam format HTML menggunakan <h3> untuk judul dan <p> atau <ul> untuk konten."""


def get_approach_prompt(language: str = "id") -> str:
    """Generate prompt for proposed approach section."""
    if language == "en":
        return """You are writing the proposed approach section of a professional Upwork proposal.

Guidelines:
- Outline a high-level strategy for the project
- Keep it simple and easy to follow
- Avoid excessive technical jargon
- Show your problem-solving methodology
- Mention 3-5 key steps or phases
- Focus on value, not just tasks

Write ONLY the approach section in HTML format using <h3> for title and <p> or <ol> for content."""
    else:  # Indonesian
        return """Anda menulis bagian pendekatan yang diusulkan untuk proposal profesional.

Panduan:
- Uraikan strategi tingkat tinggi untuk proyek
- Tetap sederhana dan mudah diikuti
- Hindari jargon teknis yang berlebihan
- Tunjukkan metodologi pemecahan masalah Anda
- Sebutkan 3-5 langkah atau fase utama
- Fokus pada nilai, bukan hanya tugas

Tulis HANYA bagian pendekatan dalam format HTML menggunakan <h3> untuk judul dan <p> atau <ol> untuk konten."""


def get_strengths_prompt(language: str = "id") -> str:
    """Generate prompt for strengths section."""
    if language == "en":
        return """You are writing the strengths/benefits section of a professional Upwork proposal.

Guidelines:
- Use a bulleted list format for scannability
- Highlight 4-6 key strengths relevant to web development
- Include: technical expertise, problem-solving, communication, track record
- Be specific but concise
- Focus on client benefits, not just your skills

Write ONLY the strengths section in HTML format using <h3> for title and <ul><li> for the list."""
    else:  # Indonesian
        return """Anda menulis bagian keunggulan/manfaat untuk proposal profesional.

Panduan:
- Gunakan format daftar poin untuk kemudahan membaca
- Sorot 4-6 keunggulan utama yang relevan dengan pengembangan web
- Sertakan: keahlian teknis, pemecahan masalah, komunikasi, track record
- Spesifik namun ringkas
- Fokus pada manfaat untuk klien, bukan hanya skill Anda

Tulis HANYA bagian keunggulan dalam format HTML menggunakan <h3> untuk judul dan <ul><li> untuk daftar."""


def get_timeline_prompt(language: str = "id") -> str:
    """Generate prompt for timeline section."""
    if language == "en":
        return """You are writing the timeline section of a professional Upwork proposal.

Guidelines:
- Provide a realistic delivery estimate
- Be specific with timeframes (e.g., "3-5 business days", "roughly 3 weeks")
- Mention key milestones if applicable
- Include revision windows
- Set clear expectations
- Adjust based on project complexity

Write ONLY the timeline section in HTML format using <h3> for title and <p> for content."""
    else:  # Indonesian
        return """Anda menulis bagian timeline untuk proposal profesional.

Panduan:
- Berikan estimasi pengiriman yang realistis
- Spesifik dengan jangka waktu (misalnya, "3-5 hari kerja", "sekitar 3 minggu")
- Sebutkan milestone utama jika ada
- Sertakan waktu revisi
- Tetapkan ekspektasi yang jelas
- Sesuaikan berdasarkan kompleksitas proyek

Tulis HANYA bagian timeline dalam format HTML menggunakan <h3> untuk judul dan <p> untuk konten."""


def get_pricing_prompt(language: str = "id") -> str:
    """Generate prompt for pricing section."""
    if language == "en":
        return """You are writing the pricing section of a professional Upwork proposal.

Guidelines:
- Explain your rate clearly
- Show how it relates to the value you provide
- Mention experience, results, or efficient delivery
- Frame as an investment, not just a cost
- Be transparent and professional
- Include what's covered in the price

Write ONLY the pricing section in HTML format using <h3> for title and <p> for content."""
    else:  # Indonesian
        return """Anda menulis bagian harga untuk proposal profesional.

Panduan:
- Jelaskan tarif Anda dengan jelas
- Tunjukkan bagaimana ini berhubungan dengan nilai yang Anda berikan
- Sebutkan pengalaman, hasil, atau pengiriman yang efisien
- Posisikan sebagai investasi, bukan hanya biaya
- Transparan dan profesional
- Sertakan apa yang termasuk dalam harga

Tulis HANYA bagian harga dalam format HTML menggunakan <h3> untuk judul dan <p> untuk konten."""


def get_credentials_prompt(language: str = "id") -> str:
    """Generate prompt for credentials section."""
    if language == "en":
        return """You are writing the credentials/tools section of a professional Upwork proposal.

Guidelines:
- List relevant software, platforms, or certifications
- Focus on tools mentioned in the job description
- Include commonly used web development tools
- Keep it scannable with bullet points
- Show capability without overwhelming

Write ONLY the credentials section in HTML format using <h3> for title and <ul><li> for the list."""
    else:  # Indonesian
        return """Anda menulis bagian kredensial/tools untuk proposal profesional.

Panduan:
- Daftar software, platform, atau sertifikasi yang relevan
- Fokus pada tools yang disebutkan dalam deskripsi pekerjaan
- Sertakan tools pengembangan web yang umum digunakan
- Buat mudah dibaca dengan poin-poin
- Tunjukkan kemampuan tanpa berlebihan

Tulis HANYA bagian kredensial dalam format HTML menggunakan <h3> untuk judul dan <ul><li> untuk daftar."""


def get_social_proof_prompt(language: str = "id") -> str:
    """Generate prompt for social proof section."""
    if language == "en":
        return """You are writing the social proof/testimonials section of a professional Upwork proposal.

Guidelines:
- Include 1-2 client outcome examples with metrics
- Add brief testimonial quotes if available
- Focus on results (e.g., "increased conversions by 20%")
- Keep testimonials authentic and specific
- Show that your work delivers value

Write ONLY the social proof section in HTML format using <h3> for title, <p> for outcomes, and <blockquote> for testimonials."""
    else:  # Indonesian
        return """Anda menulis bagian bukti sosial/testimoni untuk proposal profesional.

Panduan:
- Sertakan 1-2 contoh hasil klien dengan metrik
- Tambahkan kutipan testimoni singkat jika ada
- Fokus pada hasil (misalnya, "meningkatkan konversi 20%")
- Buat testimoni autentik dan spesifik
- Tunjukkan bahwa pekerjaan Anda memberikan nilai

Tulis HANYA bagian bukti sosial dalam format HTML menggunakan <h3> untuk judul, <p> untuk hasil, dan <blockquote> untuk testimoni."""


def get_terms_prompt(language: str = "id") -> str:
    """Generate prompt for terms/expectations section."""
    if language == "en":
        return """You are writing the terms and expectations section of a professional Upwork proposal.

Guidelines:
- Explain communication channels and frequency
- Mention deliverable management approach
- Include revision policy
- Set clear expectations for the working relationship
- Keep it professional but friendly
- Use bullet points for clarity

Write ONLY the terms section in HTML format using <h3> for title and <ul><li> for the list."""
    else:  # Indonesian
        return """Anda menulis bagian syarat dan ekspektasi untuk proposal profesional.

Panduan:
- Jelaskan saluran komunikasi dan frekuensi
- Sebutkan pendekatan manajemen deliverable
- Sertakan kebijakan revisi
- Tetapkan ekspektasi yang jelas untuk hubungan kerja
- Tetap profesional namun ramah
- Gunakan poin-poin untuk kejelasan

Tulis HANYA bagian syarat dalam format HTML menggunakan <h3> untuk judul dan <ul><li> untuk daftar."""
