from typing import List, Dict, Any
import re


APPROVED_KNOWLEDGE_DOCUMENTS = [
    {
        "id": "tax-115bac-ay2526",
        "title": "Income Tax Act 1961 - Section 115BAC (New Tax Regime)",
        "source": "Income Tax Department / Finance Act 2024",
        "citation": "Section 115BAC of the Income-tax Act, 1961 as amended by Finance (No. 2) Act, 2024",
        "content": (
            "Section 115BAC(1A) defines the concessional New Tax Regime applicable as default from AY 2024-25. "
            "For AY 2025-26, standard deduction for salaried employees is enhanced to ₹75,000 under Section 16(ia). "
            "Tax slabs for AY 2025-26: 0-3L (Nil), 3L-7L (5%), 7L-10L (10%), 10L-12L (15%), 12L-15L (20%), >15L (30%). "
            "Section 87A rebate provides full relief up to ₹25,000 for taxable income up to ₹7,00,000. Salaried individuals "
            "earning up to ₹7,75,000 (after standard deduction of ₹75,000) pay zero income tax."
        ),
        "tags": ["tax", "new regime", "115BAC", "standard deduction", "87A", "slabs"]
    },
    {
        "id": "tax-deductions-old-regime",
        "title": "Chapter VI-A Deductions (Old Tax Regime)",
        "source": "Income Tax Department",
        "citation": "Income-tax Act, 1961 Chapter VI-A (Sections 80C, 80D, 80CCD, 24(b))",
        "content": (
            "Under the Old Tax Regime, taxpayers can claim: Section 80C up to ₹1,50,000 (EPF, PPF, ELSS, Life Insurance); "
            "Section 80D up to ₹25,000 for self/family and ₹50,000 for senior citizen parents; Section 80CCD(1B) up to ₹50,000 "
            "for National Pension System (NPS); Section 24(b) deduction up to ₹2,00,000 for interest on borrowed capital for "
            "self-occupied home loan; Section 10(13A) HRA exemption based on rent paid."
        ),
        "tags": ["tax", "old regime", "80C", "80D", "NPS", "home loan", "HRA"]
    },
    {
        "id": "invest-sebi-liquid-funds",
        "title": "SEBI Categorization and Norms for Liquid Mutual Funds",
        "source": "Securities and Exchange Board of India (SEBI)",
        "citation": "SEBI Circular SEBI/HO/IMD/DF3/CIR/P/2017/114 & SEBI/HO/IMD/DF2/CIR/P/2019/101",
        "content": (
            "SEBI regulations require Liquid Schemes to invest solely in debt and money market securities with a residual maturity "
            "not exceeding 91 days. Schemes must maintain at least 20% in liquid assets (cash, treasury bills, government securities). "
            "Instant redemption facility allows up to ₹50,000 or 90% of folio value (whichever is lower) per day per scheme within "
            "minutes via IMPS. Exit loads apply only if redeemed within 7 days of subscription."
        ),
        "tags": ["investment", "liquid fund", "SEBI", "liquidity", "redemption", "exit load"]
    },
    {
        "id": "tax-section-50aa-debt-funds",
        "title": "Section 50AA - Taxation of Specified Mutual Funds",
        "source": "Finance Act 2023 / CBDT",
        "citation": "Section 50AA of the Income-tax Act, 1961 (inserted w.e.f. Assessment Year 2024-25)",
        "content": (
            "Any capital gain arising from transfer or redemption of units of a 'Specified Mutual Fund' acquired on or after "
            "April 1, 2023, where not more than 35% of total proceeds is invested in equity shares of domestic companies, "
            "is deemed to be short-term capital gains and taxed at the investor's applicable marginal income tax slab rate, "
            "without indexation benefits."
        ),
        "tags": ["tax", "debt mutual funds", "liquid fund", "50AA", "capital gains", "slab rate"]
    },
    {
        "id": "banking-dicgc-insurance",
        "title": "DICGC Bank Deposit Insurance Cover",
        "source": "Deposit Insurance and Credit Guarantee Corporation (RBI)",
        "citation": "DICGC Act 1961 / Deposit Insurance Scheme",
        "content": (
            "Each depositor in an insured bank is insured up to a maximum of ₹5,00,000 (Rupees Five Lakhs) for both principal "
            "and interest held in the same capacity and same right across all branches of that bank. Covered deposits include "
            "savings, fixed, current, and recurring deposits."
        ),
        "tags": ["banking", "fixed deposit", "FD", "DICGC", "safety", "insurance"]
    }
]


class KnowledgeRetriever:
    """
    RAG retrieval engine matching user financial queries against approved source documents.
    """

    @classmethod
    def search(cls, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        tokens = set(re.findall(r"\w+", query.lower()))
        scored = []

        for doc in APPROVED_KNOWLEDGE_DOCUMENTS:
            doc_text = (doc["title"] + " " + doc["content"] + " " + " ".join(doc["tags"])).lower()
            doc_tokens = set(re.findall(r"\w+", doc_text))
            
            # Jaccard / token overlap score
            overlap = len(tokens.intersection(doc_tokens))
            tag_matches = sum(1 for tag in doc["tags"] if tag.lower() in query.lower())
            score = overlap + (tag_matches * 3)

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
