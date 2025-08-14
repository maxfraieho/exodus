# Direct Vectorization Pipeline for RAG-Enhanced Development

## 🚀 Overview

This is a complete implementation of a direct vectorization pipeline that processes Markdown files into vector embeddings for RAG (Retrieval-Augmented Generation) enhanced AI pair programming. The system bypasses XML aggregation and directly vectorizes knowledge from Obsidian-managed `.md` files.

## 🏗️ Architecture

```
Obsidian Vault → GitHub → Vectorization Pipeline → MinIO Storage → RAG Queries
                    ↓                ↓                    ↓
              Git Plugin    Cloudflare Workers AI    Vector Buckets
                            (Primary Embedding)     (Dept-Isolated)
                                    ↓
                            Local Embedding Server
                              (Fallback)
```

## 🔧 Components

### 1. **GitHub Actions Workflow** (`vectorize-to-minio.yml`)
- Triggers on pushes to `.md` files
- Detects changed files for incremental processing
- Manages the entire vectorization pipeline
- Handles fallback logic between CF Workers AI and local embedding

### 2. **Python Vectorization Script** (`scripts/vectorize_documents.py`)
- Chunks markdown documents using LangChain
- Generates embeddings via Cloudflare Workers AI (primary)
- Falls back to local embedding server when rate limited
- Saves vectors as Parquet and JSON to MinIO

### 3. **MCP Vector Server** (`mcp-vector-server.js`)
- Provides MCP (Model Context Protocol) interface
- Supports semantic search across vectors
- Implements RAG query functionality
- Exposes HTTP API for web access

### 4. **RAG Query Interface** (`scripts/rag_query.py`)
- Demonstrates RAG-enhanced prompting
- Provides interactive query interface
- Formats prompts with retrieved context
- Supports multiple task types (code generation, debugging, etc.)

## 📦 Installation

### Prerequisites

1. **MinIO Server**
   ```bash
   docker run -p 9000:9000 -p 9001:9001 \
     -e MINIO_ROOT_USER=admin \
     -e MINIO_ROOT_PASSWORD=password \
     minio/minio server /data --console-address ":9001"
   ```

2. **Local Embedding Server** (Optional fallback)
   ```bash
   # Using Ollama
   ollama serve
   ollama pull nomic-embed-text
   
   # OR using sentence-transformers API
   pip install sentence-transformers fastapi uvicorn
   python -m uvicorn embedding_server:app --port 8000
   ```

3. **Cloudflare Workers AI**
   - Get account ID from Cloudflare dashboard
   - Generate API token with Workers AI permissions

### GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```yaml
MINIO_ENDPOINT_URL: https://your-minio-server.com
MINIO_ACCESS_KEY: your-access-key
MINIO_SECRET_KEY: your-secret-key
CF_ACCOUNT_ID: your-cloudflare-account-id
CF_API_TOKEN: your-cloudflare-api-token
LOCAL_EMBEDDING_URL: http://your-local-embedding-server:8000
```

## 🚀 Usage

### 1. Automatic Vectorization

Files are automatically vectorized when:
- You push `.md` files to the main branch
- Files in `docs/`, `development-workflow/`, or `investigation/` change
- You manually trigger the workflow with force reprocess

### 2. Manual Vectorization

```bash
# Process specific files
echo "docs/README.md" > files.txt
echo "docs/ARCHITECTURE.md" >> files.txt

python scripts/vectorize_documents.py \
  --input-file files.txt \
  --minio-endpoint https://minio.example.com \
  --cf-account-id YOUR_CF_ACCOUNT \
  --cf-api-token YOUR_CF_TOKEN \
  --local-embedding-url http://localhost:8000
```

### 3. RAG Queries

#### Interactive Mode
```bash
python scripts/rag_query.py interactive
```

#### Specific Examples
```bash
# Authentication story generation
python scripts/rag_query.py auth

# Logistics architecture review
python scripts/rag_query.py logistics

# Production debugging
python scripts/rag_query.py debug
```

### 4. MCP Server Usage

#### Start MCP Server
```bash
# For MCP protocol
node mcp-vector-server.js

# For HTTP API
node mcp-vector-server.js --http
```

#### API Endpoints
```bash
# Health check
curl http://localhost:8091/health

# List vector buckets
curl http://localhost:8091/api/v1/vector-buckets

# Semantic search
curl -X POST http://localhost:8091/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication JWT", "department": "auth-story", "top_k": 5}'

# RAG query
curl -X POST http://localhost:8091/api/v1/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "implement user login", "departments": ["auth-story"], "max_tokens": 2000}'
```

## 📁 MinIO Bucket Structure

```
vectors-auth-story/
├── auth-story_20240115_143022.parquet
├── auth-story_20240115_143022.json
└── ...

vectors-logistics-dept/
├── logistics-dept_20240115_143125.parquet
├── logistics-dept_20240115_143125.json
└── ...

vectors-production-dept/
├── production-dept_20240115_143230.parquet
├── production-dept_20240115_143230.json
└── ...
```

## 🔄 Department Mapping

The system automatically maps directories to departments:

- `docs/` → `documentation`
- `development-workflow/` → `development`
- `investigation/` → `research`
- `architecture/` → `architecture`
- Files with "auth" → `auth-story`
- Files with "deploy/infrastructure" → `logistics-dept`
- Files with "production" → `production-dept`

## 🛡️ Security Features

1. **Departmental Isolation**: Each department has its own MinIO bucket
2. **IAM Policies**: Buckets can have department-specific access controls
3. **Secure Credentials**: All sensitive data stored in GitHub secrets
4. **HTTPS Support**: MinIO and API endpoints support SSL/TLS

## 🎯 Benefits

1. **No XML Aggregation**: Direct vectorization is more efficient
2. **Incremental Updates**: Only changed files are reprocessed
3. **Dual Embedding Strategy**: CF Workers AI with local fallback
4. **RAG-Enhanced Development**: Context-aware AI assistance
5. **Department Isolation**: Secure, organized knowledge management
6. **Ukrainian Language Support**: Multilingual embedding models

## 📊 Performance

- **Chunk Size**: 1000 characters (configurable)
- **Chunk Overlap**: 200 characters (configurable)
- **Embedding Dimension**: 768 (BERT-based models)
- **Processing Speed**: ~100 documents/minute with CF Workers AI
- **Cache Duration**: 5 minutes for vector cache

## 🔧 Troubleshooting

### Common Issues

1. **Rate Limiting**: System automatically falls back to local embedding
2. **MinIO Connection**: Check endpoint URL and credentials
3. **Empty Vectors**: Ensure `.md` files have content
4. **Missing Departments**: Check department mapping logic

### Debug Commands

```bash
# Check MinIO buckets
aws s3 ls s3:// --endpoint-url https://your-minio.com

# Test embeddings
curl -X POST https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT/ai/run/@cf/baai/bge-base-en-v1.5 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"text": "test"}'

# View logs
docker logs mcp-vector-server
```

## 🚀 Advanced Features

### Custom Department Mapping

Edit `determine_department()` in `vectorize_documents.py`:

```python
dept_mapping = {
    'your-folder': 'your-department',
    # Add custom mappings
}
```

### Custom Embedding Models

```python
# Cloudflare model
EMBEDDING_MODEL_CF='@cf/baai/bge-large-en-v1.5'

# Local model
EMBEDDING_MODEL_LOCAL='your-custom-model'
```

### Webhook Integration

The pipeline can trigger webhooks on completion:

```yaml
- name: Notify completion
  run: |
    curl -X POST https://your-webhook.com/vectorization-complete \
      -d '{"status": "complete", "files": "'$(wc -l < changed_files.txt)'"}'
```

## 📝 License

This implementation is provided as-is for use in your Pravda project.

## 🤝 Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review GitHub Actions logs
- Inspect MinIO bucket contents
- Verify embedding service status
