import chromadb
import hashlib
import os
from typing import List, Dict, Optional, Any
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..config import settings as app_settings

class VectorStore:
    def __init__(self):
        self.chroma_db_path = app_settings.CHROMA_DB_PATH
        
        if not os.path.exists(self.chroma_db_path):
            os.makedirs(self.chroma_db_path)
        
        self.client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        collection_name = "code_documents"
        
        try:
            return self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except ValueError:
            return self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Repository code documents for semantic search"}
            )

    async def add_document(self, file_path: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        try:
            if not content or not content.strip():
                return
            
            doc_id = self._generate_doc_id(file_path, content)
            
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "file_path": file_path,
                "content_length": len(content),
                "file_extension": os.path.splitext(file_path)[1]
            })
            
            chunks = self._chunk_content(content, file_path)
            
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_start": chunk["start"],
                    "chunk_end": chunk["end"]
                })
                
                ids.append(chunk_id)
                documents.append(chunk["content"])
                metadatas.append(chunk_metadata)
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
        except Exception as e:
            print(f"Error adding document {file_path}: {str(e)}")

    async def search(self, query: str, limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        try:
            where_clause = filter_metadata if filter_metadata else None
            
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    search_results.append({
                        "content": doc,
                        "file_path": metadata.get("file_path", ""),
                        "language": metadata.get("language", ""),
                        "relevance_score": round(1.0 - distance, 3),
                        "context": self._generate_context(doc, metadata),
                        "metadata": metadata
                    })
            
            return search_results
            
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    async def search_by_file_type(self, query: str, file_extension: str, limit: int = 10) -> List[Dict]:
        filter_metadata = {"file_extension": file_extension}
        return await self.search(query, limit, filter_metadata)

    async def search_by_language(self, query: str, language: str, limit: int = 10) -> List[Dict]:
        filter_metadata = {"language": language}
        return await self.search(query, limit, filter_metadata)

    async def get_similar_files(self, file_path: str, limit: int = 5) -> List[Dict]:
        try:
            file_docs = self.collection.get(
                where={"file_path": file_path},
                include=["documents"]
            )
            
            if not file_docs["documents"]:
                return []
            
            sample_content = file_docs["documents"][0][:500]
            
            similar_results = await self.search(
                sample_content,
                limit=limit + 5,
                filter_metadata={"file_path": {"$ne": file_path}}
            )
            
            return similar_results[:limit]
            
        except Exception as e:
            print(f"Error finding similar files: {str(e)}")
            return []

    def _chunk_content(self, content: str, file_path: str) -> List[Dict]:
        max_chunk_size = 1000
        overlap = 100
        
        if len(content) <= max_chunk_size:
            return [{
                "content": content,
                "start": 0,
                "end": len(content)
            }]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + max_chunk_size, len(content))
            
            if end < len(content):
                last_newline = content.rfind('\n', start, end)
                if last_newline > start:
                    end = last_newline
            
            chunk_content = content[start:end]
            
            if chunk_content.strip():
                chunks.append({
                    "content": chunk_content,
                    "start": start,
                    "end": end
                })
            
            start = max(start + 1, end - overlap)
        
        return chunks

    def _generate_doc_id(self, file_path: str, content: str) -> str:
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"{file_hash}_{content_hash}"

    def _generate_context(self, content: str, metadata: Dict) -> str:
        file_path = metadata.get("file_path", "")
        language = metadata.get("language", "")
        chunk_info = ""
        
        if metadata.get("total_chunks", 1) > 1:
            chunk_index = metadata.get("chunk_index", 0)
            total_chunks = metadata.get("total_chunks", 1)
            chunk_info = f" (part {chunk_index + 1} of {total_chunks})"
        
        return f"From {file_path} ({language}){chunk_info}"

    async def delete_repository_documents(self, repo_name: str):
        try:
            self.collection.delete(
                where={"repo": repo_name}
            )
        except Exception as e:
            print(f"Error deleting repository documents: {str(e)}")

    async def get_repository_stats(self, repo_name: str) -> Dict:
        try:
            repo_docs = self.collection.get(
                where={"repo": repo_name},
                include=["metadatas"]
            )
            
            if not repo_docs["metadatas"]:
                return {"total_documents": 0, "languages": [], "total_size": 0}
            
            languages = set()
            total_size = 0
            files = set()
            
            for metadata in repo_docs["metadatas"]:
                languages.add(metadata.get("language", "unknown"))
                total_size += metadata.get("content_length", 0)
                files.add(metadata.get("file_path", ""))
            
            return {
                "total_documents": len(repo_docs["metadatas"]),
                "unique_files": len(files),
                "languages": list(languages),
                "total_size": total_size
            }
            
        except Exception as e:
            print(f"Error getting repository stats: {str(e)}")
            return {"total_documents": 0, "languages": [], "total_size": 0}

    def health_check(self) -> Dict[str, Any]:
        try:
            collection_count = self.client.list_collections()
            document_count = self.collection.count()
            
            return {
                "status": "healthy",
                "collections": len(collection_count),
                "documents": document_count,
                "db_path": self.chroma_db_path
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "db_path": self.chroma_db_path
            }

    async def reset_database(self):
        try:
            self.client.reset()
            self.collection = self._get_or_create_collection()
        except Exception as e:
            print(f"Error resetting database: {str(e)}")