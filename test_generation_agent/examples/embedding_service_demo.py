#!/usr/bin/env python
"""
Demonstration script for the Embedding Service.

This script shows how to use the enhanced embedding service with various features:
- Basic text embedding
- Batch embedding with caching
- User story and test case embedding
- Performance measurement
- Cache statistics
- Switching between OpenAI and Sentence Transformers models

Usage:
    python embedding_service_demo.py [--model MODEL_NAME] [--cache-size SIZE]
"""
import argparse
import time
import json
from typing import List, Any, Dict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding import get_embedding_service, EmbeddingService
from app.config import EMBEDDING_MODEL, EMBEDDING_DIMENSIONS


def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper


class EmbeddingDemo:
    """Class to demonstrate the embedding service functionality."""
    
    def __init__(self, model_name: str = None, cache_size: int = 1000):
        """Initialize the demo with the specified model and cache size."""
        self.embedding_service = get_embedding_service(model_name, cache_size)
        self.model_name = self.embedding_service.model_name
        logger.info(f"Initialized embedding service with model: {self.model_name}")
        
        # Sample texts for demonstration
        self.sample_texts = [
            "Automated testing helps ensure software quality",
            "LangGraph is a framework for building stateful LLM agents",
            "Vector databases store embeddings for semantic search",
            "User stories describe features from the user's perspective",
            "Test cases verify that the software meets requirements",
            "Embedding models convert text into numerical vectors",
            "Azure DevOps provides CI/CD pipelines and issue tracking",
            "Quality assurance is a critical part of the software development lifecycle"
        ]
        
        # Sample user stories
        self.user_stories = [
            {
                "title": "View Test Results Dashboard",
                "description": "As a QA engineer, I want to view a dashboard of test results so I can quickly assess the quality of the latest build."
            },
            {
                "title": "Export Test Cases",
                "description": "As a test manager, I want to export test cases to CSV so I can share them with stakeholders who don't have access to the test management system."
            },
            {
                "title": "Link Test Cases to Requirements",
                "description": "As a QA engineer, I want to link test cases to requirements so I can ensure test coverage and traceability."
            }
        ]
        
        # Sample test cases
        self.test_cases = [
            {
                "title": "Verify Dashboard Displays All Test Suites",
                "description": "Test that the dashboard shows all test suites with their pass/fail status",
                "steps": "1. Log in as QA user\n2. Navigate to Test Results Dashboard\n3. Check that all test suites are displayed",
                "expected_result": "All test suites should be displayed with correct pass/fail indicators"
            },
            {
                "title": "Verify CSV Export Format",
                "description": "Test that exported CSV files have the correct format",
                "steps": "1. Navigate to Test Cases page\n2. Select multiple test cases\n3. Click Export to CSV\n4. Open the downloaded file",
                "expected_result": "CSV file should contain all selected test cases with correct columns"
            }
        ]
    
    @measure_time
    def demonstrate_single_embedding(self) -> None:
        """Demonstrate embedding a single text."""
        logger.info("--- Single Text Embedding ---")
        text = self.sample_texts[0]
        logger.info(f"Embedding text: {text}")
        
        embedding = self.embedding_service.embed_text(text)
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"Embedding sample (first 5 values): {embedding[:5]}")
        
        # Demonstrate caching by embedding the same text again
        logger.info("Embedding the same text again (should use cache)...")
        embedding_cached = self.embedding_service.embed_text(text)
        assert embedding == embedding_cached, "Cached embedding should be identical"
        
        # Get cache stats
        cache_stats = self.embedding_service.get_cache_stats()
        logger.info(f"Cache stats: {json.dumps(cache_stats, indent=2)}")
    
    @measure_time
    def demonstrate_batch_embedding(self) -> None:
        """Demonstrate embedding multiple texts in a batch."""
        logger.info("--- Batch Text Embedding ---")
        logger.info(f"Embedding {len(self.sample_texts)} texts in a batch")
        
        embeddings = self.embedding_service.embed_texts(self.sample_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        logger.info(f"First embedding dimension: {len(embeddings[0])}")
        
        # Embedding again to demonstrate caching for batch processing
        logger.info("Embedding the same batch again (should use cache)...")
        embeddings_cached = self.embedding_service.embed_texts(self.sample_texts)
        
        # Get cache stats
        cache_stats = self.embedding_service.get_cache_stats()
        logger.info(f"Cache stats after batch: {json.dumps(cache_stats, indent=2)}")
    
    @measure_time
    def demonstrate_user_story_embedding(self) -> None:
        """Demonstrate embedding user stories."""
        logger.info("--- User Story Embedding ---")
        
        for idx, story in enumerate(self.user_stories):
            logger.info(f"User Story {idx+1}: {story['title']}")
            embedding = self.embedding_service.embed_user_story(
                story['title'], 
                story['description']
            )
            logger.info(f"Embedding dimension: {len(embedding)}")
    
    @measure_time
    def demonstrate_test_case_embedding(self) -> None:
        """Demonstrate embedding test cases."""
        logger.info("--- Test Case Embedding ---")
        
        for idx, test_case in enumerate(self.test_cases):
            logger.info(f"Test Case {idx+1}: {test_case['title']}")
            embedding = self.embedding_service.embed_test_case(
                test_case['title'],
                test_case['description'],
                test_case['steps'],
                test_case['expected_result']
            )
            logger.info(f"Embedding dimension: {len(embedding)}")
    
    def run_full_demo(self) -> None:
        """Run a complete demonstration of the embedding service."""
        logger.info(f"=== Embedding Service Demo: Model {self.model_name} ===")
        
        self.demonstrate_single_embedding()
        self.demonstrate_batch_embedding()
        self.demonstrate_user_story_embedding()
        self.demonstrate_test_case_embedding()
        
        # Final cache stats
        cache_stats = self.embedding_service.get_cache_stats()
        logger.info(f"Final cache stats: {json.dumps(cache_stats, indent=2)}")
        
        logger.info("=== Demo Complete ===")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Embedding Service Demo")
    parser.add_argument(
        "--model", 
        type=str, 
        default=EMBEDDING_MODEL,
        help=f"Embedding model name (default: {EMBEDDING_MODEL})"
    )
    parser.add_argument(
        "--cache-size", 
        type=int, 
        default=1000,
        help="Size of the embedding cache (default: 1000)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    try:
        demo = EmbeddingDemo(model_name=args.model, cache_size=args.cache_size)
        demo.run_full_demo()
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
