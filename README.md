## 🚀 Tech Stack

### **Frontend**
- **React.js** – Provides the foundation for building the interactive, component-based user interface of Lighthouse.
- **Tailwind CSS** – Utility-first CSS framework that ensures a clean, responsive, and modern UI design without writing custom CSS from scratch.
- **Recharts / Map Libraries (Leaflet, Mapbox, etc.)** – Power the visualization features such as interactive heatmaps, dashboards, and trend graphs.

### **Backend**
- **FastAPI (Python)** – High-performance framework for building the backend RESTful API. Handles data ingestion, preprocessing, and serves analysis results to the frontend.
- **Ollama (LLM Integration)** – Integrates an open-source LLM to analyze incoming posts:
  - Classify crisis type (e.g., natural disaster, public safety, infrastructure).
  - Perform sentiment analysis and detect misinformation.
  - Extract structured metadata like severity, urgency, and affected regions.

### **Database**
- **Vector Database (e.g., Pinecone, Weaviate, or Milvus)** – Stores embeddings of processed posts, enabling:
  - Semantic search for relevant crisis updates.
  - Clustering of posts to detect emerging trends.
  - Fast retrieval for real-time monitoring and dashboard updates.

### **Cloud & Infrastructure**
- **Git + GitHub** – Version control and collaboration for distributed team development.
- **Jira** – Agile task management and sprint planning.
- **Cloud Provider (TBD: AWS, GCP, or Azure)** – Will be used for deployment of backend services, frontend hosting, and database infrastructure.
