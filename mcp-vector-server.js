#!/usr/bin/env node
/**
 * MCP Vector Server for MinIO
 * Provides access to vectorized documents stored in MinIO buckets
 * Supports semantic search and RAG queries
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { Minio } = require('minio');
const express = require('express');
const cors = require('cors');
const { createHash } = require('crypto');

// Configuration from environment
const config = {
  minioEndpoint: process.env.MINIO_ENDPOINT || 'localhost',
  minioPort: parseInt(process.env.MINIO_PORT || '9000'),
  minioAccessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
  minioSecretKey: process.env.MINIO_SECRET_KEY || 'minioadmin',
  minioUseSSL: process.env.MINIO_USE_SSL === 'true',
  vectorBucketPrefix: process.env.VECTOR_BUCKET_PREFIX || 'vectors-',
  enableRAG: process.env.ENABLE_RAG === 'true',
  httpPort: parseInt(process.env.HTTP_PORT || '8091')
};

// Initialize MinIO client
const minioClient = new Minio.Client({
  endPoint: config.minioEndpoint,
  port: config.minioPort,
  useSSL: config.minioUseSSL,
  accessKey: config.minioAccessKey,
  secretKey: config.minioSecretKey
});

// Vector similarity calculation
function cosineSimilarity(vec1, vec2) {
  if (!vec1 || !vec2 || vec1.length !== vec2.length) return 0;
  
  let dotProduct = 0;
  let norm1 = 0;
  let norm2 = 0;
  
  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i];
    norm1 += vec1[i] * vec1[i];
    norm2 += vec2[i] * vec2[i];
  }
  
  return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
}

class VectorMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'pravda-vector-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );
    
    this.setupHandlers();
    this.vectorCache = new Map();
    this.lastCacheUpdate = null;
  }
  
  setupHandlers() {
    // List available vector buckets
    this.server.setRequestHandler('resources/list', async () => {
      const buckets = await this.listVectorBuckets();
      return {
        resources: buckets.map(bucket => ({
          uri: `minio://vectors/${bucket}`,
          name: bucket,
          description: `Vector bucket: ${bucket}`,
          mimeType: 'application/json'
        }))
      };
    });
    
    // Read vector data from bucket
    this.server.setRequestHandler('resources/read', async (request) => {
      const { uri } = request.params;
      const bucketName = uri.replace('minio://vectors/', '');
      
      const vectors = await this.readVectorBucket(bucketName);
      return {
        contents: [{
          uri,
          mimeType: 'application/json',
          text: JSON.stringify(vectors, null, 2)
        }]
      };
    });
    
    // Semantic search tool
    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: [
          {
            name: 'semantic_search',
            description: 'Search for relevant content using semantic similarity',
            inputSchema: {
              type: 'object',
              properties: {
                query: { type: 'string', description: 'Search query' },
                department: { type: 'string', description: 'Department to search in (optional)' },
                top_k: { type: 'number', description: 'Number of results to return', default: 5 }
              },
              required: ['query']
            }
          },
          {
            name: 'rag_query',
            description: 'Retrieve augmented context for a query',
            inputSchema: {
              type: 'object',
              properties: {
                query: { type: 'string', description: 'Query for context retrieval' },
                departments: { 
                  type: 'array', 
                  items: { type: 'string' },
                  description: 'Departments to search (optional)'
                },
                max_tokens: { type: 'number', description: 'Maximum context tokens', default: 2000 }
              },
              required: ['query']
            }
          }
        ]
      };
    });
    
    // Handle tool calls
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      switch (name) {
        case 'semantic_search':
          return await this.semanticSearch(args);
        case 'rag_query':
          return await this.ragQuery(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }
  
  async listVectorBuckets() {
    try {
      const buckets = await minioClient.listBuckets();
      return buckets
        .filter(b => b.name.startsWith(config.vectorBucketPrefix))
        .map(b => b.name);
    } catch (error) {
      console.error('Error listing buckets:', error);
      return [];
    }
  }
  
  async readVectorBucket(bucketName) {
    try {
      const objects = [];
      const stream = minioClient.listObjectsV2(bucketName, '', true);
      
      for await (const obj of stream) {
        if (obj.name.endsWith('.json')) {
          const dataStream = await minioClient.getObject(bucketName, obj.name);
          const chunks = [];
          
          for await (const chunk of dataStream) {
            chunks.push(chunk);
          }
          
          const data = JSON.parse(Buffer.concat(chunks).toString());
          objects.push(...data);
        }
      }
      
      return objects;
    } catch (error) {
      console.error('Error reading bucket:', error);
      return [];
    }
  }
  
  async loadAllVectors() {
    // Cache vectors for faster search
    if (this.lastCacheUpdate && 
        Date.now() - this.lastCacheUpdate < 300000) { // 5 min cache
      return;
    }
    
    const buckets = await this.listVectorBuckets();
    
    for (const bucket of buckets) {
      const vectors = await this.readVectorBucket(bucket);
      this.vectorCache.set(bucket, vectors);
    }
    
    this.lastCacheUpdate = Date.now();
  }
  
  async semanticSearch(args) {
    const { query, department, top_k = 5 } = args;
    
    await this.loadAllVectors();
    
    // Get query embedding (simplified - in production, call embedding service)
    const queryEmbedding = await this.getQueryEmbedding(query);
    
    const results = [];
    const bucketsToSearch = department 
      ? [`${config.vectorBucketPrefix}${department}`]
      : Array.from(this.vectorCache.keys());
    
    for (const bucket of bucketsToSearch) {
      const vectors = this.vectorCache.get(bucket) || [];
      
      for (const vector of vectors) {
        const similarity = cosineSimilarity(queryEmbedding, vector.embedding);
        results.push({
          ...vector,
          similarity,
          bucket
        });
      }
    }
    
    // Sort by similarity and take top K
    results.sort((a, b) => b.similarity - a.similarity);
    const topResults = results.slice(0, top_k);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          query,
          results: topResults.map(r => ({
            text: r.text,
            similarity: r.similarity,
            source: r.source_file,
            department: r.department,
            metadata: r.metadata
          }))
        }, null, 2)
      }]
    };
  }
  
  async ragQuery(args) {
    const { query, departments, max_tokens = 2000 } = args;
    
    // Perform semantic search
    const searchResults = await this.semanticSearch({
      query,
      department: departments?.[0],
      top_k: 10
    });
    
    const results = JSON.parse(searchResults.content[0].text).results;
    
    // Build context from top results
    let context = [];
    let tokenCount = 0;
    const approxTokensPerChar = 0.25;
    
    for (const result of results) {
      const resultTokens = result.text.length * approxTokensPerChar;
      if (tokenCount + resultTokens > max_tokens) break;
      
      context.push({
        content: result.text,
        source: result.source,
        relevance: result.similarity
      });
      
      tokenCount += resultTokens;
    }
    
    // Format RAG response
    const ragResponse = {
      query,
      context,
      instructions: "Use the provided context to answer the query. The context is ordered by relevance.",
      metadata: {
        sources_used: context.length,
        departments_searched: departments || 'all',
        token_count: Math.round(tokenCount)
      }
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(ragResponse, null, 2)
      }]
    };
  }
  
  async getQueryEmbedding(query) {
    // Simplified: generate random embedding for demo
    // In production, call Cloudflare Workers AI or local embedding service
    const dim = 768; // Standard BERT dimension
    const embedding = Array.from({ length: dim }, () => Math.random());
    
    // Normalize
    const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => val / norm);
  }
  
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('MCP Vector Server running');
  }
}

// Also run HTTP API server for web access
function startHttpServer() {
  const app = express();
  app.use(cors());
  app.use(express.json());
  
  const vectorServer = new VectorMCPServer();
  
  // Health check
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'mcp-vector-server' });
  });
  
  // List vector buckets
  app.get('/api/v1/vector-buckets', async (req, res) => {
    try {
      const buckets = await vectorServer.listVectorBuckets();
      res.json({ buckets });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // Semantic search
  app.post('/api/v1/search', async (req, res) => {
    try {
      const result = await vectorServer.semanticSearch(req.body);
      res.json(JSON.parse(result.content[0].text));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  // RAG query
  app.post('/api/v1/rag', async (req, res) => {
    try {
      const result = await vectorServer.ragQuery(req.body);
      res.json(JSON.parse(result.content[0].text));
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
  
  app.listen(config.httpPort, () => {
    console.log(`HTTP API server running on port ${config.httpPort}`);
  });
}

// Main execution
if (require.main === module) {
  // Check if running as MCP server or HTTP server
  if (process.argv.includes('--http')) {
    startHttpServer();
  } else {
    const server = new VectorMCPServer();
    server.run().catch(console.error);
  }
}

module.exports = { VectorMCPServer };
