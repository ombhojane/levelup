import os
import json
import random
import re
import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
from google import genai
from google.genai import types

class TransactionChatAssistant:
    def __init__(self):
        """Initialize the chat assistant with Gemini API."""
        # Look for either GEMINI_API_KEY or GOOGLE_API_KEY
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.api_available = False
        
        if not api_key:
            print("WARNING: No API key found. Using fallback responses.")
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-1.5-pro"  # Fallback to a standard model if 02-05 isn't available
            
            # Check available models and use the most appropriate one
            try:
                models = self.client.list_models()
                model_names = [model.name for model in models]
                
                # Try to use these models in order of preference
                preferred_models = [
                    "gemini-2.0-pro-exp-02-05", 
                    "gemini-1.5-pro", 
                    "gemini-1.0-pro"
                ]
                
                for model_name in preferred_models:
                    if any(model_name in name for name in model_names):
                        self.model = model_name
                        break
                
                self.api_available = True
                
            except Exception as e:
                print(f"Warning: Could not list models: {e}")
                # Still consider API available since we were able to create a client
                self.api_available = True
            
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
    
    def _classify_query(self, query):
        """
        Determine if the query is transaction-related.
        
        Args:
            query (str): The user's query
            
        Returns:
            str: 'TRANSACTIONS' or 'NO_TRANSACTIONS'
        """
        if not self.api_available:
            # Default to NO_TRANSACTIONS for simplicity
            return 'NO_TRANSACTIONS'
        
        # Keywords indicating transaction-related queries
        transaction_keywords = [
            'transaction', 'transactions', 'spending', 'purchase', 'purchases', 'payment', 'payments',
            'deposit', 'withdraw', 'transfer', 'expense', 'expenses', 'income', 'balance', 'spent',
            'received', 'paid', 'money flow', 'account activity', 'recent activity', 'show me', 'analyze',
            'analysis', 'chart', 'graph', 'plot', 'visualization', 'report', 'summary', 'statistics',
            'trend', 'pattern', 'compare', 'filter', 'categorize', 'group', 'total'
        ]
        
        # Check if any transaction keyword is in the query
        query_lower = query.lower()
        
        # Simple rule-based classification
        for keyword in transaction_keywords:
            if keyword in query_lower:
                return 'TRANSACTIONS'
        
        try:
            # Use Gemini for more sophisticated classification
            prompt = f"""Given the user query below, classify it as either 'TRANSACTIONS' or 'NO_TRANSACTIONS'.
Choose 'TRANSACTIONS' if the user is asking for data analysis, visualization, or specific information about their transaction history.
Choose 'NO_TRANSACTIONS' if the user is asking general questions about fraud, security, or banking that don't require analysis of their specific transaction data.

USER QUERY: {query}

RESPOND WITH ONLY ONE WORD: 'TRANSACTIONS' OR 'NO_TRANSACTIONS'."""
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.0,  # Using lowest temperature for deterministic results
                max_output_tokens=10,
                response_mime_type="text/plain",
            )
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            result = response.text.strip().upper()
            
            # Ensure valid response
            if result not in ['TRANSACTIONS', 'NO_TRANSACTIONS']:
                # Default to NO_TRANSACTIONS for invalid responses
                return 'NO_TRANSACTIONS'
                
            return result
            
        except Exception as e:
            print(f"Error in query classification: {e}")
            # Default to NO_TRANSACTIONS on error
            return 'NO_TRANSACTIONS'

    def generate_response(self, query, transactions_data, customer_id):
        """
        Generate a response to a query about transaction data.
        
        Args:
            query (str): The user's query
            transactions_data (list): List of transaction dictionaries
            customer_id (str): The ID of the customer
            
        Returns:
            dict: Response containing text, HTML, and visualization data
        """
        # If API is not available, use fallback response
        if not self.api_available:
            fallback_response = self._generate_fallback_response(query, transactions_data, customer_id)
            return {
                'response': fallback_response,
                'html_response': fallback_response,
                'is_transaction_query': False,
                'canvas_data': None
            }
        
        # Determine if this is a transaction-related query
        query_type = self._classify_query(query)
        is_transaction_query = (query_type == 'TRANSACTIONS')
        
        # Return full response with visualization if transaction data is requested
        if is_transaction_query and transactions_data:
            return self._generate_transaction_analysis(query, transactions_data, customer_id)
        elif is_transaction_query and not transactions_data:
            # Handle the case where transaction data is requested but not available
            response = "I'd like to analyze your transaction data, but it seems I don't have access to it at the moment. Please try again later or contact customer support if this issue persists."
            return {
                'response': response,
                'html_response': response,
                'is_transaction_query': True,
                'canvas_data': None
            }
        else:
            # Non-transaction query
            direct_response = self._generate_direct_response(query)
            return {
                'response': direct_response,
                'html_response': direct_response,
                'is_transaction_query': False,
                'canvas_data': None
            }
    
    def _generate_transaction_analysis(self, query, transactions_data, customer_id):
        """
        Generate code and analysis for transaction-related queries.
        
        Args:
            query (str): The user's query
            transactions_data (list): List of transaction dictionaries
            customer_id (str): The ID of the customer
            
        Returns:
            dict: Response with text, HTML, and visualization data
        """
        try:
            # Create dataframe from transactions
            df = pd.DataFrame(transactions_data)
            
            # Generate Python code to analyze the data
            code_prompt = f"""You are an expert Python developer specializing in financial data analysis with pandas and matplotlib.

TASK: Generate Python code to analyze transaction data based on the user's query.

USER QUERY: {query}

TRANSACTION DATA SCHEMA:
```python
# Sample of the dataframe schema (first few rows shown):
{df.head(2).to_string()}

# Available columns:
{', '.join(df.columns.tolist())}
```
IMPORTANT: All monetary values are in Indian Rupees (₹). Make sure everywhere use the ₹ symbol instead of $ and refer to the currency as "rupees" not "dollars".


INSTRUCTIONS:
1. Write Python code that analyzes the transaction data to answer the user's query.
2. The dataframe is already available as variable 'df'.
3. Your code should:
   - Include clear comments explaining what it's doing
   - Generate visualizations when appropriate (using matplotlib)
   - For visualization, use plt.tight_layout() and save the figure to a BytesIO object as explained below
   - If the user is asking to see transaction details or a specific subset of transactions, filter the dataframe accordingly and include it in the output

For visualizations, use the following code pattern:
```python
import io
import base64
import matplotlib.pyplot as plt

# [... your analysis code ...]

# Creating visualization
plt.figure(figsize=(10, 5))
# [... your plotting code ...]
plt.title("Meaningful Title")
plt.tight_layout()

# Save figure to BytesIO object
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)
img_str = base64.b64encode(buffer.read()).decode()
plt.close()

# Return data including visualization - IMPORTANT: Use proper dictionary syntax
output = {{
    "summary": "A brief textual summary of the findings",
    "visualization": img_str
}}
```

IF THE USER IS REQUESTING TO SEE TRANSACTION DETAILS OR DATA:
Generate a filtered dataframe as needed for the query, and include it in the output dictionary like this:
```python
# Filter the dataframe based on the query
filtered_df = df[df['label_for_fraud'] == 1]  # Example: filtering for suspicious transactions

# Format the dataframe for display
# Limit to 20 rows max to avoid overwhelming the UI
display_df = filtered_df.head(20)

# Convert to HTML for rendering in the canvas
df_html = display_df.to_html(classes='table table-striped table-hover', border=0, index=False)

# Return data including both filtered dataframe and optionally a visualization
output = {{
    "summary": "A brief textual summary of the findings",
    "visualization": img_str if 'img_str' in locals() else None,
    "dataframe_html": df_html
}}
```

RESPOND ONLY WITH PYTHON CODE, NO EXPLANATIONS OR COMMENTS OUTSIDE THE CODE BLOCK.
"""
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=code_prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
                response_mime_type="text/plain",
            )
            
            code_response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # Extract Python code from response
            code_text = code_response.text
            
            # Clean up code - extract just the Python code if it's within markdown blocks
            if "```python" in code_text and "```" in code_text:
                code_text = re.search(r"```python\n(.*?)```", code_text, re.DOTALL).group(1)
            elif "```" in code_text:
                code_text = re.search(r"```\n(.*?)```", code_text, re.DOTALL).group(1)
            
            # Fix potential string formatting issues in the code
            # Look for the output dictionary and ensure it's formatted correctly
            code_text = self._fix_output_format(code_text)
            
            # Create a global/local scope for code execution
            global_vars = {'df': df, 'pd': pd, 'plt': plt, 'io': io, 'base64': base64}
            local_vars = {}
            
            # Execute the code
            print("Executing generated Python code:")
            print(code_text)
            
            try:
                exec(code_text, global_vars, local_vars)
                
                # Extract the output
                if 'output' in local_vars:
                    analysis_output = local_vars['output']
                    visualization_b64 = analysis_output.get('visualization')
                    summary = analysis_output.get('summary', 'Analysis complete, see visualization for details.')
                else:
                    # If no output provided, create a fallback visualization
                    visualization_b64, summary = self._create_fallback_visualization(df, query)
            except Exception as code_exec_error:
                print(f"Error executing generated code: {code_exec_error}")
                # Create fallback visualization if code execution fails
                visualization_b64, summary = self._create_fallback_visualization(df, query)
            
            # Generate a more detailed explanation using the analysis results
            explanation_prompt = f"""You are a financial analyst explaining transaction data to a bank customer.

USER QUERY: {query}

ANALYSIS SUMMARY:
{summary}

TRANSACTION DATA OVERVIEW:
Total transactions: {len(df)}
Time period: {df['timestamp'].min() if 'timestamp' in df.columns else 'N/A'} to {df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'}
Total transaction amount: {df['transaction_amount'].sum() if 'transaction_amount' in df.columns else 'N/A'}
Flagged transactions: {df['label_for_fraud'].sum() if 'label_for_fraud' in df.columns else 'N/A'}

Explain the results of the analysis in a clear, concise way that directly answers the user's query.
Include specific numbers and insights from the data.
Your response should be conversational but precise.
"""
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=explanation_prompt)],
                ),
            ]
            
            explanation_response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            explanation_text = explanation_response.text
            
            # Format the response with markdown for better readability
            html_response = f"<h3>Transaction Analysis</h3><p>{explanation_text}</p>"
            
            # Prepare canvas data
            canvas_data = {
                'code': code_text,
                'visualization': visualization_b64,
                'summary': summary
            }
            
            # If dataframe HTML was generated, include it in the canvas data
            if 'output' in local_vars and 'dataframe_html' in local_vars['output']:
                canvas_data['dataframe_html'] = local_vars['output']['dataframe_html']
            
            return {
                'response': explanation_text,
                'html_response': html_response,
                'is_transaction_query': True,
                'canvas_data': canvas_data
            }
            
        except Exception as e:
            error_message = f"I encountered an error while analyzing your transaction data: {str(e)}"
            print(f"Error in transaction analysis: {e}")
            
            # Try to create a basic visualization even when the main function fails
            try:
                df = pd.DataFrame(transactions_data)
                visualization_b64, summary = self._create_fallback_visualization(df, query)
                
                return {
                    'response': f"I've analyzed your transaction data. {summary}",
                    'html_response': f"<h3>Transaction Analysis</h3><p>{summary}</p>",
                    'is_transaction_query': True,
                    'canvas_data': {
                        'visualization': visualization_b64,
                        'summary': summary
                    }
                }
            except Exception as fallback_error:
                print(f"Error creating fallback visualization: {fallback_error}")
                return {
                    'response': error_message,
                    'html_response': error_message,
                    'is_transaction_query': True,
                    'canvas_data': None
                }
                
    def _create_fallback_visualization(self, df, query):
        """
        Create a basic visualization of transaction data when code generation fails.
        
        Args:
            df (DataFrame): Pandas DataFrame with transaction data
            query (str): The user's query
            
        Returns:
            tuple: (base64_visualization, summary_text)
        """
        try:
            plt.figure(figsize=(12, 6))
            
            # Determine what kind of visualization to create based on the query
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ['fraud', 'suspicious', 'unusual']):
                # Fraud-related visualization
                # Create pie chart of fraud vs normal transactions
                fraud_count = df['label_for_fraud'].sum()
                normal_count = len(df) - fraud_count
                
                plt.subplot(1, 2, 1)
                plt.pie([normal_count, fraud_count], 
                       labels=['Normal', 'Flagged'], 
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'])
                plt.title('Transaction Fraud Analysis')
                
                # Bar chart of suspicious transactions by location
                plt.subplot(1, 2, 2)
                fraud_df = df[df['label_for_fraud'] == 1]
                if not fraud_df.empty:
                    location_counts = fraud_df['location_data'].value_counts()
                    location_counts.plot(kind='bar', color='#F44336')
                    plt.title('Suspicious Transactions by Location')
                    plt.xticks(rotation=45)
                else:
                    plt.text(0.5, 0.5, "No suspicious transactions found", 
                             horizontalalignment='center', verticalalignment='center')
                
                summary = f"Found {fraud_count} suspicious transactions out of {len(df)} total transactions."
                
            elif any(keyword in query_lower for keyword in ['category', 'categories', 'spending']):
                # Spending by category
                category_spending = df.groupby('merchant_category')['transaction_amount'].sum().sort_values(ascending=False)
                
                plt.subplot(1, 2, 1)
                category_spending.plot(kind='bar', color='#2196F3')
                plt.title('Spending by Category')
                plt.ylabel('Total Amount')
                plt.xticks(rotation=45)
                
                # Pie chart of top categories
                plt.subplot(1, 2, 2)
                top_categories = category_spending.head(5)
                other_amount = category_spending[5:].sum() if len(category_spending) > 5 else 0
                if other_amount > 0:
                    data = top_categories.tolist() + [other_amount]
                    labels = top_categories.index.tolist() + ['Other']
                else:
                    data = top_categories.tolist()
                    labels = top_categories.index.tolist()
                    
                plt.pie(data, labels=labels, autopct='%1.1f%%')
                plt.title('Top Spending Categories')
                
                top_category = category_spending.index[0] if not category_spending.empty else "N/A"
                summary = f"Your highest spending category is {top_category}, with ${category_spending.iloc[0]:.2f} in transactions."
                
            elif any(keyword in query_lower for keyword in ['time', 'trend', 'over time', 'pattern']):
                # Time series visualization
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                daily_totals = df.groupby('date')['transaction_amount'].sum()
                
                plt.subplot(2, 1, 1)
                daily_totals.plot(kind='line', marker='o', color='#4CAF50')
                plt.title('Transaction Amounts Over Time')
                plt.ylabel('Total Amount')
                
                plt.subplot(2, 1, 2)
                transaction_counts = df.groupby('date').size()
                transaction_counts.plot(kind='bar', color='#2196F3')
                plt.title('Transaction Frequency Over Time')
                plt.ylabel('Number of Transactions')
                
                highest_day = daily_totals.idxmax()
                summary = f"Your highest spending day was {highest_day} with ${daily_totals.max():.2f} in transactions."
                
            elif any(keyword in query_lower for keyword in ['payment', 'method']):
                # Payment method analysis
                method_counts = df['method_of_transaction'].value_counts()
                method_amounts = df.groupby('method_of_transaction')['transaction_amount'].sum()
                
                plt.subplot(1, 2, 1)
                method_counts.plot(kind='bar', color='#673AB7')
                plt.title('Transactions by Payment Method')
                plt.ylabel('Number of Transactions')
                plt.xticks(rotation=45)
                
                plt.subplot(1, 2, 2)
                method_amounts.plot(kind='pie', autopct='%1.1f%%')
                plt.title('Transaction Amount by Payment Method')
                
                most_used = method_counts.index[0] if not method_counts.empty else "N/A"
                summary = f"Your most frequently used payment method is {most_used}, used for {method_counts.iloc[0]} transactions."
                
            else:
                # General overview
                plt.subplot(2, 2, 1)
                df['transaction_amount'].plot(kind='hist', bins=20, color='#2196F3')
                plt.title('Transaction Amount Distribution')
                
                plt.subplot(2, 2, 2)
                category_counts = df['merchant_category'].value_counts().head(5)
                category_counts.plot(kind='bar', color='#4CAF50')
                plt.title('Top 5 Transaction Categories')
                plt.xticks(rotation=45)
                
                plt.subplot(2, 2, 3)
                method_counts = df['method_of_transaction'].value_counts()
                method_counts.plot(kind='pie', autopct='%1.1f%%')
                plt.title('Transactions by Payment Method')
                
                plt.subplot(2, 2, 4)
                df['label_for_fraud'].value_counts().plot(kind='bar', color=['#4CAF50', '#F44336'])
                plt.title('Normal vs Flagged Transactions')
                plt.xticks([0, 1], ['Normal', 'Flagged'])
                
                avg_amount = df['transaction_amount'].mean()
                summary = f"You have {len(df)} transactions with an average amount of ${avg_amount:.2f}."
            
            plt.tight_layout()
            
            # Save figure to BytesIO object
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return img_str, summary
            
        except Exception as e:
            print(f"Error in fallback visualization: {e}")
            # Return empty visualization
            return None, "I was unable to create a visualization from your transaction data."
    
    def _fix_output_format(self, code_text):
        """
        Fix potential formatting issues in the generated code, particularly with the output dictionary.
        
        Args:
            code_text (str): The generated Python code
            
        Returns:
            str: Fixed Python code
        """
        # 1. Look for output dictionary definition lines
        output_pattern = re.compile(r'output\s*=\s*{.*?}', re.DOTALL)
        match = output_pattern.search(code_text)
        
        if match:
            output_dict_text = match.group(0)
            
            # 2. Fix typical formatting errors
            # Check for f-string formatting issues
            if 'f"' in output_dict_text or "f'" in output_dict_text:
                # Replace f-strings with regular strings
                fixed_output_dict = re.sub(r'f(["\'])(.*?)\1', r'\1\2\1', output_dict_text)
                code_text = code_text.replace(output_dict_text, fixed_output_dict)
                
            # Fix string formatting with % operator
            if '"%' in output_dict_text or "'%" in output_dict_text:
                fixed_output_dict = re.sub(r'(["\'])(.*?)%\((.*?)\)([sdf])\1', r'\1\2\1 % (\3)', output_dict_text)
                code_text = code_text.replace(output_dict_text, fixed_output_dict)
                
            # Ensure proper dictionary format - replace any multiline with single line dict
            if '\n' in output_dict_text and ('"summary"' in output_dict_text or '"visualization"' in output_dict_text):
                # Extract key values
                summary_pattern = re.compile(r'"summary"\s*:\s*([^,}]+)')
                summary_match = summary_pattern.search(output_dict_text)
                
                viz_pattern = re.compile(r'"visualization"\s*:\s*([^,}]+)')
                viz_match = viz_pattern.search(output_dict_text)
                
                df_html_pattern = re.compile(r'"dataframe_html"\s*:\s*([^,}]+)')
                df_html_match = df_html_pattern.search(output_dict_text)
                
                # Build clean dictionary
                new_output_dict = 'output = {'
                
                if summary_match:
                    summary_value = summary_match.group(1).strip()
                    new_output_dict += f'"summary": {summary_value}'
                else:
                    new_output_dict += '"summary": "Analysis of your transaction data is complete."'
                
                if viz_match:
                    viz_value = viz_match.group(1).strip()
                    new_output_dict += f', "visualization": {viz_value}'
                
                if df_html_match:
                    df_html_value = df_html_match.group(1).strip()
                    new_output_dict += f', "dataframe_html": {df_html_value}'
                
                new_output_dict += '}'
                code_text = code_text.replace(output_dict_text, new_output_dict)
        
        # 3. Add default output code if no output dictionary is found
        if 'output =' not in code_text and 'plt.savefig' in code_text:
            # Typical case: visualization created but output dict missing
            buffer_code = """
# Ensure visualization is properly saved
if 'buffer' not in locals():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
img_str = base64.b64encode(buffer.read()).decode()
plt.close()

# Create proper output dictionary
output = {
    "summary": "Analysis of your transaction data is complete.",
    "visualization": img_str
}
"""
            code_text += buffer_code
        
        # 4. Check if there's a filtered dataframe that should be included in the output
        if 'output =' not in code_text and ('filtered_df' in code_text or 'display_df' in code_text):
            df_output_code = """
# Create a dataframe HTML output if a filtered dataframe exists
if 'filtered_df' in locals():
    display_df = filtered_df.head(20)
    df_html = display_df.to_html(classes='table table-striped table-hover', border=0, index=False)
elif 'display_df' in locals():
    df_html = display_df.to_html(classes='table table-striped table-hover', border=0, index=False)
else:
    df_html = None

# Create proper output dictionary
output = {
    "summary": "Here are the transaction details you requested.",
    "visualization": None if 'img_str' not in locals() else img_str,
    "dataframe_html": df_html
}
"""
            code_text += df_output_code
            
        # 5. If there's still no output dictionary and no visualization
        if 'output =' not in code_text:
            # Add default output at the end
            code_text += """
# Ensure there's always an output
output = {
    "summary": "Analysis of your transaction data is complete.",
    "visualization": None
}
"""
            
        return code_text
    
    def _generate_direct_response(self, query):
        """
        Generate a direct response to a query without transaction data
        
        Args:
            query (str): The user's query
            
        Returns:
            str: The assistant's response
        """
        try:
            # Create a simple prompt for direct queries
            prompt = f"""You are a banking fraud detection assistant powered by Gemini AI. 
You specialize in helping users understand fraud prevention, security measures, 
and how to identify suspicious transactions.

USER QUERY: {query}

Provide a helpful, accurate, and concise response focused on banking fraud and security.
"""
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
                response_mime_type="text/plain",
            )
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # Extract text from response
            return response.text
            
        except Exception as e:
            print(f"Error generating direct response: {e}")
            return f"I'm sorry, I couldn't process your query. Please try again or ask a different question. Error: {str(e)}"
    
    def _generate_fallback_response(self, query, transactions_data, customer_id):
        """Generate a simple fallback response without using the API."""
        try:
            # If no transaction data, provide generic fraud info
            if not transactions_data:
                fallback_responses = [
                    "To identify fraud, look for unexpected transactions, calls from unknown numbers claiming to be your bank, or requests for personal information.",
                    "Common signs of fraud include unexpected withdrawals, purchases you didn't make, and notifications about password changes you didn't request.",
                    "If you suspect fraud, contact your bank immediately through their official phone number, freeze your accounts, and change your passwords.",
                    "To protect your account, use strong unique passwords, enable two-factor authentication, and never share your banking details with anyone who contacts you first."
                ]
                return random.choice(fallback_responses)
            
            query_lower = query.lower()
            total_count = len(transactions_data)
            fraud_count = sum(1 for t in transactions_data if t.get('label_for_fraud') == 1)
            fraud_percentage = (fraud_count / total_count * 100) if total_count > 0 else 0
            
            # Calculate total amount and average transaction amount
            total_amount = sum(float(t.get('transaction_amount', 0)) for t in transactions_data)
            avg_amount = total_amount / total_count if total_count > 0 else 0
            
            # Get transaction methods distribution
            methods = {}
            for t in transactions_data:
                method = t.get('method_of_transaction', 'Unknown')
                methods[method] = methods.get(method, 0) + 1
            
            # Find most common method
            most_common_method = max(methods.items(), key=lambda x: x[1])[0] if methods else "Unknown"
            
            # Generic responses
            generic_responses = [
                f"Based on your transaction data, you have {total_count} transactions, with {fraud_count} flagged as potential fraud.",
                f"Your account shows {fraud_count} suspicious transactions out of {total_count} total transactions.",
                f"You have a total of {total_count} transactions, with approximately {fraud_percentage:.1f}% flagged as potential fraud.",
                f"The total amount across all your transactions is {total_amount:.2f}.",
                f"Your most frequently used transaction method is {most_common_method}."
            ]
            
            # Query-specific responses
            if "fraud" in query_lower or "suspicious" in query_lower:
                return f"I found {fraud_count} transactions flagged as potential fraud, representing {fraud_percentage:.1f}% of your total transactions."
            
            elif "total" in query_lower and "amount" in query_lower:
                return f"The total amount across all your transactions is {total_amount:.2f}."
            
            elif "average" in query_lower:
                return f"The average transaction amount is {avg_amount:.2f}."
            
            elif "method" in query_lower or "payment" in query_lower:
                methods_str = ", ".join(f"{method}: {count}" for method, count in methods.items())
                return f"Your transaction methods breakdown: {methods_str}. The most common method is {most_common_method}."
            
            elif "help" in query_lower or "can you" in query_lower:
                return "I can help you analyze your transaction data, including fraud detection, transaction methods, amounts, and patterns. What would you like to know?"
            
            else:
                # Return a generic response if no specific patterns matched
                return random.choice(generic_responses)
                
        except Exception as e:
            print(f"Error in fallback response: {e}")
            return "I'm sorry, I'm having trouble analyzing your transaction data right now. Please try a simpler query or try again later."
    
    def _create_transactions_summary(self, transactions):
        """
        Create a summary of transactions to include in the prompt.
        
        Args:
            transactions (list): List of transaction dictionaries
            
        Returns:
            str: A text summary of the transactions
        """
        try:
            # Check if transactions is empty
            if not transactions:
                return "No transaction data available for this customer."
                
            # Count total transactions
            total_count = len(transactions)
            
            # Count fraud transactions
            fraud_count = sum(1 for t in transactions if t.get('label_for_fraud') == 1)
            
            # Calculate total transaction amount
            total_amount = sum(float(t.get('transaction_amount', 0)) for t in transactions)
            
            # Get transaction methods distribution
            methods = {}
            for t in transactions:
                method = t.get('method_of_transaction', 'Unknown')
                methods[method] = methods.get(method, 0) + 1
            
            # Get locations distribution
            locations = {}
            for t in transactions:
                location = t.get('location_data', 'Unknown')
                locations[location] = locations.get(location, 0) + 1
            
            # Format summary
            summary = f"""Total Transactions: {total_count}
Fraud Transactions: {fraud_count}
Total Transaction Amount: {total_amount:.2f}

Transaction Methods:
{self._format_dict(methods)}

Transaction Locations:
{self._format_dict(locations)}

Sample Transactions (up to 5):
{json.dumps(transactions[:5], indent=2)}
"""
            return summary
        except Exception as e:
            print(f"Error creating transaction summary: {e}")
            return f"Error summarizing transactions: {str(e)}"
    
    def _format_dict(self, d):
        """Format a dictionary as a string with each key-value pair on a new line."""
        return '\n'.join(f"- {k}: {v}" for k, v in d.items()) 