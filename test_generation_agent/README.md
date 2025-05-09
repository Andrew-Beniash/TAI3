# Test Generation Agent

Automate the generation of detailed, context-aware QA test cases for user stories created in Azure DevOps by integrating a LangGraph-based agent with Azure DevOps service hooks and a vector database.

## Architecture

This system integrates the following components:

1. **Azure DevOps Service Hook**: Triggered on user story creation or update
2. **Webhook Service (API Layer)**: Receives POST requests from Azure DevOps
3. **LangGraph QA Agent**: Generates detailed test cases with edge, negative, and positive scenarios
4. **Vector Store**: Stores vector embeddings for user stories and test cases
5. **Embedding Service**: Vectorizes both new input and indexed documents

![Architecture Diagram](docs/architecture-diagram.png)

## Features

- **Context-Aware Test Generation**: Leverages similar previous user stories and test cases to improve relevance
- **Multiple Vector Database Support**: Works with Weaviate, Qdrant, or FAISS
- **Comprehensive Test Coverage**: Generates positive, negative, and edge case scenarios
- **Azure DevOps Integration**: Automatically creates and links test cases to user stories
- **CSV Export**: Provides test cases in CSV format for manual testing

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key
- Azure DevOps organization with Personal Access Token (PAT)
- Vector database (Weaviate, Qdrant, or FAISS)

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd test_generation_agent
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the application:
   ```bash
   python launch.py
   ```

### Using Docker

1. Create a `.env` file based on `.env.example`

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. The application will be available at http://localhost:8000

## Configuration

The application is configured through environment variables, which can be set in the `.env` file:

- **API Configuration**:
  - `DEBUG`: Set to "True" for development mode
  - `HOST`: Host to bind the server to (default: "0.0.0.0")
  - `PORT`: Port to bind the server to (default: 8000)

- **Azure DevOps Settings**:
  - `AZURE_DEVOPS_ORG`: Your Azure DevOps organization name
  - `AZURE_DEVOPS_PAT`: Personal Access Token for Azure DevOps
  - `AZURE_DEVOPS_PROJECT`: Your Azure DevOps project name

- **OpenAI Settings**:
  - `OPENAI_API_KEY`: Your OpenAI API key
  - `OPENAI_EMBEDDING_MODEL`: Embedding model to use (default: "text-embedding-3-small")
  - `OPENAI_COMPLETION_MODEL`: Completion model to use (default: "gpt-4")

- **Vector DB Settings**:
  - `VECTOR_DB_TYPE`: Type of vector DB (weaviate, qdrant, or faiss)
  - `VECTOR_DB_URL`: URL of the vector database
  - `VECTOR_DB_API_KEY`: API key for the vector database (if required)

- **Webhook Security**:
  - `WEBHOOK_SECRET`: Secret for signing and verifying webhook requests

## API Endpoints

- `GET /`: Root endpoint (health check)
- `GET /health`: Health check endpoint
- `POST /api/v1/webhook/azure-devops`: Webhook endpoint for Azure DevOps service hooks
- `POST /api/v1/webhook/mock`: Mock endpoint for testing without Azure DevOps

## Testing

### Running Tests

Run the automated tests using pytest:

```bash
pytest
```

### Manual Testing

You can manually test the webhook endpoint using curl or Postman:

```bash
# Using curl
curl -X POST \
  -H "Content-Type: application/json" \
  -d @tests/mock_payload.json \
  http://localhost:8000/api/v1/webhook/mock
```

A Postman collection is available at `tests/Test_Generation_Agent.postman_collection.json`.

## Azure DevOps Integration

### Setting Up Personal Access Token (PAT)

1. In Azure DevOps, go to User Settings > Personal Access Tokens
2. Create a new Personal Access Token with the following scopes:
   - Work Items: Read & Write
   - Test Management: Read & Write
3. Copy the generated token and add it to your `.env` file as `AZURE_DEVOPS_PAT`

### Setting Up Azure AD App (Alternative to PAT)

For production environments, it's recommended to use Azure AD App authentication:

1. Register a new application in Azure AD
2. Set the redirect URI to your application's callback URL
3. Grant API permissions for Azure DevOps
4. Configure your application to use the client ID and client secret

### Setting Up Webhook

1. In Azure DevOps, go to Project Settings > Service Hooks
2. Create a new Service Hook with the following configuration:
   - Trigger: Work item created or updated
   - Filters: Work item type = User Story
   - Action: WebHook
   - URL: Your webhook endpoint URL (e.g., https://your-domain.com/api/v1/webhook/azure-devops)
   - Basic Authentication: If enabled, add credentials
   - Headers: Add a secret if using WEBHOOK_SECRET

### Using the Azure DevOps Test Plans API

The application uses the Azure DevOps Test Plans API to create and manage test cases. Here's how it works:

1. When a new user story is created or updated in Azure DevOps, the webhook is triggered
2. The application generates test cases using the LangGraph agent
3. The test cases are created in Azure DevOps using the Test Plans API
4. The test cases are linked to the original user story using WorkItemRelation

The `AzureDevOpsService` class in `app/services/azure_devops.py` provides the following functionality:

- Creating test plans and test suites
- Creating test cases with detailed steps
- Adding test cases to test suites
- Linking test cases to user stories

### Example Usage

```python
from app.services.azure_devops import AzureDevOpsService
from app.models.data_models import TestCaseRecord

# Initialize the Azure DevOps service
azure_devops = AzureDevOpsService()

# Create a test case record
test_case = TestCaseRecord(
    story_id="123",
    title="Test Case Title",
    description="Test case description",
    steps=[
        {"action": "Step 1", "expected": "Expected Result 1"},
        {"action": "Step 2", "expected": "Expected Result 2"},
    ],
    test_case_text="# Test Case Title\n\n## Description\nTest case description\n\n## Steps\n1. Step 1\n   - Expected: Expected Result 1\n2. Step 2\n   - Expected: Expected Result 2"
)

# Create the test case in Azure DevOps and link it to the user story
azure_devops.create_test_cases_for_story(123, [test_case])
```

### Running the Example

An example script is provided to demonstrate the Azure DevOps integration:

```bash
# Update the user_story_id in the script first
python examples/azure_devops_example.py
```

## Project Structure

```
test_generation_agent/
├── app/
│   ├── main.py                  # FastAPI entry point (webhook receiver)
│   ├── config.py                # Env var loading, secrets, model config
│   ├── routes/
│   │   └── webhook.py           # POST handler for Azure DevOps webhook
│   ├── services/
│   │   ├── langgraph_runner.py  # LangGraph agent invocation logic
│   │   ├── embedding.py         # Embedding model wrapper
│   │   ├── vector_store.py      # Interface to Weaviate or Qdrant
│   │   └── azure_devops.py      # Handles Azure DevOps integration
│   ├── models/
│   │   └── data_models.py       # Pydantic models for request/response
│   ├── prompts/
│   │   └── test_case_prompts.py # Prompt templates used in LangGraph nodes
│   └── utils/
│       └── csv_writer.py        # CSV generation from agent output
│
├── langgraph/
│   └── qa_agent_graph.py        # Full LangGraph agent with all nodes
│
├── vector_db/
│   └── schema.yaml              # Schema config for Weaviate/Qdrant
│
├── tests/
│   ├── test_webhook.py
│   ├── test_embedding.py
│   ├── test_csv_writer.py
│   └── mock_payload.json
│
├── docs/
│   └── architecture-diagram.png # Architecture diagram
│
├── examples/
│   └── azure_devops_example.py  # Example script for Azure DevOps integration
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── launch.py                    # Script to start the application
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
