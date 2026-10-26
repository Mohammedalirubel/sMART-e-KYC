"""Transparent DEMO risk indicator. NOT the bank's Annexure-2 grading."""
HIGH_RISK_PROFESSIONS = ('politician', 'minister', 'mp', 'money changer', 'jeweller', 'real estate', 'exchange house')

def indicate(product, path, income, source, profession, age, nominee_rel):
    score, why = 0, []
    if income >= 500_000: score += 2; why.append('Very high declared monthly income')
    elif income >= 150_000: score += 1; why.append('High declared monthly income')
    if income == 0: score += 1; why.append('No income declared')
    if any(k in profession.lower() for k in HIGH_RISK_PROFESSIONS):
        score += 2; why.append('Profession needs enhanced review (PEP / cash-intensive)')
    if len(source.strip()) < 4: score += 1; why.append('Source of funds too vague')
    if product == 'Limited Transactions Account' and income > 100_000:
        score += 1; why.append('Income inconsistent with limited-transaction product')
    if path.startswith('Simplified') and income > 50_000:
        score += 1; why.append('Income high for simplified e-KYC')
    if age < 21 or age > 75: score += 1; why.append('Age band needs extra care')
    grade = 'Low' if score <= 1 else 'Medium' if score <= 3 else 'High'
    return grade, score, why or ['No heuristic flags']
