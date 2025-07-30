import requests
import json
import base64

class GitHubClient:
    def __init__(self):
        pass
    
    def fetch_chunks(self, owner, repo, file_path, token):
        """Fetch chunks from GitHub repository"""
        try:
            # GitHub API URL for file content
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Decode base64 content
                content = base64.b64decode(data['content']).decode('utf-8')
                
                # Parse JSON content
                chunks = json.loads(content)
                
                # Validate chunks format
                if isinstance(chunks, list) and all(isinstance(chunk, dict) for chunk in chunks):
                    return chunks
                else:
                    print("Invalid chunks format in GitHub file")
                    return []
            else:
                print(f"Failed to fetch from GitHub: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching from GitHub: {str(e)}")
            return []
    
    def fetch_raw_file(self, owner, repo, file_path, token):
        """Fetch raw file content from GitHub"""
        try:
            # Use raw.githubusercontent.com for direct file access
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch raw file: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching raw file: {str(e)}")
            return None