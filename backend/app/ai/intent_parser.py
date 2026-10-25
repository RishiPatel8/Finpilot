import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, timedelta
from app.schemas.agent import ParsedIntent


class AgentIntentParser:
    """
    Interprets natural language financial queries and commands.
    Distinguishes:
    - READ_ANALYSIS (questions, diagnostics, scenario simulations)
    - WRITE_ACTION (financial record creation, update, pause, cancellation)
    - AMBIGUOUS (requests that require one focused clarification question)
    - UNSUPPORTED (requests outside system capabilities, e.g. direct bank wire transfers)
    """

    @classmethod
    def parse(
        cls,
        message: str,
        recent_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ParsedIntent:
        q = message.strip()
        ql = q.lower()

        # 1. External payment or unsupported money transfer request
        is_live_wire = any(p in ql for p in ["transfer money to", "send money to", "pay via upi to", "wire transfer", "disburse loan to"])
        is_record_cmd = any(p in ql for p in ["add", "record", "track", "log", "note", "transaction", "transcation"])
        if is_live_wire and not is_record_cmd:
            return ParsedIntent(
                intent_type="UNSUPPORTED",
                confidence=0.95,
                clarification_question=(
                    "FinPilot AI is a personal finance intelligence and record-keeping platform. "
                    "For your security, I do not execute direct bank fund transfers, UPI payments, or wire transactions. "
                    "Would you like me to record this as a tracked manual transaction or recurring expense instead?"
                )
            )

        # 1B. Live Brokerage Trades, Crypto, and External Order Placement Safety Gate
        is_external_trade = any(p in ql for p in [
            "buy stock", "sell stock", "trade bitcoin", "buy bitcoin", "buy crypto", "sell crypto",
            "execute order", "book flight", "book hotel"
        ])
        if is_external_trade:
            return ParsedIntent(
                intent_type="UNSUPPORTED",
                confidence=0.95,
                clarification_question=(
                    "FinPilot AI is a personal finance intelligence and record-keeping platform. "
                    "I do not execute live broker stock orders, cryptocurrency trades, or booking transactions. "
                    "You can track your existing investments under Assets or simulate investment scenarios."
                )
            )

        # 2. Check for follow-up contextual references (e.g. "increase it by 10%", "undo that", "confirm")
        if any(p in ql for p in ["increase it by", "decrease it by", "reduce it by", "cut it by"]) and recent_history:
            pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", ql)
            pct = float(pct_match.group(1)) if pct_match else 10.0
            is_increase = "increase" in ql
            
            # Find last mentioned category or budget in recent history
            last_asst = next((m["content"] for m in reversed(recent_history) if m.get("sender") == "assistant"), "")
            cat = "Living Expenses"
            for c in ["groceries", "grocery", "dining", "food", "entertainment", "shopping", "transport"]:
                if c in last_asst.lower() or c in ql:
                    cat = c.capitalize()
                    break

            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="update_budget",
                target_entity="budget",
                confidence=0.88,
                extracted_parameters={
                    "category": cat,
                    "adjustment_pct": pct if is_increase else -pct,
                    "is_relative": True
                }
            )

        # 3A. Credit Card Loan Ambiguity
        # Distinguish: outstanding statement balance, EMI loan liability, loan inflow, or debt repayment
        is_cc_loan = ("credit card" in ql or "credit-card" in ql or "cc loan" in ql) and ("loan" in ql or "debt" in ql or "liability" in ql)
        if is_cc_loan and not any(k in ql for k in ["statement balance only", "convert to emi", "already paid"]):
            amt = cls._extract_amount(ql) or 10000.0
            emi_calc = round((amt * (0.16 / 12) * ((1 + 0.16 / 12) ** 12)) / (((1 + 0.16 / 12) ** 12) - 1), 2)
            options = [
                {
                    "id": "opt_cc_balance",
                    "label": "Credit-card outstanding balance",
                    "action_type": "create_debt",
                    "target_entity": "liability",
                    "parameters": {
                        "name": "Credit Card Outstanding Balance",
                        "principal": amt,
                        "interest_rate": 36.0,
                        "monthly_emi": amt,
                        "tenure_months": 1,
                        "remaining_months": 1
                    }
                },
                {
                    "id": "opt_cc_emi",
                    "label": "Credit-card EMI/loan liability",
                    "action_type": "create_debt",
                    "target_entity": "liability",
                    "parameters": {
                        "name": "Credit Card EMI Loan",
                        "principal": amt,
                        "interest_rate": 16.0,
                        "monthly_emi": emi_calc,
                        "tenure_months": 12,
                        "remaining_months": 12
                    }
                },
                {
                    "id": "opt_cc_inflow",
                    "label": "Loan received as income",
                    "action_type": "create_transaction",
                    "target_entity": "transaction",
                    "parameters": {
                        "amount": amt,
                        "type": "income",
                        "category": "Loan Inflow",
                        "description": "Credit Card Loan Proceeds Received"
                    }
                },
                {
                    "id": "opt_cc_repay",
                    "label": "Record a repayment already made",
                    "action_type": "create_transaction",
                    "target_entity": "transaction",
                    "parameters": {
                        "amount": amt,
                        "type": "expense",
                        "category": "Debt Repayment",
                        "description": "Credit Card Repayment Made"
                    }
                }
            ]
            return ParsedIntent(
                intent_type="AMBIGUOUS",
                is_ambiguous=True,
                confidence=0.95,
                extracted_parameters={"amount": amt, "loan_type": "credit_card"},
                clarification_question=(
                    f"What should I add for this ₹{amt:,.0f} credit card liability?\n\n"
                    "1. Credit-card outstanding balance\n"
                    "2. Credit-card EMI/loan liability\n"
                    "3. Loan received as income\n"
                    "4. Record a repayment already made"
                ),
                clarification_options=[opt["label"] for opt in options],
                structured_options=options
            )

        # 3B. General Loan Ambiguity: "Add ... loan to debt" or "loan to debt" without specific loan type
        if ("loan" in ql and "debt" in ql) and not any(k in ql for k in ["repay", "paid", "emi", "interest rate", "tenure", "car loan", "home loan", "education loan"]):
            amt = cls._extract_amount(ql) or 1000.0
            options = [
                {
                    "id": "opt_debt_liability",
                    "label": "Record a new debt liability",
                    "action_type": "create_debt",
                    "target_entity": "liability",
                    "parameters": {
                        "name": "Personal Loan",
                        "principal": amt,
                        "interest_rate": 12.0,
                        "monthly_emi": round(amt / 12, 2),
                        "tenure_months": 12,
                        "remaining_months": 12
                    }
                },
                {
                    "id": "opt_debt_repayment",
                    "label": "Record an EMI or loan repayment",
                    "action_type": "create_transaction",
                    "target_entity": "transaction",
                    "parameters": {
                        "amount": amt,
                        "type": "expense",
                        "category": "Debt Repayment",
                        "description": "Loan Repayment"
                    }
                },
                {
                    "id": "opt_debt_inflow",
                    "label": "Record loan disbursement received as income",
                    "action_type": "create_transaction",
                    "target_entity": "transaction",
                    "parameters": {
                        "amount": amt,
                        "type": "income",
                        "category": "Loan Inflow",
                        "description": "Loan Proceeds Received"
                    }
                }
            ]
            return ParsedIntent(
                intent_type="AMBIGUOUS",
                is_ambiguous=True,
                confidence=0.92,
                extracted_parameters={"amount": amt},
                clarification_question=(
                    f"You mentioned adding a ₹{amt:,.0f} loan. To record this accurately in FinPilot, which option do you mean?\n\n"
                    "1. Record a new debt liability (outstanding balance to track and pay off)\n"
                    "2. Record a loan repayment or EMI payment made\n"
                    "3. Record loan disbursement received as income\n\n"
                    "Please reply with 1, 2, or 3, or select an option below."
                ),
                clarification_options=[opt["label"] for opt in options],
                structured_options=options
            )

        # 4. Clarification answer handling: Fallback when recent_history is provided without active persistent clarification
        if recent_history:
            last_user_or_asst = recent_history[-1].get("content", "").lower()
            if "loan" in last_user_or_asst and ("which option do you mean" in last_user_or_asst or "what should i add" in last_user_or_asst):
                # Find amount from history
                prior_amt = 1000.0
                amt_match = re.search(r"₹?([0-9,]+(?:\.[0-9]+)?)", last_user_or_asst)
                if amt_match:
                    try:
                        prior_amt = float(amt_match.group(1).replace(",", ""))
                    except Exception:
                        pass

                if ql in ["1", "1.", "1. update it", "option 1", "yes, update it"] or "debt liability" in ql or "outstanding balance" in ql:
                    is_cc = "credit card" in last_user_or_asst
                    return ParsedIntent(
                        intent_type="WRITE_ACTION",
                        action_type="create_debt",
                        target_entity="liability",
                        confidence=0.95,
                        extracted_parameters={
                            "name": "Credit Card Outstanding Balance" if is_cc else "Personal Loan",
                            "principal": prior_amt,
                            "interest_rate": 36.0 if is_cc else 12.0,
                            "monthly_emi": prior_amt if is_cc else round(prior_amt / 12, 2),
                            "tenure_months": 1 if is_cc else 12,
                            "remaining_months": 1 if is_cc else 12
                        }
                    )
                elif ql in ["2", "2.", "2. update it", "option 2"] or "emi" in ql or "loan liability" in ql or "repayment" in ql:
                    is_cc = "credit card" in last_user_or_asst
                    if is_cc:
                        emi_val = round((prior_amt * (0.16 / 12) * ((1 + 0.16 / 12) ** 12)) / (((1 + 0.16 / 12) ** 12) - 1), 2)
                        return ParsedIntent(
                            intent_type="WRITE_ACTION",
                            action_type="create_debt",
                            target_entity="liability",
                            confidence=0.95,
                            extracted_parameters={
                                "name": "Credit Card EMI Loan",
                                "principal": prior_amt,
                                "interest_rate": 16.0,
                                "monthly_emi": emi_val,
                                "tenure_months": 12,
                                "remaining_months": 12
                            }
                        )
                    else:
                        return ParsedIntent(
                            intent_type="WRITE_ACTION",
                            action_type="create_transaction",
                            target_entity="transaction",
                            confidence=0.95,
                            extracted_parameters={
                                "amount": prior_amt,
                                "type": "expense",
                                "category": "Debt Repayment",
                                "description": "Loan Repayment"
                            }
                        )
                elif ql in ["3", "3.", "3. update it", "option 3"] or "income" in ql or "disbursement" in ql:
                    return ParsedIntent(
                        intent_type="WRITE_ACTION",
                        action_type="create_transaction",
                        target_entity="transaction",
                        confidence=0.95,
                        extracted_parameters={
                            "amount": prior_amt,
                            "type": "income",
                            "category": "Loan Inflow",
                            "description": "Loan Proceeds Received"
                        }
                    )
                elif ql in ["4", "4.", "4. update it", "option 4"] or "repayment" in ql:
                    return ParsedIntent(
                        intent_type="WRITE_ACTION",
                        action_type="create_transaction",
                        target_entity="transaction",
                        confidence=0.95,
                        extracted_parameters={
                            "amount": prior_amt,
                            "type": "expense",
                            "category": "Debt Repayment",
                            "description": "Credit Card Repayment Made"
                        }
                    )

        # 5A. Repay Debt / Mark Loan as Repaid: "Mark the ₹1,000 loan as repaid", "repaid 1000 loan to friend"
        is_repay_cmd = (
            any(p in ql for p in ["as repaid", "as paid", "mark the loan", "mark loan", "mark debt", "repaid the loan", "repaid loan", "paid back loan", "cleared loan", "closed loan"])
            or ("repaid" in ql and ("loan" in ql or "debt" in ql))
            or ("paid" in ql and ("loan" in ql or "debt" in ql) and any(w in ql for w in ["back", "off", "as repaid", "full"]))
        )
        if is_repay_cmd:
            amt = cls._extract_amount(ql)
            counterparty = cls._extract_counterparty(ql)
            target_name = f"Loan with {counterparty}" if counterparty else (f"Loan of ₹{amt:,.0f}" if amt else "Active Loan")
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="repay_debt",
                target_entity="liability",
                confidence=0.95,
                extracted_parameters={
                    "amount": amt,
                    "counterparty": counterparty,
                    "name": target_name
                }
            )

        # 5B. Show Money Lent / Receivables: "Show all money I have lent to others", "Who owes me money?", "Show receivables"
        if any(p in ql for p in ["money i have lent", "money i lent", "money lent to others", "money lent", "who owes me", "who owes me money", "show my receivables", "show all receivables", "list receivables"]):
            return ParsedIntent(
                intent_type="READ_ANALYSIS",
                action_type="list_receivables",
                target_entity="liability",
                confidence=0.95,
                extracted_parameters={"query_type": "receivables"}
            )

        # 5C. Show Debts / Liabilities: "What are my debts?", "Show all my debts", "Who do I owe?"
        if any(p in ql for p in ["what are my debts", "show all my debts", "show my debts", "who do i owe", "list my debts", "list all debts", "tell me what is the debt", "what is the debt", "my active debts"]):
            return ParsedIntent(
                intent_type="READ_ANALYSIS",
                action_type="list_debts",
                target_entity="liability",
                confidence=0.95,
                extracted_parameters={"query_type": "debts"}
            )

        # 5D. Debt & Loan Creation: "Add a debt of ₹1,000 to my friend at 1% monthly interest", "My friend owes me ₹5,000", "I borrowed ₹10,000 from my brother"
        is_debt_creation = (
            any(p in ql for p in [
                "add a debt", "add debt", "record debt", "new debt", "track debt", "add liability",
                "add a loan", "add loan", "record loan", "new loan", "took a loan", "took loan",
                "borrowed", "owes me", "owe me", "lent to", "lent", "lend to", "i lent",
                "home loan", "car loan", "education loan", "personal loan"
            ])
            and not any(p in ql for p in ["repay", "paid", "what is my debt", "who do i owe", "show all money", "who owes me"])
        )
        if is_debt_creation:
            amt = cls._extract_amount(ql)
            dtype = cls._detect_debt_type(ql)
            counterparty = cls._extract_counterparty(ql)
            rate, period, is_rate_ambiguous = cls._extract_interest_info(ql)
            tenure = cls._extract_months(ql) or 12

            # 1. Check if principal amount is missing
            if amt is None:
                return ParsedIntent(
                    intent_type="AMBIGUOUS",
                    is_ambiguous=True,
                    confidence=0.9,
                    clarification_question="How much is the loan or debt amount you would like to record?",
                    clarification_options=["₹1,000", "₹5,000", "₹10,000"]
                )

            # 2. Check if counterparty is missing
            if not counterparty:
                loan_type_match = next((t for t in ["home loan", "car loan", "education loan", "personal loan", "gold loan"] if t in ql), None)
                if loan_type_match:
                    counterparty = loan_type_match.title()
                else:
                    question = "Who is the borrower who owes you this money?" if dtype == "receivable" else "Who did you borrow this debt from, or who is the lender/counterparty?"
                    return ParsedIntent(
                        intent_type="AMBIGUOUS",
                        is_ambiguous=True,
                        confidence=0.9,
                        extracted_parameters={"amount": amt, "debt_type": dtype},
                        clarification_question=question,
                        clarification_options=["Friend", "Brother", "Colleague", "Bank"]
                    )

            # 3. Check if interest rate period is ambiguous (e.g. "1% interest" without specifying monthly vs annual)
            if is_rate_ambiguous and rate is not None:
                annual_equiv = round(rate * 12, 2)
                loan_label = f"Money Lent to {counterparty}" if dtype == "receivable" else f"Debt to {counterparty}"
                options = [
                    {
                        "id": "opt_monthly_interest",
                        "label": f"{rate:g}% Monthly Interest ({annual_equiv:g}% per year)",
                        "action_type": "create_debt",
                        "target_entity": "liability",
                        "parameters": {
                            "principal": amt,
                            "interest_rate": annual_equiv,
                            "interest_period": "monthly",
                            "counterparty": counterparty,
                            "debt_type": dtype,
                            "tenure_months": tenure,
                            "name": loan_label
                        }
                    },
                    {
                        "id": "opt_annual_interest",
                        "label": f"{rate:g}% Annual Interest ({rate:g}% per year)",
                        "action_type": "create_debt",
                        "target_entity": "liability",
                        "parameters": {
                            "principal": amt,
                            "interest_rate": rate,
                            "interest_period": "annual",
                            "counterparty": counterparty,
                            "debt_type": dtype,
                            "tenure_months": tenure,
                            "name": loan_label
                        }
                    }
                ]
                return ParsedIntent(
                    intent_type="AMBIGUOUS",
                    is_ambiguous=True,
                    confidence=0.95,
                    extracted_parameters={"amount": amt, "interest_rate": rate, "counterparty": counterparty, "debt_type": dtype},
                    clarification_question=f"Is the {rate:g}% interest rate monthly (or per month) or annual (per year)?",
                    clarification_options=[opt["label"] for opt in options],
                    structured_options=options
                )

            # 4. Defaults for complete debt creation
            effective_rate = rate if rate is not None else 0.0
            interest_period = period if period is not None else "annual"
            if interest_period == "monthly" and rate is not None:
                effective_annual_rate = round(rate * 12, 2)
            else:
                effective_annual_rate = effective_rate

            # Monthly EMI calculation approximation
            monthly_rate = (effective_annual_rate / 100) / 12
            if monthly_rate > 0 and tenure > 0:
                emi = (amt * monthly_rate * ((1 + monthly_rate) ** tenure)) / (((1 + monthly_rate) ** tenure) - 1)
            else:
                emi = 0.0

            loan_name = f"Money Lent to {counterparty}" if dtype == "receivable" else f"Debt to {counterparty}"

            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="create_debt",
                target_entity="liability",
                confidence=0.94,
                extracted_parameters={
                    "name": loan_name,
                    "counterparty": counterparty,
                    "principal": amt,
                    "interest_rate": effective_annual_rate,
                    "interest_period": interest_period,
                    "monthly_emi": round(float(emi), 2),
                    "tenure_months": tenure,
                    "remaining_months": tenure,
                    "debt_type": dtype
                }
            )

        # 6. Recurring Transactions: Pause or Cancel
        if any(p in ql for p in ["pause subscription", "pause my", "pause recurring", "put on hold"]):
            item_name = cls._extract_subscription_name(ql, action="pause")
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="pause_recurring_commitment",
                target_entity="recurring_transaction",
                confidence=0.9,
                extracted_parameters={"name": item_name}
            )

        if any(p in ql for p in ["cancel subscription", "cancel my", "delete recurring"]):
            item_name = cls._extract_subscription_name(ql, action="cancel")
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="cancel_recurring_commitment",
                target_entity="recurring_transaction",
                confidence=0.9,
                extracted_parameters={"name": item_name}
            )

        # 7. Add Recurring Commitment / Bill: "Add electricity bill of ₹2,500 due on the 28th"
        if any(p in ql for p in ["recurring", "monthly bill", "electricity bill", "subscription", "gym membership", "wifi bill", "due on the", "due on"]):
            amt = cls._extract_amount(ql)
            if amt and ("bill" in ql or "subscription" in ql or "membership" in ql or "due" in ql):
                name = cls._extract_bill_name(ql)
                cat = cls._infer_category(name)
                next_date = cls._extract_due_date(ql)
                return ParsedIntent(
                    intent_type="WRITE_ACTION",
                    action_type="create_recurring_commitment",
                    target_entity="recurring_transaction",
                    confidence=0.9,
                    extracted_parameters={
                        "name": name,
                        "amount": amt,
                        "category": cat,
                        "frequency": "monthly",
                        "transaction_type": "expense",
                        "next_expected_date": str(next_date)
                    }
                )

        # 8. Record Income: "I received ₹45,000 salary today", "Record ₹15,000 bonus"
        if any(p in ql for p in ["received", "salary", "earned", "got paid", "consulting income", "freelance income", "dividend received"]):
            amt = cls._extract_amount(ql)
            if amt:
                cat = "Salary" if "salary" in ql else ("Freelance" if "freelance" in ql or "consulting" in ql else "Income")
                desc = cls._extract_description(q, default="Income Inflow")
                return ParsedIntent(
                    intent_type="WRITE_ACTION",
                    action_type="create_transaction",
                    target_entity="transaction",
                    confidence=0.92,
                    extracted_parameters={
                        "amount": amt,
                        "type": "income",
                        "category": cat,
                        "description": desc,
                        "date": str(date.today())
                    }
                )

        # 9. Record Expense / Bank Transaction:
        # e.g. "add a bank transcation of 100rs sentt mohan", "Record ₹3,500 spent on groceries", "Spent 450 on coffee", "Add transaction 500 for dinner"
        is_txn_write = any(p in ql for p in [
            "spent", "spent on", "record expense", "add expense", "bought", "paid for", "paid ₹", "record ₹",
            "transaction", "transcation", "bank transaction", "bank transcation", "add payment", "record payment",
            "sent to", "sentt"
        ])
        if is_txn_write and not any(p in ql for p in ["whom i want to pay", "want to pay", "who do i owe", "what is the debt", "what are my debts", "budget"]):
            amt = cls._extract_amount(ql)
            if amt:
                cat = cls._infer_category(ql)
                desc = cls._extract_description(q, default=f"Payment on {cat}")
                return ParsedIntent(
                    intent_type="WRITE_ACTION",
                    action_type="create_transaction",
                    target_entity="transaction",
                    confidence=0.95,
                    extracted_parameters={
                        "amount": amt,
                        "type": "expense",
                        "category": cat,
                        "description": desc,
                        "date": str(date.today())
                    }
                )

        # 10. Budget Update: "Increase my grocery budget to ₹7,00,0", "Set food budget to 12000"
        if "budget" in ql and any(p in ql for p in ["increase", "decrease", "set", "update", "change", "allocate", "add"]):
            amt = cls._extract_amount(ql)
            cat = cls._infer_category(ql)
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="update_budget",
                target_entity="budget",
                confidence=0.88,
                extracted_parameters={
                    "category": cat,
                    "target_amount": amt or 10000.0,
                    "is_relative": False
                }
            )

        # 11. Goals: "add finacial goal", "add financial goal", "create vacation goal of 1,00,000 by December 2026"
        is_goal_trigger = (
            any(w in ql for w in ["goal", "goals", "finacial goal", "financial goal"]) and
            any(p in ql for p in ["add", "create", "set", "new", "save for", "start", "track", "make"])
        ) or (
            ql.strip() in ["add financial goal", "add finacial goal", "add a goal", "create goal", "new goal", "add goal"]
        )
        if is_goal_trigger and not any(w in ql for w in ["what are my goals", "list my goals", "goals summary", "tell me my goals"]):
            amt = cls._extract_amount(ql) or 100000.0
            name = cls._extract_goal_name(ql)
            target_date = cls._extract_future_date(ql)
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="create_savings_goal",
                target_entity="goal",
                confidence=0.92,
                extracted_parameters={
                    "name": name,
                    "target_amount": amt,
                    "target_date": str(target_date),
                    "category": "custom",
                    "priority": "medium"
                }
            )

        # 12. Investments / Asset Holdings: "Add investment of 50000 in mutual fund", "Record asset holding"
        if (any(p in ql for p in ["add investment", "record investment", "add asset", "buy mutual fund", "add mutual fund", "invested in", "add stock", "record asset"])
            and not any(p in ql for p in ["compare", "what are my investments", "list my investments", "portfolio"])):
            amt = cls._extract_amount(ql) or 50000.0
            name = cls._extract_investment_name(ql)
            cat = cls._infer_asset_category(ql)
            ret_rate = 12.0 if "equity" in ql or "stock" in ql or "mf" in ql else (7.0 if "fd" in ql or "debt" in ql else 9.0)
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="create_asset_holding",
                target_entity="asset",
                confidence=0.9,
                extracted_parameters={
                    "name": name,
                    "category": cat,
                    "invested_value": amt,
                    "current_value": amt,
                    "expected_return_rate": ret_rate
                }
            )

        # 13. Tax Regime Update: "Switch to new tax regime", "Set tax regime to old"
        if any(p in ql for p in ["switch to new regime", "switch to old regime", "set tax regime to new", "set tax regime to old", "change regime to new", "change regime to old"]):
            new_regime = "new" if "new" in ql else "old"
            return ParsedIntent(
                intent_type="WRITE_ACTION",
                action_type="update_tax_regime",
                target_entity="profile",
                confidence=0.92,
                extracted_parameters={"tax_regime": new_regime}
            )

        # Default: READ_ANALYSIS for all questions, calculations, affordability, health, taxes, FIRE, etc.
        return ParsedIntent(
            intent_type="READ_ANALYSIS",
            confidence=0.95
        )

    # --- Helper Extractors ---

    @classmethod
    def _extract_amount(cls, text: str) -> Optional[float]:
        # Handle formats: ₹1,000, 1000, 1.5 lakh, 50k
        m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", text, re.IGNORECASE)
        if m_k:
            return float(m_k.group(1)) * 1000.0

        m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b", text, re.IGNORECASE)
        if m_lakh:
            return float(m_lakh.group(1)) * 100000.0

        m_num = re.search(r"(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(?:rs\.?|inr)?", text, re.IGNORECASE)
        if m_num:
            val_str = m_num.group(1).replace(",", "")
            try:
                val = float(val_str)
                if val > 0:
                    return val
            except Exception:
                pass
        return None

    @classmethod
    def _extract_interest_rate(cls, text: str) -> Optional[float]:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:interest|rate|p\.?a\.?)?", text, re.IGNORECASE)
        if m:
            return float(m.group(1))
        return None

    @classmethod
    def _extract_months(cls, text: str) -> Optional[int]:
        m_yr = re.search(r"(\d+)\s*(?:years?|yrs?)\b", text, re.IGNORECASE)
        if m_yr:
            return int(m_yr.group(1)) * 12
        m_mo = re.search(r"(\d+)\s*(?:months?|mos?)\b", text, re.IGNORECASE)
        if m_mo:
            return int(m_mo.group(1))
        return None

    @classmethod
    def _extract_loan_name(cls, text: str) -> str:
        for t in ["home loan", "car loan", "auto loan", "vehicle loan", "education loan", "personal loan", "credit card loan", "gold loan"]:
            if t in text:
                return t.title()
        return "Personal Loan"

    @classmethod
    def _extract_subscription_name(cls, text: str, action: str) -> str:
        # e.g. "Pause my gym subscription" -> "Gym"
        clean = re.sub(rf"(?i){action}\s+(?:my\s+)?", "", text)
        clean = re.sub(r"(?i)\s+(?:subscription|membership|recurring|plan|service).*", "", clean)
        return clean.strip().title() or "Subscription"

    @classmethod
    def _extract_bill_name(cls, text: str) -> str:
        for b in ["electricity bill", "water bill", "wifi bill", "broadband bill", "gym membership", "netflix subscription", "spotify", "rent payment", "mobile recharge"]:
            if b in text:
                return b.title()
        m = re.search(r"([a-zA-Z\s]+)\s+bill", text, re.IGNORECASE)
        if m:
            return f"{m.group(1).strip().title()} Bill"
        return "Monthly Bill"

    @classmethod
    def _infer_category(cls, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["sent to", "sentt", "transfer", "paid to", "peer", "friend", "mohan", "rahul"]):
            return "Transfers & Peer Payments"
        if any(w in t for w in ["groceries", "grocery", "supermarket", "vegetables", "bigbasket"]):
            return "Groceries"
        if any(w in t for w in ["dining", "restaurant", "swiggy", "zomato", "coffee", "starbucks", "food"]):
            return "Food & Dining"
        if any(w in t for w in ["electric", "water", "utility", "wifi", "broadband", "gas"]):
            return "Utilities"
        if any(w in t for w in ["rent", "housing", "maintenance", "pg"]):
            return "Housing"
        if any(w in t for w in ["fuel", "petrol", "diesel", "uber", "ola", "metro", "transport"]):
            return "Transportation"
        if any(w in t for w in ["gym", "fitness", "health", "doctor", "medicine"]):
            return "Health & Fitness"
        if any(w in t for w in ["netflix", "prime", "movie", "spotify", "entertainment"]):
            return "Entertainment"
        return "General Expense"

    @classmethod
    def _extract_description(cls, text: str, default: str) -> str:
        # Check for recipient pattern: sent to <name>, sentt <name>, paid to <name>, for <purpose>
        m_sent = re.search(r"(?:sent\s+to|sentt\s+to|sentt|sent|paid\s+to|transferred\s+to)\s+([a-zA-Z\s]{2,30})", text, re.IGNORECASE)
        if m_sent:
            recipient = m_sent.group(1).strip().title()
            return f"Payment sent to {recipient}"

        m_for = re.search(r"(?:for|on)\s+([a-zA-Z\s]{2,30})", text, re.IGNORECASE)
        if m_for:
            return m_for.group(1).strip().title()

        cleaned = re.sub(
            r"(?i)(?:please\s+)?(?:record|add|spent|received|bought|a\s+bank\s+transaction\s+of|a\s+bank\s+transcation\s+of|bank\s+transaction\s+of|bank\s+transcation\s+of|transaction\s+of|transcation\s+of)\s*",
            "",
            text,
        ).strip()
        if len(cleaned) > 3:
            return cleaned[:60]
        return default

    @classmethod
    def _extract_due_date(cls, text: str) -> date:
        today = date.today()
        m_day = re.search(r"due\s+(?:on\s+)?(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?", text, re.IGNORECASE)
        if m_day:
            day_num = int(m_day.group(1))
            day_num = min(28, max(1, day_num))  # safe day for all months
            # If day has already passed this month, project next month
            if today.day > day_num:
                month = today.month + 1 if today.month < 12 else 1
                year = today.year if today.month < 12 else today.year + 1
                return date(year, month, day_num)
            return date(today.year, today.month, day_num)
        return today + timedelta(days=7)

    @classmethod
    def _extract_future_date(cls, text: str) -> date:
        today = date.today()
        # Look for year
        m_yr = re.search(r"\b(202[5-9]|203[0-9])\b", text)
        target_year = int(m_yr.group(1)) if m_yr else today.year + 1

        # Look for month
        months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        target_month = 12
        for idx, m_name in enumerate(months, 1):
            if m_name in text:
                target_month = idx
                break

        return date(target_year, target_month, 28)

    @classmethod
    def _extract_goal_name(cls, text: str) -> str:
        for g in ["vacation", "home down payment", "car down payment", "higher education", "wedding", "emergency fund", "retirement", "car", "house", "bike", "laptop", "europe trip"]:
            if g in text.lower():
                return g.title()
        m = re.search(r"(?:goal for|goal to|save for)\s+([a-zA-Z\s]{3,25})", text, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
        return "Financial Goal"

    @classmethod
    def _extract_investment_name(cls, text: str) -> str:
        t = text.lower()
        if "mutual fund" in t or "mf" in t:
            return "Nifty 50 Index Mutual Fund"
        if "gold" in t:
            return "Sovereign Gold Bond"
        if "fd" in t or "fixed deposit" in t:
            return "Bank Fixed Deposit"
        if "stock" in t or "equity" in t:
            return "Direct Equity Portfolio"
        return "Investment Holding"

    @classmethod
    def _infer_asset_category(cls, text: str) -> str:
        t = text.lower()
        if "gold" in t:
            return "gold"
        if "fd" in t or "fixed deposit" in t:
            return "fd"
        if "debt" in t or "bond" in t:
            return "debt_mf"
        if "stock" in t or "equity" in t or "shares" in t:
            return "stocks"
        if "crypto" in t:
            return "crypto"
        if "real estate" in t or "property" in t or "land" in t:
            return "real_estate"
        return "equity_mf"

    @classmethod
    def _extract_counterparty(cls, text: str) -> Optional[str]:
        t = text.strip()
        # 1. "my friend owes me", "rohan owes me", "brother owes me"
        m_owes = re.search(r"([a-zA-Z\s]+?)\s+owes\s+me\b", t, re.IGNORECASE)
        if m_owes:
            cp = m_owes.group(1).strip()
            cp = re.sub(r"(?i)^(my|a|an)\s+", "", cp).strip()
            if cp:
                return cp.title()

        # 2. "to/from/with my friend", "to/from/with brother", "to/from/with Rohan"
        m_prep = re.search(r"\b(?:to|from|with)\s+(?:my\s+)?([a-zA-Z\s]{2,30}?)(?:\s+(?:at|with|for|due|on|interest)\b|[.,!?]|$)", t, re.IGNORECASE)
        if m_prep:
            candidate = m_prep.group(1).strip()
            candidate = re.sub(r"(?i)^(my|a|an)\s+", "", candidate).strip()
            if candidate.lower() not in ["interest", "rate", "the", "a", "an", "debt", "loan", "bank"] and len(candidate) >= 2:
                return candidate.title()

        # 3. "lent/borrowed ... to/from <name>"
        m_lb = re.search(r"\b(?:lent|borrowed|owe|paying)\s+(?:₹?\s*\d+[\d,.]*\s*(?:rs|inr|k|lakh)?\s+)?(?:to|from)\s+(?:my\s+)?([a-zA-Z\s]{2,30}?)(?:\s+(?:at|with|for|due|on|interest)\b|[.,!?]|$)", t, re.IGNORECASE)
        if m_lb:
            candidate = m_lb.group(1).strip()
            candidate = re.sub(r"(?i)^(my|a|an)\s+", "", candidate).strip()
            if candidate.lower() not in ["interest", "rate", "the", "a", "an", "debt", "loan"] and len(candidate) >= 2:
                return candidate.title()

        # 4. Known relationship words
        for rel in ["friend", "brother", "sister", "colleague", "cousin", "father", "mother", "uncle", "aunt", "roommate"]:
            if re.search(rf"\b{rel}\b", t, re.IGNORECASE):
                return rel.title()

        return None

    @classmethod
    def _detect_debt_type(cls, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["owes me", "owe me", "lent to", "lent", "lend", "lending", "gave loan", "given loan", "money lent", "receivable", "i gave a loan", "loan i gave", "money i lent"]):
            return "receivable"
        return "payable"

    @classmethod
    def _extract_interest_info(cls, text: str) -> Tuple[Optional[float], Optional[str], bool]:
        """
        Extracts (rate, period, is_ambiguous).
        period: 'monthly', 'annual', or None
        is_ambiguous is True when interest rate is specified (e.g. 1%) but neither
        'monthly' nor 'annual' (or equivalent) is stated.
        """
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:interest|rate)?", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(?:interest\s+(?:of|at)\s*|at\s+)(\d+(?:\.\d+)?)\s*%", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(?:interest\s+(?:of|at)\s*|at\s+)(\d+(?:\.\d+)?)\s*(?:percent|pct)\b", text, re.IGNORECASE)

        if not m:
            return None, None, False

        rate = float(m.group(1))
        t = text.lower()

        # Explicit monthly signals
        has_monthly = any(k in t for k in ["monthly", "per month", "p.m.", "pm\b", "/month", "/mo", "each month"])
        # Explicit annual signals
        has_annual = any(k in t for k in ["annual", "yearly", "per year", "per annum", "p.a.", "pa\b", "/year", "/yr", "annually"])
        if not has_annual and re.search(r"\b(?:for|in)?\s*\d+\s*(?:years?|yrs?)\b", t):
            has_annual = True
        if not has_annual and any(k in t for k in ["car loan", "home loan", "education loan", "mortgage", "bank loan"]):
            has_annual = True

        if has_monthly and not has_annual:
            return rate, "monthly", False
        elif has_annual and not has_monthly:
            return rate, "annual", False
        elif has_monthly and has_annual:
            return rate, "monthly", False
        else:
            return rate, None, True

