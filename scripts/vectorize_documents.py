#!/usr/bin/env python3
"""
Direct Vectorization Pipeline for Markdown Documents
Processes .md files directly to vectors without XML aggregation
Uses Cloudflare Workers AI as primary, falls back to local embedding server
"""

import os
import sys
import json
import asyncio
import argparse
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import pickle

import aiohttp
import requests
import numpy as np
from minio import Minio
from minio.error import S3Error
import pyarrow as pa
import pyarrow.parquet as pq

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VectorChunk:
    """Represents a vectorized chunk of text"""
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    chunk_id: str
    source_file: str
    department: str

class CloudflareEmbeddings:
    """Cloudflare Workers AI Embeddings wrapper"""
    
    def __init__(self, account_id: str, api_token: str, model: str = "@cf/baai/bge-base-en-v1.5"):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"
        self.request_count = 0
        self.rate_limit_remaining = 1000  # Default limit
        
    async def embed_documents_async(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents asynchronously"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for text in texts:
                tasks.append(self._embed_single(session, text))
            
            embeddings = await asyncio.gather(*tasks)
            return embeddings
    
    async def _embed_single(self, session: aiohttp.ClientSession, text: str) -> List[float]:
        """Embed a single text"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text[:8192]  # CF Workers AI text limit
        }
        
        try:
            async with session.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=data
            ) as response:
                self.request_count += 1
                
                # Check rate limits
                if 'x-ratelimit-remaining' in response.headers:
                    self.rate_limit_remaining = int(response.headers['x-ratelimit-remaining'])
                
                if response.status == 200:
                    result = await response.json()
                    return result['result']['data'][0]
                elif response.status == 429:
                    logger.warning("Cloudflare rate limit reached")
                    raise Exception("Rate limit exceeded")
                else:
                    logger.error(f"CF API error: {response.status}")
                    raise Exception(f"API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error embedding with Cloudflare: {e}")
            raise
    
    def check_limits(self) -> bool:
        """Check if we're approaching rate limits"""
        return self.rate_limit_remaining > 10

class LocalEmbeddings:
    """Local embedding server fallback"""
    
    def __init__(self, endpoint_url: str, model: str = "ukr-paraphrase-multilingual-mpnet-base"):
        self.endpoint_url = endpoint_url
        self.model = model
        
    async def embed_documents_async(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using local server"""
        async with aiohttp.ClientSession() as session:
            embeddings = []
            for text in texts:
                embedding = await self._embed_single(session, text)
                embeddings.append(embedding)
            return embeddings
    
    async def _embed_single(self, session: aiohttp.ClientSession, text: str) -> List[float]:
        """Embed single text via local server"""
        try:
            async with session.post(
                f"{self.endpoint_url}/embed",
                json={"text": text, "model": self.model}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['embedding']
                else:
                    raise Exception(f"Local server error: {response.status}")
        except Exception as e:
            logger.error(f"Error with local embedding: {e}")
            # Fallback to sentence-transformers if local server fails
            return self._embed_with_sentence_transformers(text)
    
    def _embed_with_sentence_transformers(self, text: str) -> List[float]:
        """Ultimate fallback using sentence-transformers locally"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Sentence transformers fallback failed: {e}")
            raise

class VectorizationPipeline:
    """Main vectorization pipeline"""
    
    def __init__(self, args):
        self.args = args
        self.minio_client = self._init_minio()
        self.cf_embeddings = CloudflareEmbeddings(
            args.cf_account_id,
            args.cf_api_token,
            args.embedding_model_cf
        )
        self.local_embeddings = LocalEmbeddings(
            args.local_embedding_url,
            args.embedding_model_local
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.use_cloudflare = True  # Start with CF as primary
        
    def _init_minio(self) -> Minio:
        """Initialize MinIO client"""
        endpoint = self.args.minio_endpoint.replace('https://', '').replace('http://', '')
        return Minio(
            endpoint,
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
            secure='https' in self.args.minio_endpoint
        )
    
    def determine_department(self, file_path: str) -> str:
        """Determine department/section from file path"""
        path_parts = Path(file_path).parts
        
        # Map directories to departments
        dept_mapping = {
            'docs': 'documentation',
            'development-workflow': 'development',
            'investigation': 'research',
            'architecture': 'architecture',
            'protocols': 'protocols',
            'auth': 'auth-story',
            'logistics': 'logistics-dept',
            'production': 'production-dept'
        }
        
        for part in path_parts:
            if part in dept_mapping:
                return dept_mapping[part]
        
        # Default department based on file name patterns
        file_name = Path(file_path).stem.lower()
        if 'auth' in file_name or 'security' in file_name:
            return 'auth-story'
        elif 'deploy' in file_name or 'infrastructure' in file_name:
            return 'logistics-dept'
        elif 'architecture' in file_name or 'design' in file_name:
            return 'architecture'
        
        return 'general'
    
    async def process_file(self, file_path: str) -> List[VectorChunk]:
        """Process a single markdown file into vector chunks"""
        logger.info(f"Processing file: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create document
        doc = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "department": self.determine_department(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "file_hash": hashlib.md5(content.encode()).hexdigest()
            }
        )
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Prepare texts for embedding
        texts = [chunk.page_content for chunk in chunks]
        
        # Generate embeddings with fallback logic
        embeddings = await self.generate_embeddings(texts)
        
        # Create VectorChunk objects
        vector_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{Path(file_path).stem}_{i:04d}"
            vector_chunk = VectorChunk(
                text=chunk.page_content,
                embedding=embedding,
                metadata=chunk.metadata,
                chunk_id=chunk_id,
                source_file=file_path,
                department=doc.metadata["department"]
            )
            vector_chunks.append(vector_chunk)
        
        return vector_chunks
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with automatic fallback"""
        if self.use_cloudflare and self.cf_embeddings.check_limits():
            try:
                logger.info(f"Using Cloudflare Workers AI for {len(texts)} texts")
                return await self.cf_embeddings.embed_documents_async(texts)
            except Exception as e:
                logger.warning(f"Cloudflare failed, falling back to local: {e}")
                self.use_cloudflare = False
        
        # Use local embeddings as fallback
        logger.info(f"Using local embedding server for {len(texts)} texts")
        return await self.local_embeddings.embed_documents_async(texts)
    
    def save_to_minio(self, vector_chunks: List[VectorChunk], department: str):
        """Save vector chunks to MinIO as Parquet files"""
        bucket_name = f"vectors-{department}"
        
        # Ensure bucket exists
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            return
        
        # Prepare data for Parquet
        data = {
            'chunk_id': [],
            'text': [],
            'embedding': [],
            'source_file': [],
            'department': [],
            'metadata': []
        }
        
        for chunk in vector_chunks:
            data['chunk_id'].append(chunk.chunk_id)
            data['text'].append(chunk.text)
            data['embedding'].append(chunk.embedding)
            data['source_file'].append(chunk.source_file)
            data['department'].append(chunk.department)
            data['metadata'].append(json.dumps(chunk.metadata))
        
        # Create Parquet table
        table = pa.Table.from_pydict(data)
        
        # Save to buffer
        import io
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)
        
        # Upload to MinIO
        file_name = f"{department}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        self.minio_client.put_object(
            bucket_name,
            file_name,
            buffer,
            length=buffer.getbuffer().nbytes,
            content_type="application/octet-stream"
        )
        
        logger.info(f"Uploaded {len(vector_chunks)} vectors to {bucket_name}/{file_name}")
        
        # Also save as JSON for easier access
        json_data = []
        for chunk in vector_chunks:
            json_data.append({
                'chunk_id': chunk.chunk_id,
                'text': chunk.text,
                'embedding': chunk.embedding,
                'source_file': chunk.source_file,
                'department': chunk.department,
                'metadata': chunk.metadata
            })
        
        json_buffer = io.BytesIO(json.dumps(json_data, indent=2).encode())
        json_file_name = file_name.replace('.parquet', '.json')
        
        self.minio_client.put_object(
            bucket_name,
            json_file_name,
            json_buffer,
            length=json_buffer.getbuffer().nbytes,
            content_type="application/json"
        )
        
        logger.info(f"Also saved as JSON: {bucket_name}/{json_file_name}")
    
    async def run(self):
        """Run the vectorization pipeline"""
        # Read list of files to process
        with open(self.args.input_file, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
        
        if not files:
            logger.info("No files to process")
            return
        
        logger.info(f"Processing {len(files)} files")
        
        # Group files by department
        department_files = {}
        for file_path in files:
            if os.path.exists(file_path):
                dept = self.determine_department(file_path)
                if dept not in department_files:
                    department_files[dept] = []
                department_files[dept].append(file_path)
        
        # Process each department's files
        for department, dept_files in department_files.items():
            logger.info(f"Processing department: {department} ({len(dept_files)} files)")
            
            all_chunks = []
            for file_path in dept_files:
                try:
                    chunks = await self.process_file(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue
            
            if all_chunks:
                self.save_to_minio(all_chunks, department)
        
        # Generate summary
        logger.info("✅ Vectorization complete!")
        logger.info(f"Cloudflare requests: {self.cf_embeddings.request_count}")
        logger.info(f"Rate limit remaining: {self.cf_embeddings.rate_limit_remaining}")

def main():
    parser = argparse.ArgumentParser(description="Direct Vectorization Pipeline")
    parser.add_argument('--input-file', required=True, help='File containing list of files to process')
    parser.add_argument('--minio-endpoint', required=True, help='MinIO endpoint URL')
    parser.add_argument('--cf-account-id', required=True, help='Cloudflare account ID')
    parser.add_argument('--cf-api-token', required=True, help='Cloudflare API token')
    parser.add_argument('--local-embedding-url', required=True, help='Local embedding server URL')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size for text splitting')
    parser.add_argument('--chunk-overlap', type=int, default=200, help='Chunk overlap for text splitting')
    parser.add_argument('--embedding-model-cf', default='@cf/baai/bge-base-en-v1.5', help='Cloudflare embedding model')
    parser.add_argument('--embedding-model-local', default='ukr-paraphrase-multilingual-mpnet-base', help='Local embedding model')
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = VectorizationPipeline(args)
    asyncio.run(pipeline.run())

if __name__ == "__main__":
    main()
