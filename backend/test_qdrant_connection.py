from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

def test_qdrant_connection():
    """Test local Qdrant connection"""
    try:
        # connect to Qdrant
        client = QdrantClient(host="localhost", port=6333)
        
        print("Successfully connected to Qdrant")
        
        # get collections
        collections = client.get_collections()
        print(f"Existing collections: {len(collections.collections)}")
        
        # create test collection
        test_collection = "connection_test"
        
        # clean up if exists
        try:
            client.delete_collection(test_collection)
        except:
            pass
        
        # create collection
        client.create_collection(
            collection_name=test_collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Created test collection: {test_collection}")
        
        # insert test vector
        client.upsert(
            collection_name=test_collection,
            points=[
                PointStruct(
                    id=1,
                    vector=np.random.rand(384).tolist(),
                    payload={"test": "data", "team": "lighthouse"}
                )
            ]
        )
        print("Inserted test vector")
        
        # search test
        results = client.search(
            collection_name=test_collection,
            query_vector=np.random.rand(384).tolist(),
            limit=1
        )
        print(f"Search successful! Found {len(results)} result(s)")
        
        # cleanup
        client.delete_collection(test_collection)
        print("Test complete and cleaned up")
        print("\nQdrant is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_qdrant_connection()
