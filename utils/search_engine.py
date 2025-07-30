import re

def enhanced_search(chunks, query, top_k=5):
    """Enhanced search with context and metadata awareness"""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Detect if this is a comparison/analytical question
    analytical_keywords = [
        'how many', 'what states', 'which state', 'highest', 'lowest', 'compare', 
        'all states', 'total', 'maximum', 'minimum', 'list all', 'differences',
        'across states', 'between states', 'summary', 'overview'
    ]
    
    is_analytical = any(keyword in query_lower for keyword in analytical_keywords)
    
    if is_analytical:
        # For analytical questions, we need broader context
        top_k = min(15, len(chunks))  # Get more chunks for analysis
    
    # Extract query intent
    query_state = None
    query_section = None
    query_topics = []
    
    # State detection
    state_patterns = {
        'OH': [r'\boh\b', r'\bohio\b'],
        'MD': [r'\bmd\b', r'\bmaryland\b'],
        'NJ': [r'\bnj\b', r'\bnew jersey\b', r'\bjersey\b'],
        'IL': [r'\bil\b', r'\billinois\b'],
        'NY': [r'\bny\b', r'\bnew york\b'],
        'NV': [r'\bnv\b', r'\bnevada\b'],
        'MA': [r'\bma\b', r'\bmassachusetts\b']
    }
    
    for state, patterns in state_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                query_state = state
                break
    
    # Section detection
    if 'rise' in query_lower or 'internal' in query_lower:
        query_section = 'RISE'
    elif 'regular' in query_lower or 'wholesale' in query_lower:
        query_section = 'REGULAR'
    
    # Topic detection
    topic_keywords = {
        'PRICING': ['price', 'pricing', 'cost', 'discount', 'menu'],
        'BATTERIES': ['battery', 'batteries', 'separate', 'invoice'],
        'BATCH_SUB': ['batch', 'sub', 'substitution', 'split'],
        'DELIVERY_DATE': ['delivery', 'date', 'schedule'],
        'ORDER_LIMIT': ['limit', 'maximum', 'max', 'unit'],
        'LESS_AVAILABLE': ['less', 'available', 'partial', 'shortage']
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            query_topics.append(topic)
    
    # Score chunks
    scored_chunks = []
    for chunk in chunks:
        score = 0
        text_lower = chunk['text'].lower()
        text_words = set(text_lower.split())
        metadata = chunk.get('metadata', {})
        
        # Base keyword overlap score
        overlap = len(query_words.intersection(text_words))
        score += overlap / max(len(query_words), 1)
        
        # Boost for exact phrase matches
        for word in query_words:
            if len(word) > 3 and word in text_lower:
                score += 0.3
        
        # Boost for metadata matches
        if query_state and query_state in metadata.get('states', []):
            score += 0.5
        
        if query_section and query_section in metadata.get('sections', []):
            score += 0.3
        
        for topic in query_topics:
            if topic in metadata.get('topics', []):
                score += 0.4
        
        # Boost for images if visual content is requested
        if any(word in query_lower for word in ['image', 'show', 'example', 'visual']):
            if metadata.get('has_images'):
                score += 0.3
        
        # Boost for longer, more complete content
        if len(chunk['text']) > 200:
            score += 0.1
        
        if score > 0:
            scored_chunks.append({
                'chunk': chunk,
                'score': score,
                'chunk_id': chunk['chunk_id'],
                'search_types': []
            })
    
    # Sort by score and return top results
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:top_k]