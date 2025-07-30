# GTI SOP Assistant - Flask Web App

A Flask web application that replicates the functionality of the Streamlit SOP Assistant, designed for deployment on Vercel.

## Features

- **Document Processing**: Upload and process DOCX files with image extraction
- **GitHub Integration**: Load pre-processed chunks from GitHub repositories
- **Enhanced Search**: Context-aware search with metadata filtering
- **AI Chat**: OpenAI-powered chat interface for document queries
- **Image Support**: Display relevant images based on search context

## Setup

### Local Development

1. Clone the repository and navigate to the project directory:
   ```bash
   cd flask_sop_app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here
   SECRET_KEY=your_secret_key_here
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open http://localhost:5000 in your browser

### Vercel Deployment

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy to Vercel:
   ```bash
   vercel --prod
   ```

3. Set environment variables in Vercel dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GITHUB_TOKEN`: Your GitHub personal access token
   - `SECRET_KEY`: A secure random string for sessions

## Environment Variables

### Required Variables

- **OPENAI_API_KEY**: OpenAI API key for AI chat functionality
- **GITHUB_TOKEN**: GitHub personal access token for loading chunks from repositories
- **SECRET_KEY**: Flask secret key for session management

### Setting Up GitHub Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` scope
3. Add the token to your environment variables

### Setting Up OpenAI API Key

1. Go to OpenAI Platform (https://platform.openai.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Add the key to your environment variables

## Usage

### Processing Documents

1. Navigate to the "Process Document" tab
2. Upload a DOCX file or load from GitHub
3. Configure chunk size (default: 800 characters)
4. Click "Process Document"

### GitHub Integration

1. Enter your GitHub repository URL
2. Specify the path to your chunks JSON file (default: `output/hybrid_chunks.json`)
3. Click "Load from GitHub"

### Chat Interface

1. Navigate to the "Search & Chat" tab
2. Ask questions about your processed documents
3. View search results and related images
4. Adjust AI model and temperature in the sidebar

### Viewing Chunks

1. Navigate to the "View Chunks" tab
2. Search through processed chunks
3. Use pagination to browse all chunks
4. View metadata for each chunk

## Project Structure

```
flask_sop_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
├── .env.example          # Environment variables template
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   └── index.html        # Main page template
└── utils/                # Utility modules
    ├── __init__.py
    ├── document_processor.py  # DOCX processing
    ├── search_engine.py       # Search functionality
    ├── llm_client.py          # OpenAI client
    └── github_client.py       # GitHub integration
```

## API Endpoints

- `GET /` - Main application page
- `POST /api/upload` - Upload and process DOCX file
- `POST /api/load-from-github` - Load chunks from GitHub
- `POST /api/chat` - Chat with processed documents
- `GET /api/chunks` - Get processed chunks with pagination
- `GET /api/status` - Get processing status
- `GET /images/<filename>` - Serve processed images

## Dependencies

- **Flask**: Web framework
- **python-docx**: DOCX file processing
- **requests**: HTTP requests for GitHub and OpenAI APIs
- **openai**: OpenAI API client
- **Werkzeug**: WSGI utilities

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

2. **API Key Errors**: Verify your OpenAI API key and GitHub token are set correctly in environment variables

3. **File Upload Issues**: Ensure the `uploads/` and `temp/` directories have write permissions

4. **Vercel Deployment Issues**: Check that all environment variables are set in the Vercel dashboard

### Debug Mode

For local development, the app runs in debug mode. For production deployment, debug mode is automatically disabled.

## Security Notes

- Never commit API keys to version control
- Use strong, unique secret keys for production
- Environment variables are handled securely in Vercel
- File uploads are restricted to DOCX files only
- Temporary files are cleaned up after processing