# QA Agent for Context-Aware Test Case Generation

This project integrates a LangGraph-based agent with Azure DevOps and a vector database (Qdrant/Weaviate) to generate context-aware test cases for user stories.

## Features

- **Contextual Test Generation**: Uses previous similar test cases to generate better quality tests
- **Vector Database Integration**: Stores user stories and test cases as vector embeddings
- **Azure DevOps Integration**: Automatically creates test cases linked to user stories
- **LangGraph Agent**: Customizable multi-step workflow for test case generation
- **Multiple Output Formats**: Generates both markdown and CSV formats for test cases
- **Enhanced Embedding Service**: High-performance text embedding with caching and optimized batch processing

## Project Structure

```
qa-agent-project/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration loading
│   ├── routes/
│   │   └── webhook.py           # Azure DevOps webhook handler
│   ├── services/
│   │   ├── langgraph_runner.py  # LangGraph agent runner
│   │   ├── embedding.py         # Embedding service
│   │   ├── vector_store.py      # Vector database interface
│   │   └── azure_devops.py      # Azure DevOps API integration
│   ├── models/
│   │   ├── agent_state.py       # LangGraph agent state types
│   │   └── data_models.py       # Data models
│   ├── prompts/
│   │   └── test_case_prompts.py # Prompt templates
│   └── utils/
│       └── csv_writer.py        # CSV conversion utilities
│
├── langgraph/
│   └── qa_agent_graph.py        # LangGraph agent implementation
│
├── vector_db/
│   ├── schema.yaml              # Vector DB schema config
│   └── test_vector_db.py        # Utility to test vector DB operations
│
├── examples/
│   └── embedding_service_demo.py # Demo script for embedding service
│
├── tests/
│   ├── test_langgraph.py
│   ├── test_embedding.py
│   └── test_vector_store.py
│
├── requirements.txt
├── .env
├── README.md
└── run_local.sh                 # Script for local testing
```

## Setup and Installation

### Prerequisites

- Python 3.9+
- Qdrant or Weaviate instance (can be run locally with Docker)
- Azure DevOps account with PAT (for Azure DevOps integration)
- OpenAI API key (for LLM and embeddings)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd test_generation_agent
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   AZURE_DEVOPS_PAT=your-azure-devops-pat
   AZURE_DEVOPS_ORG=your-organization
   AZURE_DEVOPS_PROJECT=your-project
   VECTOR_DB_TYPE=weaviate  # Options: weaviate, qdrant
   QDRANT_URL=http://localhost:6333
   WEAVIATE_URL=http://localhost:8080
   EMBEDDING_MODEL=text-embedding-3-small
   EMBEDDING_DIMENSIONS=1536
   EMBEDDING_CACHE_SIZE=1000
   BATCH_SIZE=32
   MAX_RETRY_ATTEMPTS=3
   ```

### Vector Database Setup

#### Qdrant Setup (Option 1)

Start Qdrant using Docker:
```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

#### Weaviate Setup (Option 2)

Start Weaviate using Docker Compose:
1. Create a `docker-compose.yml` file:
```yaml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.19.6
    ports:
      - "8080:8080"
    restart: on-failure:0
    environment:
      QUERY_DEFAULTS_LIMIT: 20
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: './data'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
```

2. Start Weaviate:
```bash
docker-compose up -d
```

### Testing the Vector Database

You can test the vector database functionality using the provided utility script:

```bash
# Test with the default vector DB type from .env
python vector_db/test_vector_db.py --action all

# Test with a specific vector DB type
python vector_db/test_vector_db.py --db-type weaviate --action store

# Test retrieval with a custom query
python vector_db/test_vector_db.py --action retrieve --query "As a user, I want to update my profile picture"

# Test health check only
python vector_db/test_vector_db.py --action health
```

6. Run the application:
   ```
   ./run_local.sh
   ```

## Usage

### Via Webhook (Automated)

1. Set up an Azure DevOps Service Hook for work item creation/update events pointing to:
   ```
   http://your-server:8000/webhook/azure-devops
   ```

2. When new user stories are created, the system will automatically:
   - Extract the user story details
   - Find similar past user stories and test cases
   - Generate contextually relevant test cases
   - Create test cases in Azure DevOps Test Plans
   - Link the test cases to the original user story

### Manual API Usage

You can also trigger test case generation manually via the API:

```bash
curl -X POST http://localhost:8000/webhook/manual \
  -H "Content-Type: application/json" \
  -d '{"story_id":"12345","project_id":"project-123","title":"User can reset password","description":"As a user, I want to be able to reset my password if I forget it..."}'
```

## Embedding Service

The project includes an enhanced embedding service with the following features:

### Key Features

- **Multiple Model Support**: Compatible with OpenAI's text-embedding models and Sentence Transformers
- **Efficient Caching**: LRU-based caching to avoid redundant API calls during testing and development
- **Batch Processing**: Optimized batch processing for faster handling of multiple texts
- **Error Handling**: Robust error handling with automatic retries for transient issues
- **Performance Monitoring**: Built-in timing and statistics for performance analysis

### Configuration Options

The embedding service can be configured using the following environment variables:

- `EMBEDDING_MODEL`: Model to use (default: "text-embedding-3-small")
- `EMBEDDING_DIMENSIONS`: Expected embedding dimensions (default: 1536)
- `EMBEDDING_CACHE_SIZE`: Maximum entries in the cache (default: 1000)
- `BATCH_SIZE`: Number of texts to process in a batch (default: 32)
- `MAX_RETRY_ATTEMPTS`: Maximum retry attempts for API calls (default: 3)

### Example Usage

Basic usage of the embedding service:

```python
from app.services.embedding import get_embedding_service

# Get a singleton instance of the embedding service
embedding_service = get_embedding_service()

# Generate embeddings for a user story
story_embedding = embedding_service.embed_user_story(
    title="User can reset password",
    description="As a user, I want to reset my password easily"
)

# Generate embeddings for multiple texts
texts = ["First text", "Second text", "Third text"]
embeddings = embedding_service.embed_texts(texts)

# Get cache statistics
cache_stats = embedding_service.get_cache_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']}")
```

### Demonstration Script

A demonstration script is provided to showcase the embedding service capabilities:

```bash
# Run with default settings
python examples/embedding_service_demo.py

# Use a specific embedding model
python examples/embedding_service_demo.py --model all-MiniLM-L6-v2

# Customize cache size
python examples/embedding_service_demo.py --cache-size 500
```

## Vector Database Integration

This project supports two vector database options:

### Qdrant Integration

Qdrant is used to store and retrieve vector embeddings for user stories and test cases. The implementation:
- Creates collections for user stories and test cases
- Stores user stories with their vector embeddings
- Stores test cases with their vector embeddings
- Provides similarity search for finding related stories and test cases
- Uses cosine similarity for vector comparisons

### Weaviate Integration

Weaviate provides an alternative vector database with schema-based configuration:
- Uses schema-based classes for UserStory and TestCase
- Stores objects with their vector embeddings
- Provides semantic search with certainty scores
- Supports filtering and sorting of results
- Automatic schema creation from YAML configuration

To switch between vector databases, simply update the `VECTOR_DB_TYPE` in your `.env` file.

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Vector DB Support

1. Create a new class in `app/services/vector_store.py` implementing the `VectorStoreService` interface
2. Update the `get_vector_store()` function to include your new vector store type
3. Create any necessary schema files in the `vector_db` directory

## License

MIT

## Acknowledgments

- This project uses [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Vector embeddings powered by OpenAI
- Qdrant and Weaviate for vector database functionality
