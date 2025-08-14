#!/usr/bin/env python3
"""
RAG Query Example - Demonstrates how to use vectorized knowledge for AI pair programming
Connects to MinIO vectors and provides context-aware responses
"""

import os
import json
import requests
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import aiohttp

@dataclass
class RAGContext:
    """Represents retrieved context for augmentation"""
    query: str
    contexts: List[Dict[str, Any]]
    department: Optional[str] = None
    
class RAGQueryEngine:
    """RAG Query Engine for AI Pair Programming"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8091"):
        self.mcp_server_url = mcp_server_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def semantic_search(
        self, 
        query: str, 
        department: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Perform semantic search across vectorized documents"""
        
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        if department:
            payload["department"] = department
        
        async with self.session.post(
            f"{self.mcp_server_url}/api/v1/search",
            json=payload
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Search failed: {response.status}")
    
    async def retrieve_context(
        self,
        query: str,
        departments: Optional[List[str]] = None,
        max_tokens: int = 2000
    ) -> RAGContext:
        """Retrieve relevant context for query augmentation"""
        
        payload = {
            "query": query,
            "max_tokens": max_tokens
        }
        
        if departments:
            payload["departments"] = departments
        
        async with self.session.post(
            f"{self.mcp_server_url}/api/v1/rag",
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return RAGContext(
                    query=data["query"],
                    contexts=data["context"],
                    department=departments[0] if departments else None
                )
            else:
                raise Exception(f"RAG retrieval failed: {response.status}")
    
    def format_prompt_with_context(
        self,
        user_query: str,
        rag_context: RAGContext,
        task_type: str = "code_generation"
    ) -> str:
        """Format a prompt with retrieved RAG context"""
        
        # Build context section
        context_parts = []
        for ctx in rag_context.contexts:
            context_parts.append(f"""
Source: {ctx['source']}
Relevance: {ctx['relevance']:.2f}
Content:
{ctx['content']}
---""")
        
        context_section = "\n".join(context_parts)
        
        # Format based on task type
        if task_type == "code_generation":
            prompt = f"""You are an AI pair programmer with access to project-specific knowledge.

## Retrieved Context from Project Documentation:
{context_section}

## User Query:
{user_query}

## Instructions:
1. Use the provided context to understand project-specific patterns, conventions, and requirements
2. Generate code that follows the established patterns from the context
3. Ensure compatibility with the existing architecture described in the context
4. Include relevant imports and dependencies mentioned in the context
5. Add comments explaining how the solution relates to the project context

Please provide a complete, production-ready solution based on the context above."""

        elif task_type == "architecture_review":
            prompt = f"""You are an AI architecture consultant with knowledge of this specific project.

## Project Context:
{context_section}

## Review Request:
{user_query}

## Review Guidelines:
1. Evaluate against the project's established patterns and principles
2. Identify any deviations from documented architecture
3. Suggest improvements based on existing project conventions
4. Consider integration points mentioned in the context
5. Provide specific, actionable recommendations

Please provide a detailed architectural review based on the project context."""

        elif task_type == "debugging":
            prompt = f"""You are an AI debugging assistant familiar with this project's codebase.

## Relevant Project Information:
{context_section}

## Debugging Request:
{user_query}

## Debugging Approach:
1. Consider known patterns and common issues from the context
2. Check against documented configurations and settings
3. Verify compatibility with project dependencies
4. Look for similar solved issues in the context
5. Suggest diagnostic steps based on project structure

Please help debug this issue using the project-specific knowledge above."""

        else:  # general
            prompt = f"""## Project Context:
{context_section}

## Query:
{user_query}

Please provide a response that takes into account the specific project context above."""

        return prompt

# Example usage functions
async def example_auth_story_generation():
    """Example: Generate authentication code using RAG context"""
    
    async with RAGQueryEngine() as engine:
        # Retrieve context for authentication story
        context = await engine.retrieve_context(
            query="user authentication JWT tokens security implementation",
            departments=["auth-story", "security"],
            max_tokens=3000
        )
        
        # Create augmented prompt
        prompt = engine.format_prompt_with_context(
            user_query="Generate a secure JWT authentication middleware for our Express.js API with refresh token support",
            rag_context=context,
            task_type="code_generation"
        )
        
        print("=" * 80)
        print("GENERATED PROMPT WITH RAG CONTEXT:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        
        # This prompt can now be sent to Claude or another AI model
        # The AI will have full context about your project's auth patterns
        
        return prompt

async def example_logistics_architecture_review():
    """Example: Review logistics module architecture"""
    
    async with RAGQueryEngine() as engine:
        # Retrieve logistics and architecture context
        context = await engine.retrieve_context(
            query="logistics module microservices deployment Kubernetes scaling",
            departments=["logistics-dept", "architecture"],
            max_tokens=2500
        )
        
        prompt = engine.format_prompt_with_context(
            user_query="Review our proposed logistics microservice split: inventory-service, shipping-service, and tracking-service. Each will have its own database and communicate via RabbitMQ.",
            rag_context=context,
            task_type="architecture_review"
        )
        
        return prompt

async def example_production_debugging():
    """Example: Debug production issue with context"""
    
    async with RAGQueryEngine() as engine:
        # Retrieve production and infrastructure context
        context = await engine.retrieve_context(
            query="production deployment MinIO connection timeout error handling",
            departments=["production-dept", "infrastructure"],
            max_tokens=2000
        )
        
        prompt = engine.format_prompt_with_context(
            user_query="Getting intermittent MinIO connection timeouts in production. Error: 'S3Error: Connection timeout after 30000ms'. Happens during peak hours.",
            rag_context=context,
            task_type="debugging"
        )
        
        return prompt

async def interactive_rag_query():
    """Interactive RAG query interface"""
    
    print("🤖 RAG-Enhanced AI Pair Programming Interface")
    print("=" * 50)
    
    departments = [
        "auth-story",
        "logistics-dept", 
        "production-dept",
        "architecture",
        "development",
        "documentation"
    ]
    
    task_types = [
        "code_generation",
        "architecture_review",
        "debugging",
        "general"
    ]
    
    print("\nAvailable departments:")
    for i, dept in enumerate(departments, 1):
        print(f"  {i}. {dept}")
    
    dept_choice = input("\nSelect department (number or 'all'): ").strip()
    selected_dept = None if dept_choice == 'all' else departments[int(dept_choice) - 1]
    
    print("\nTask types:")
    for i, task in enumerate(task_types, 1):
        print(f"  {i}. {task}")
    
    task_choice = int(input("\nSelect task type (number): ").strip())
    task_type = task_types[task_choice - 1]
    
    user_query = input("\nEnter your query: ").strip()
    
    print("\n🔄 Retrieving relevant context...")
    
    async with RAGQueryEngine() as engine:
        try:
            context = await engine.retrieve_context(
                query=user_query,
                departments=[selected_dept] if selected_dept else None,
                max_tokens=2500
            )
            
            print(f"\n✅ Retrieved {len(context.contexts)} relevant context chunks")
            
            prompt = engine.format_prompt_with_context(
                user_query=user_query,
                rag_context=context,
                task_type=task_type
            )
            
            print("\n" + "=" * 80)
            print("AUGMENTED PROMPT:")
            print("=" * 80)
            print(prompt)
            print("=" * 80)
            
            # Save to file for easy copying
            with open("rag_prompt.txt", "w") as f:
                f.write(prompt)
            print("\n💾 Prompt saved to 'rag_prompt.txt'")
            
            # Show source files used
            print("\n📚 Sources used:")
            unique_sources = set()
            for ctx in context.contexts:
                unique_sources.add(ctx['source'])
            for source in unique_sources:
                print(f"  - {source}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main entry point"""
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "auth":
            asyncio.run(example_auth_story_generation())
        elif sys.argv[1] == "logistics":
            asyncio.run(example_logistics_architecture_review())
        elif sys.argv[1] == "debug":
            asyncio.run(example_production_debugging())
        elif sys.argv[1] == "interactive":
            asyncio.run(interactive_rag_query())
        else:
            print("Usage: python rag_query.py [auth|logistics|debug|interactive]")
    else:
        # Default to interactive mode
        asyncio.run(interactive_rag_query())

if __name__ == "__main__":
    main()
