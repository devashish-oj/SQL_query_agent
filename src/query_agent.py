"""Query generation agent using Google Gemini LLM."""

import logging
import re
from typing import Dict, Any, List, Optional
from groq import Groq

from .config import settings
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class QueryAgent:
    """Agent for generating SQL queries from natural language using Google Gemini."""
    
    def __init__(self, schema_manager: SchemaManager):
        """
        Initialize the query agent.
        
        Args:
            schema_manager: SchemaManager instance for accessing database schema
        """
        self.schema_manager = schema_manager
        
        # Configure Groq
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    async def generate_query(
        self,
        user_request: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language request.
        
        Args:
            user_request: User's natural language request
            conversation_history: Optional list of previous messages
            
        Returns:
            Dict containing:
                - query: Generated SQL query
                - explanation: Explanation of the query
                - query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
                - tables_used: List of tables referenced
                - warning: Any safety warnings
        """
        try:
            # Get schema information
            schema_text = self.schema_manager.format_schema_for_llm()
            
            # Build the prompt
            prompt = self._build_prompt(schema_text, user_request)
            
            # Call Groq
            logger.info(f"Generating query for request: {user_request}")
            
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Generate the SQL query for the request above."}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=2048,
            )
            
            # Parse the response
            response_text = completion.choices[0].message.content
            result = self._parse_response(response_text)
            
            # Add safety validation
            result["is_safe"] = self._validate_query_safety(result.get("query", ""))
            
            logger.info(f"Generated {result.get('query_type')} query")
            return result
            
        except Exception as e:
            logger.error(f"Error generating query: {e}")
            return {
                "error": str(e),
                "query": None,
                "explanation": f"Failed to generate query: {e}"
            }
    
    def _build_prompt(self, schema_text: str, user_request: str) -> str:
        """
        Build the prompt for Gemini.
        
        Args:
            schema_text: Formatted database schema
            user_request: User's natural language request
            
        Returns:
            Complete prompt string
        """
        return f"""You are an expert SQL query generator for PostgreSQL databases. Your task is to generate SQL queries based on user requests.

DATABASE SCHEMA:
{schema_text}

USER REQUEST:
{user_request}

INSTRUCTIONS:
1. Generate ONLY valid PostgreSQL SQL queries
2. Always include an explanation of what the query does
3. Identify the query type (SELECT, INSERT, UPDATE, DELETE)
4. List all tables used in the query
5. Add appropriate WHERE clauses for UPDATE and DELETE to prevent accidental mass operations
6. Use proper SQL formatting and indentation
7. Include comments in the SQL for clarity
8. For INSERT queries, specify all column names explicitly
9. For complex queries, explain the logic step by step

IMPORTANT SAFETY RULES:
- For DELETE or UPDATE queries, ALWAYS include a WHERE clause unless the user explicitly requests to affect all rows
- For potentially destructive operations, add a comment warning about the impact
- Never generate queries that could compromise database security
- Avoid queries with obvious vulnerabilities (SQL injection patterns, etc.)

OUTPUT FORMAT:
Provide your response in the following format:

QUERY TYPE: [SELECT|INSERT|UPDATE|DELETE]

EXPLANATION:
[Clear explanation of what the query does]

TABLES USED:
[Comma-separated list of table names]

SQL QUERY:
```sql
[Your SQL query here]
```

WARNINGS (if any):
[Any warnings about the query's impact]

Remember: This query will NOT be executed automatically. It will only be displayed to the user for review."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response into structured format.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed response dict
        """
        result = {
            "query": None,
            "explanation": "",
            "query_type": "UNKNOWN",
            "tables_used": [],
            "warnings": ""
        }
        
        # Extract query type
        query_type_match = re.search(r'QUERY TYPE:\s*(\w+)', response_text, re.IGNORECASE)
        if query_type_match:
            result["query_type"] = query_type_match.group(1).upper()
        
        # Extract explanation
        explanation_match = re.search(
            r'EXPLANATION:\s*\n(.*?)\n\n(?:TABLES USED:|SQL QUERY:)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if explanation_match:
            result["explanation"] = explanation_match.group(1).strip()
        
        # Extract tables used
        tables_match = re.search(
            r'TABLES USED:\s*\n(.*?)\n\n',
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if tables_match:
            tables_text = tables_match.group(1).strip()
            result["tables_used"] = [t.strip() for t in tables_text.split(',')]
        
        # Extract SQL query
        sql_match = re.search(
            r'```sql\s*\n(.*?)\n```',
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if sql_match:
            result["query"] = sql_match.group(1).strip()
        
        # Extract warnings
        warnings_match = re.search(
            r'WARNINGS.*?:\s*\n(.*?)(?:\n\n|$)',
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if warnings_match:
            result["warnings"] = warnings_match.group(1).strip()
        
        return result
    
    def _validate_query_safety(self, query: str) -> bool:
        """
        Perform basic safety validation on the generated query.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query appears safe, False otherwise
        """
        if not query:
            return False
        
        query_upper = query.upper()
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DROP\s+DATABASE',
            r'TRUNCATE',
            r'ALTER\s+TABLE',
            r'CREATE\s+TABLE',
            r'GRANT',
            r'REVOKE',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                return False
        
        # Check for DELETE/UPDATE without WHERE
        if re.search(r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', query_upper):
            logger.warning("DELETE without WHERE clause detected")
            return False
        
        if re.search(r'\bUPDATE\s+\w+\s+SET\s+.*?(?:;|$)', query_upper):
            if not re.search(r'\bWHERE\b', query_upper):
                logger.warning("UPDATE without WHERE clause detected")
                return False
        
        return True
    
    async def explain_query(self, sql_query: str) -> str:
        """
        Explain what a SQL query does.
        
        Args:
            sql_query: SQL query to explain
            
        Returns:
            Explanation of the query
        """
        try:
            prompt = f"""Please explain what this SQL query does in simple terms:

```sql
{sql_query}
```

Provide a clear, concise explanation that a non-technical user can understand."""

            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful SQL assistant. Explain SQL queries in simple terms."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
            )
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return f"Unable to explain query: {e}"
