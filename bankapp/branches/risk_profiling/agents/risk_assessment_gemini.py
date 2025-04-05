import os
import json
from google import genai
from google.genai import types

class GeminiRiskAssessmentAgent:
    def __init__(self):
        """Initialize the risk assessment agent with Gemini API."""
        # Use Google API key from environment
        api_key = os.environ.get("GOOGLE_API_KEY")
        try:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-1.5-pro"
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
    
    def assess_transaction_risks_batch(self, transactions):
        """
        Assess the risk of a batch of transactions using Gemini LLM
        
        Args:
            transactions: A list of transaction dictionaries
            
        Returns:
            List of transaction dictionaries with added risk assessment fields
        """
        if not transactions:
            return transactions
        
        # Create a detailed prompt for the LLM
        transactions_str = json.dumps(transactions, indent=2)
        
        # Using the rules as context and guidance for the model
        rules = self._get_rules()
        
        prompt = f"""You are an expert financial risk assessment agent for a bank's transaction monitoring system.

TASK: Analyze the following batch of banking transactions and provide a risk assessment for each one.

TRANSACTION DATA:
{transactions_str}

RISK ASSESSMENT RULES:
{rules}

ADDITIONAL RISK FACTORS TO CONSIDER:
1. Unusual transaction amounts compared to the account's history
2. Transactions to high-risk jurisdictions/locations
3. Unusual transaction patterns (frequency, timing)
4. Account age and KYC status
5. Previous fraud indicators
6. Transactions creating negative balances
7. Smurfing indicators (multiple small transactions to avoid detection)

For EACH transaction, provide a JSON object with the following fields:
- transaction_id: The ID of the transaction
- risk_score: A number from 0-100 indicating risk level
- risk_category: "Low" (0-30), "Medium" (31-70), "High" (71-90), or "Very High" (91-100)
- risk_explanation: A detailed explanation of why this risk score was assigned

Your response should be a valid JSON array containing one object for each transaction.
"""
        
        # Generate content using Gemini
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4096,
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # Parse the response as JSON
            result_text = response.text
            
            # Clean the response text if it contains markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse the JSON
            risk_assessments = json.loads(result_text)
            
            # Map the risk assessments back to the original transactions
            risk_mapping = {assessment['transaction_id']: assessment for assessment in risk_assessments}
            
            # Add risk assessments to the original transactions
            for transaction in transactions:
                transaction_id = transaction.get('transaction_id')
                if transaction_id in risk_mapping:
                    assessment = risk_mapping[transaction_id]
                    transaction['risk_score'] = assessment.get('risk_score', 0)
                    transaction['risk_category'] = assessment.get('risk_category', 'Low')
                    transaction['risk_explanation'] = assessment.get('risk_explanation', '')
            
            return transactions
            
        except Exception as e:
            print(f"Error generating risk assessment: {e}")
            # If there's an error, add default risk values
            for transaction in transactions:
                transaction['risk_score'] = 50
                transaction['risk_category'] = "Medium"
                transaction['risk_explanation'] = "Unable to generate risk assessment due to an error."
            
            return transactions
    
    def _get_rules(self):
        """Get the risk assessment rules as a string"""
        return """
Rule 1: If transaction_amount > 50000, add risk score 70, category "High", factor "Unusually large transaction amount"
Rule 2: If smurfing_indicator == 1, add risk score 80, category "High", factor "Potential structuring/smurfing behavior detected"
Rule 3: If previous_fraud_flag == 1, add risk score 90, category "Very High", factor "Account previously involved in fraudulent activity"
Rule 4: If account_age_days < 30, add risk score 60, category "Medium", factor "Account is relatively new"
Rule 5: If kyc_status == 'NONE', add risk score 50, category "Medium", factor "Account has no KYC verification"
Rule 6: If new_balance < 0, add risk score 70, category "High", factor "Transaction resulted in negative balance"
Rule 7: If label_for_fraud == 1, add risk score 95, category "Very High", factor "Transaction explicitly flagged as fraudulent"
""" 