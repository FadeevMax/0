import os
import json
import tempfile
import traceback
from pathlib import Path
import requests
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
import hashlib

from utils.document_processor import enhanced_chunk_docx
from utils.search_engine import enhanced_search
from utils.llm_client import SimpleLLMClient
from utils.github_client import GitHubClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
ALLOWED_EXTENSIONS = {'docx'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Initialize clients
llm_client = SimpleLLMClient()
github_client = GitHubClient()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only DOCX files allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Get chunk size from request
        chunk_size = int(request.form.get('chunk_size', 800))
        
        # Process document
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        chunks = enhanced_chunk_docx(file_content, chunk_size)
        
        if chunks:
            # Store chunks in session
            session['chunks'] = chunks
            session['processing_complete'] = True
            session['vector_db_ready'] = True
            
            # Clean up uploaded file
            os.remove(filepath)
            
            # Count chunks with images
            chunks_with_images = sum(1 for c in chunks if c.get('images'))
            total_images = sum(len(c.get('images', [])) for c in chunks)
            
            return jsonify({
                'success': True,
                'message': f'Document processed successfully! Created {len(chunks)} chunks.',
                'chunks_count': len(chunks),
                'chunks_with_images': chunks_with_images,
                'total_images': total_images,
                'preview': chunks[0]['text'][:200] + '...' if chunks else ''
            })
        else:
            return jsonify({'error': 'Failed to process document'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500

@app.route('/api/load-from-github', methods=['POST'])
def load_from_github():
    """Load chunks from GitHub JSON file"""
    try:
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token not configured'}), 500
        
        data = request.get_json()
        repo_url = data.get('repo_url')
        file_path = data.get('file_path', 'output/hybrid_chunks.json')
        
        if not repo_url:
            return jsonify({'error': 'Repository URL required'}), 400
        
        # Extract owner and repo from URL
        parts = repo_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            return jsonify({'error': 'Invalid GitHub URL'}), 400
        
        owner, repo = parts[0], parts[1]
        
        # Fetch chunks from GitHub
        chunks = github_client.fetch_chunks(owner, repo, file_path, github_token)
        
        if chunks:
            session['chunks'] = chunks
            session['processing_complete'] = True
            session['vector_db_ready'] = True
            
            return jsonify({
                'success': True,
                'message': f'Loaded {len(chunks)} chunks from GitHub',
                'chunks_count': len(chunks)
            })
        else:
            return jsonify({'error': 'Failed to load chunks from GitHub'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error loading from GitHub: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        if not session.get('processing_complete'):
            return jsonify({'error': 'Please process a document first'}), 400
        
        data = request.get_json()
        query = data.get('query', '')
        model = data.get('model', 'GPT-4 Mini')
        temperature = float(data.get('temperature', 0.1))
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        # Get API keys from environment
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Setup LLM client
        llm_client.setup_keys(openai_key, '')
        
        # Search for relevant chunks
        chunks = session.get('chunks', [])
        search_results = enhanced_search(chunks, query, top_k=5)
        
        if search_results:
            # Build context
            query_lower = query.lower()
            analytical_keywords = [
                'how many', 'what states', 'which state', 'highest', 'lowest', 'compare', 
                'all states', 'total', 'maximum', 'minimum', 'list all', 'differences',
                'across states', 'between states', 'summary', 'overview'
            ]
            
            is_analytical = any(keyword in query_lower for keyword in analytical_keywords)
            
            if is_analytical:
                context_parts = [f"USER QUESTION: {query}\n\nCOMPREHENSIVE DATA FOR ANALYSIS:"]
                
                state_data = {}
                all_topics = set()
                
                for i, result in enumerate(search_results):
                    chunk = result['chunk']
                    metadata = chunk.get('metadata', {})
                    states = metadata.get('states', [])
                    topics = metadata.get('topics', [])
                    
                    context_parts.append(f"\n--- Section {i+1} (Score: {result['score']:.2f}) ---")
                    
                    if states:
                        context_parts.append(f"STATES: {', '.join(states)}")
                    if topics:
                        context_parts.append(f"TOPICS: {', '.join(topics)}")
                        all_topics.update(topics)
                    
                    for state in states:
                        if state not in state_data:
                            state_data[state] = []
                        state_data[state].append({
                            'text': chunk['text'],
                            'topics': topics,
                            'score': result['score']
                        })
                    
                    context_parts.append(f"CONTENT: {chunk['text']}")
                
                context_parts.append(f"\n--- SUMMARY FOR ANALYSIS ---")
                context_parts.append(f"TOTAL SECTIONS FOUND: {len(search_results)}")
                context_parts.append(f"STATES MENTIONED: {', '.join(sorted(state_data.keys()))}")
                context_parts.append(f"TOPICS COVERED: {', '.join(sorted(all_topics))}")
                context_parts.append(f"\nINSTRUCTION: Please analyze ALL the provided sections to answer the user's question.")
                
            else:
                context_parts = [f"USER QUESTION: {query}\n\nRELEVANT DOCUMENTATION:"]
                
                for i, result in enumerate(search_results):
                    context_parts.append(f"\n--- Section {i+1} (Score: {result['score']:.2f}) ---")
                    context_parts.append(result['chunk']['text'])
            
            context = '\n'.join(context_parts)
            
            # Generate response
            answer = llm_client.generate_response(model, context, temperature)
            
            # Get relevant images
            relevant_images = get_relevant_images(search_results, query)
            
            return jsonify({
                'success': True,
                'answer': answer,
                'search_results': [{
                    'score': result['score'],
                    'preview': result['chunk']['text'][:150] + '...',
                    'metadata': result['chunk'].get('metadata', {})
                } for result in search_results],
                'images': relevant_images
            })
        else:
            return jsonify({
                'success': True,
                'answer': "I couldn't find relevant information for your query. Please try rephrasing your question.",
                'search_results': [],
                'images': []
            })
            
    except Exception as e:
        return jsonify({'error': f'Error processing chat: {str(e)}'}), 500

def get_relevant_images(search_results, query):
    """Extract relevant images from search results"""
    relevant_images = []
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    concept_keywords = {
        'order': ['order', 'ordering', 'purchase'],
        'form': ['form', 'template', 'document'],
        'invoice': ['invoice', 'billing', 'payment'],
        'delivery': ['delivery', 'shipping', 'schedule'],
        'battery': ['battery', 'batteries'],
        'pricing': ['price', 'pricing', 'cost'],
        'substitution': ['sub', 'substitution', 'batch'],
        'rise': ['rise', 'internal'],
        'regular': ['regular', 'wholesale'],
        'limit': ['limit', 'maximum', 'max'],
        'note': ['note', 'notes', 'required'],
        'split': ['split', 'splitting']
    }
    
    query_concepts = []
    for concept, keywords in concept_keywords.items():
        if any(kw in query_lower for kw in keywords):
            query_concepts.append(concept)
    
    for result in search_results[:3]:
        chunk = result['chunk']
        if chunk.get('images') and result['score'] > 0.3:
            for img in chunk['images']:
                img_label_lower = img['label'].lower()
                img_words = set(img_label_lower.split())
                
                relevance_score = 0
                
                # Direct word overlap
                word_overlap = len(query_words.intersection(img_words))
                relevance_score += word_overlap * 2
                
                # Concept overlap
                img_concepts = []
                for concept, keywords in concept_keywords.items():
                    if any(kw in img_label_lower for kw in keywords):
                        img_concepts.append(concept)
                
                concept_overlap = len(set(query_concepts).intersection(set(img_concepts)))
                relevance_score += concept_overlap * 1.5
                
                # Chunk relevance bonus
                chunk_bonus = result['score'] * 1.0
                relevance_score += chunk_bonus
                
                # Set label bonus to 0 as requested
                label_bonus = 0
                relevance_score += label_bonus
                
                min_threshold = 1.5 if query_concepts else 1.0
                
                if relevance_score >= min_threshold:
                    relevant_images.append({
                        'filename': img['filename'],
                        'label': img['label'],
                        'score': relevance_score,
                        'chunk_score': result['score']
                    })
    
    relevant_images.sort(key=lambda x: x['score'], reverse=True)
    return relevant_images[:3]

@app.route('/api/chunks')
def get_chunks():
    """Get processed chunks"""
    if not session.get('processing_complete'):
        return jsonify({'error': 'No document processed'}), 400
    
    chunks = session.get('chunks', [])
    search_term = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    
    if search_term:
        chunks = [
            chunk for chunk in chunks 
            if search_term.lower() in chunk['text'].lower()
        ]
    
    total = len(chunks)
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'chunks': chunks[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/status')
def get_status():
    """Get processing status"""
    return jsonify({
        'processing_complete': session.get('processing_complete', False),
        'vector_db_ready': session.get('vector_db_ready', False),
        'chunks_count': len(session.get('chunks', []))
    })

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve processed images"""
    temp_dir = session.get('temp_image_dir')
    if temp_dir and os.path.exists(os.path.join(temp_dir, filename)):
        return send_from_directory(temp_dir, filename)
    return '', 404

if __name__ == '__main__':
    app.run(debug=True)