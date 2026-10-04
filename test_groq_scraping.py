#!/usr/bin/env python3
"""
Test script to verify Groq AI web scraping for job descriptions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import fetch_job_description_from_url, latex_to_html
from dotenv import load_dotenv

def test_groq_web_scraping():
    """Test fetching job description using Groq AI"""
    
    load_dotenv()
    groq_api_key = os.getenv('GROQ_API_KEY', '')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment")
        print("   Set it via: $env:GROQ_API_KEY='your-key'")
        return False
    
    print("✓ Groq API key found")
    
    # Test URLs (replace with real job posting URLs)
    test_urls = [
        # Add your test job posting URLs here
        # Example format:
        # "https://indeed.com/jobs?q=python&l=hamburg",
    ]
    
    if not test_urls:
        print("\n⚠️  No test URLs configured")
        print("   Add job posting URLs to test_urls list in this script")
        return True
    
    for url in test_urls:
        print(f"\n📍 Testing URL: {url[:60]}...")
        try:
            description = fetch_job_description_from_url(url, groq_api_key)
            if description:
                print(f"✓ Successfully extracted {len(description)} characters")
                print(f"  Preview: {description[:200]}...")
            else:
                print("❌ Could not extract description")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return True


def test_latex_to_html():
    """Test LaTeX to HTML conversion"""
    
    load_dotenv()
    groq_api_key = os.getenv('GROQ_API_KEY', '')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found")
        return False
    
    # Sample LaTeX resume
    sample_latex = r"""
\documentclass{article}
\usepackage[margin=1in]{geometry}
\begin{document}

\section*{John Doe}
john@example.com | (555) 123-4567

\section{Experience}
\subsection*{Software Engineer}
\textbf{TechCorp Inc.} \hfill 2020-2023
\begin{itemize}
    \item Developed Python web applications
    \item Led team of 5 engineers
\end{itemize}

\section{Skills}
Python, JavaScript, SQL, Docker

\end{document}
"""
    
    print("\n🔧 Testing LaTeX to HTML conversion...")
    
    output_path = "/tmp/test_resume.html"
    
    try:
        success = latex_to_html(sample_latex, output_path, groq_api_key)
        
        if success and os.path.exists(output_path):
            print("✓ Successfully generated HTML resume")
            with open(output_path, 'r') as f:
                content = f.read()
            print(f"  Generated {len(content)} bytes of HTML")
            print(f"  File saved to: {output_path}")
        else:
            print("❌ Failed to generate HTML resume")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Groq AI Integration for Job Scraping")
    print("=" * 60)
    
    # Test 1: Web scraping
    print("\n[Test 1] Groq AI Web Scraping")
    print("-" * 60)
    test_groq_web_scraping()
    
    # Test 2: LaTeX to HTML
    print("\n[Test 2] LaTeX to HTML Conversion")
    print("-" * 60)
    test_latex_to_html()
    
    print("\n" + "=" * 60)
    print("✓ Tests completed!")
    print("=" * 60)
